# app.py
import os, sys, time, threading, atexit, webview, logging, traceback, socket, shutil, subprocess
from datetime import datetime
from multiprocessing import freeze_support

# ── PyInstaller helpers ──────────────────────────────────────────────────────
def resource_path(rel):
    """Resolve path đúng cả lúc dev lẫn sau khi đóng gói."""
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, rel)


def unblock_bundled_files():
    """Remove Zone.Identifier ADS on bundled files (common when extracted from Downloads)."""
    if os.name != "nt":
        return

    base = getattr(sys, "_MEIPASS", None)
    if not base:
        return

    exts = {".dll", ".exe", ".pyd"}
    for root, _, files in os.walk(base):
        for name in files:
            if os.path.splitext(name)[1].lower() not in exts:
                continue
            path = os.path.join(root, name)
            try:
                os.remove(path + ":Zone.Identifier")
            except OSError:
                pass

# ── Setup sys.path TRƯỚC KHI import blueprint ────────────────────────────────
# Phải làm ở đây vì blueprint import Boost/Trust ngay lúc module load
sys.path.insert(0, resource_path('Boost'))
sys.path.insert(0, resource_path('Trust'))

# ── Import sau khi path đã sẵn sàng ─────────────────────────────────────────
from flask import Flask
from scheduler_instance import scheduler
from blueprints.FE_routes   import fe_bp
from blueprints.Run_Main   import main_run_bp
from blueprints.Run_Schedule import cron_bp, date_bp

logging.basicConfig(
    filename="app-debug.log",
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s"
)

logging.info(
    "Scheduler timezone detected from this computer: %s (current time: %s)",
    scheduler.timezone,
    datetime.now(scheduler.timezone).isoformat(),
)


# ── uiautomator2 connection diagnostics ────────────────────────────────────
def _adb_connection_diagnostics(device_id):
    """Return ADB state to include in the log when uiautomator2 cannot connect."""
    bundled_adb = resource_path(os.path.join("adb", "windows", "adb.exe"))
    adb = bundled_adb if os.path.isfile(bundled_adb) else shutil.which("adb")
    if not adb:
        return "ADB was not found (expected bundled adb/windows/adb.exe or adb in PATH)."

    commands = [[adb, "devices", "-l"]]
    if device_id and device_id != "auto":
        commands.append([adb, "-s", str(device_id), "get-state"])

    result = []
    for command in commands:
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            output = (completed.stdout or completed.stderr or "(no output)").strip()
            result.append(f"{' '.join(command[1:])}: exit={completed.returncode}; {output}")
        except Exception as exc:
            result.append(f"{' '.join(command[1:])}: could not run ADB ({type(exc).__name__}: {exc})")
    return " | ".join(result)


def install_uiautomator2_connection_logging():
    """Log the serial, root exception and ADB status for every u2.connect call."""
    try:
        import uiautomator2 as u2
    except ImportError:
        logging.warning("uiautomator2 is unavailable; connection diagnostics were not installed.")
        return

    if getattr(u2, "_tiktool_connect_logging_installed", False):
        return

    original_connect = u2.connect
    logger = logging.getLogger("uiautomator2.connection")

    def connect_with_logging(*args, **kwargs):
        device_id = kwargs.get("serial") or kwargs.get("addr") or (args[0] if args else "auto")
        logger.info("uiautomator2: connecting to device=%r", device_id)
        started_at = time.monotonic()
        try:
            device = original_connect(*args, **kwargs)
            logger.info(
                "uiautomator2: connected to device=%r in %.2fs",
                device_id,
                time.monotonic() - started_at,
            )
            return device
        except Exception as exc:
            logger.exception(
                "uiautomator2: connection failed for device=%r after %.2fs; "
                "error=%s: %s; ADB diagnostics: %s",
                device_id,
                time.monotonic() - started_at,
                type(exc).__name__,
                exc,
                _adb_connection_diagnostics(device_id),
            )
            raise

    u2.connect = connect_with_logging
    u2._tiktool_connect_logging_installed = True


install_uiautomator2_connection_logging()

# ── Tạo Flask app ─────────────────────────────────────────────────────────────
app = Flask(
    __name__,
    template_folder=resource_path('templates'),
    static_folder=resource_path('static'),
)
app.secret_key = "tiktool-secret-change-me"

# ── Register blueprints ───────────────────────────────────────────────────────
#
#   fe_bp       → không có prefix → xử lý /  /save-config  /start  /stop  /status  /shutdown
#   main_run_bp → prefix /api     → /api/start-up-video  /api/update-avatar  ...
#   date_bp     → prefix /date → one-off jobs from the full schedule value
#   cron_bp     → prefix /cron → daily jobs from the schedule time
#
app.register_blueprint(fe_bp)
app.register_blueprint(main_run_bp, url_prefix='/api')
app.register_blueprint(date_bp, url_prefix='/date')
app.register_blueprint(cron_bp, url_prefix='/cron')

# ── Scheduler lifecycle ───────────────────────────────────────────────────────
# KHÔNG start scheduler ở đây — chỉ start khi user bấm /start
# Lý do: tránh spawn thread background khi multiprocessing fork child process
atexit.register(lambda: scheduler.shutdown(wait=False) if scheduler.running else None)

# ── Main ──────────────────────────────────────────────────────────────────────
def run_flask():
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,
        use_reloader=False,
    )


def wait_for_flask(host="127.0.0.1", port=5000, timeout=15):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.2)
    return False

if __name__ == "__main__":
    try:
        freeze_support()
        unblock_bundled_files()

        # Keep pythonnet on .NET Framework runtime for pywebview winforms backend.
        os.environ.setdefault("PYTHONNET_RUNTIME", "netfx")

        # Chạy Flask nền
        threading.Thread(target=run_flask, daemon=True).start()

        # Chờ Flask thật sự lắng nghe cổng trước khi mở WebView
        if not wait_for_flask():
            raise RuntimeError("Flask server did not start on 127.0.0.1:5000")

        # Chạy WebView trên main thread
        webview.create_window(
            "TikTool",
            "http://127.0.0.1:5000",
            width=1200,
            height=800,
        )

        webview.start(gui='edgechromium')
    except Exception :
        logging.exception("crashed")

        with open("fatal-error.txt", "w", encoding="utf-8") as f:
            f.write(traceback.format_exc())
  
