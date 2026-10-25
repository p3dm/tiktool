# Task: Fix process overload / resource leak in p3dm/tiktool

## Context

`tiktool` is a Windows desktop app (Flask + pywebview, packaged with PyInstaller) that automates
multiple Android devices over ADB/uiautomator2. Each automation run spawns a
`multiprocessing.Process` (Windows => **spawn** start method).

**Symptom:** after the packaged app runs for a while, new device connections die _before_ a worker
process is even created. Root cause: child processes that hang (uiautomator2/ADB not responding)
are never reaped — they accumulate in `_active_processes`, hold OS handles and ADB sockets, and
eventually exhaust resources.

Relevant files:

- `blueprints/Run_Main.py` — `_register_and_run` (lines ~18-30), `_run_process_later` (~32-37),
  `_run_immediate_batch` (~41-62), `/stop` route with existing terminate/kill logic (~143-164)
- `blueprints/Run_Schedule.py` — `_schedule_job` (~94-111), cron/date job registration
- `blueprints/FE_routes.py` — `/stop` handling (~93-112)
- `Boost/worker.py`, `Boost/worker_seeding.py`, `Boost/Run.py` — process targets, call `u2.connect`
- `Trust/trust.py` — device automation logic
- `app.py` — entry point, logging setup, scheduler lifecycle

## Hard requirements

### R1 — Process registry with metadata (new module `process_registry.py`)

Replace the bare `_active_processes` list with a registry keyed by a unique `run_id`:

```python
@dataclass
class ProcessRecord:
    run_id: str
    proc: multiprocessing.Process
    started_at: float        # time.monotonic()
    max_duration: float      # seconds; per-task wall-clock budget
    label: str               # human-readable, e.g. "seeding:DEVICE_SERIAL"
    device_id: str | None
    cleaned: bool = False
```

All access goes through `threading.Lock()`. Keep a thin compatibility shim so existing code that
iterates `_active_processes` keeps working, or refactor all call sites — either is fine, but be
consistent.

### R2 — Single idempotent cleanup function

```python
def cleanup_run(run_id: str, reason: str) -> None
```

Behavior, in order:

1. If `record.cleaned` is already True: return immediately (idempotent — watchdog, `/stop` and
   join-path may all call it).
2. Set `cleaned = True`.
3. If `proc.is_alive()`: `terminate()` -> `join(timeout=5)` -> if still alive: `kill()` ->
   `join(timeout=5)`.
4. If not alive: `join(timeout=0)` to reap.
5. Call `proc.close()` inside `try/except ValueError` (close() raises ValueError if the process is
   somehow still running — it MUST only be called after the process is dead and joined).
6. Release the concurrency semaphore slot (see R3) and remove the per-device lock (see R4).
7. Remove the record from the registry.
8. Log: `run_id`, `label`, `device_id`, `reason` ("finished" | "timeout" | "stopped" | "error"),
   lifetime in seconds.

Refactor the existing terminate/kill block in the `/stop` route (`Run_Main.py` ~143-164) to call
`cleanup_run` instead of duplicating logic. `/stop` simply calls `cleanup_run(run_id, "stopped")`
for every record.

### R3 — Admission control (semaphore + skip-on-full)

- Module-level `threading.BoundedSemaphore(MAX_CONCURRENT_RUNS)` where
  `MAX_CONCURRENT_RUNS` is configurable in `config.py` (default: number of expected devices, e.g. 5).
- Before spawning a process (in `_register_and_run`, `_run_process_later`, `_run_immediate_batch`):
  `acquire(blocking=False)`. If it fails, **skip the run** and log a warning
  ("system busy, skipping run for device X") — do NOT queue or block the scheduler thread.
- The semaphore is released ONLY in `cleanup_run` (parent side). Never release it inside the
  worker: a hard-killed worker would leak the slot forever.
- Do NOT use `multiprocessing.Pool` — pooled workers retain stale uiautomator2 state between runs
  and are costly under spawn on Windows.

### R4 — Per-device dedup lock

- Registry keeps a set of `device_id`s that currently have a running process.
- Before spawning: if `device_id` is already present, skip the run and log a warning
  ("device X already has a running task, skipping"). Two processes automating the same phone
  simultaneously corrupts the atx-agent/uiautomator2 session.
- The device lock is released ONLY in `cleanup_run`.

### R5 — Watchdog thread

- One `threading.Thread(daemon=True)` started once (guard against double-start) when the app
  starts, using a `threading.Event` as stop signal; loop via `stop_event.wait(WATCHDOG_INTERVAL)`
  (default 20-30s) instead of `time.sleep` so shutdown is prompt.
- Each tick: snapshot the registry under the lock, then evaluate OUTSIDE the lock:
  - `not proc.is_alive()` -> `cleanup_run(run_id, "finished")`
  - `time.monotonic() - started_at > max_duration` -> `cleanup_run(run_id, "timeout")`
- Log a one-line heartbeat at DEBUG each tick: active count, slots free.
- Register an `atexit` hook that sets the stop event.

### R6 — Timeouts inside the worker (uiautomator2 layer)

IMPORTANT: `u2.connect()` does NOT accept a `timeout` keyword. Use the supported APIs:

- At the top of each worker target (in `Boost/worker.py`, `Boost/worker_seeding.py`,
  `Trust/trust.py` entry points), set the global HTTP timeout BEFORE any `u2.connect` call:
  `u2.settings['HTTP_TIMEOUT'] = 45` (default is 60s).
- Wrap `u2.connect` in a small retry helper (2 attempts, short backoff) that logs failures.
- Worker self-termination: compute `deadline = started_at + max_duration - SAFETY_MARGIN`
  (e.g. 30s) and check it at each loop iteration; on expiry, clean up device state best-effort
  and `sys.exit(0)`. The watchdog (R5) is the last resort, not the primary mechanism.
- `max_duration` should be passed per task type (seeding vs trust jobs have different expected
  durations) — add sensible defaults in `config.py`.

### R7 — Scheduler hardening (`Run_Schedule.py` / `scheduler_instance.py`)

- Configure job defaults: `coalesce=True`, `max_instances=1`, `misfire_grace_time=300` so missed
  executions collapse into one run instead of a burst of catch-up runs spawning many processes.
- Ensure the scheduler's thread pool executor is small (e.g. 4 workers) — job functions only
  spawn processes and return; they must never block on `join()`.
- `_run_process_later` must NOT `join()`; it registers the process and returns. The watchdog owns
  the lifecycle.

### R8 — Logging inside child processes (fixes missing logs in packaged app)

- Windows spawn: child processes do NOT inherit the parent's `logging.basicConfig`.
- Add a `setup_child_logging()` helper (in `process_registry.py` or a `logutil.py`) that configures
  a `FileHandler` in append mode pointing at the SAME absolute log path as the parent
  (`app-debug.log` next to the executable when `sys.frozen`), and call it as the FIRST statement of
  every process target function.
- This also makes the existing `uiautomator2.connection` diagnostics wrapper useful in packaged
  builds.

## Constraints

- Windows + PyInstaller one-folder build; multiprocessing spawn; `freeze_support()` already in
  `app.py` — keep it first in `__main__`.
- All new tunables (`MAX_CONCURRENT_RUNS`, `WATCHDOG_INTERVAL`, per-task `max_duration`,
  `HTTP_TIMEOUT`) go in `config.py` with comments.
- Do not change the Flask route surface (paths, methods, response shapes) — the webview UI depends
  on it.
- Every cleanup/kill/skip action must be logged at INFO with run_id + device_id; keep logs
  parseable (one event per line, key=value pairs).

## Acceptance criteria

1. Soak test: packaged app runs 2-3 hours with scheduler active; number of child `python.exe`
   processes stays bounded around the device count (no linear growth).
2. Kill test: unplug one phone mid-run; within `max_duration + WATCHDOG_INTERVAL` seconds the
   watchdog kills that worker and logs `reason=timeout` with its device_id; other devices keep
   working.
3. Busy test: schedule more simultaneous runs than `MAX_CONCURRENT_RUNS`; excess runs are skipped
   with a warning log, scheduler thread never blocks.
4. `/stop` still terminates everything promptly and the app exits cleanly (no zombie processes in
   Task Manager).
5. `app-debug.log` of the packaged build contains connect/success/failure lines from child
   processes (proves R8).

## Deliverables

- The code changes above, committed on a new branch `fix/process-overload`.
- A short `CHANGELOG`-style note in the PR description describing each R-item and how it was
  verified.
