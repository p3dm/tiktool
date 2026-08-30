"""Routes that create one-off (date) and daily recurring (cron) jobs.

The Google Sheet column named ``schedule`` must use ``dd/mm/yyyy HH:MM:SS``.
Date routes retain the complete value; cron routes use only its time portion.
"""

import logging
import threading
from datetime import datetime
from multiprocessing import Process

from apscheduler.triggers.cron import CronTrigger
from flask import Blueprint, jsonify

from blueprints.Run_Main import _run_process_later
from Boost.worker import get_bold_phone_rows, running_post_video
from Boost.worker_seeding import get_bold_phone_rows_2, running_buff_view
from config import get_spreadsheet_id
from scheduler_instance import scheduler
from Trust.trust import main_flow, update_avatar, update_bio, update_name

SCHEDULE_COLUMN = "schedule"
DATETIME_FORMAT = "%d/%m/%Y %H:%M:%S"

cron_bp = Blueprint("cron_bp", __name__)
date_bp = Blueprint("date_bp", __name__)


def _parse_schedule_cell(data: dict) -> datetime | None:
    """Read a schedule cell, returning ``None`` for an empty cell."""
    raw = data.get(SCHEDULE_COLUMN)
    if raw in (None, "", 0):
        return None
    try:
        return datetime.strptime(str(raw).strip(), DATETIME_FORMAT)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"[FORMAT] Phone ID='{data.get('Phone ID', '?')}': "
            f"giá trị '{raw}' không đúng format '{DATETIME_FORMAT}'"
        ) from exc


def _resolve_date_trigger(data: dict) -> datetime | None:
    return _parse_schedule_cell(data)


def _resolve_cron_trigger(data: dict) -> tuple[int, int, int] | None:
    value = _parse_schedule_cell(data)
    if value is None:
        return None
    return value.hour, value.minute, value.second


def _schedule_date_job(target_func, data: dict):
    try:
        value = _resolve_date_trigger(data)
    except ValueError as exc:
        logging.error("Unable to schedule date job: %s", exc)
        return False

    if value is None:
        return Process(target=target_func, args=(data,))

    phone_id = data.get("Phone ID", "?")
    scheduler.add_job(
        _run_process_later,
        trigger="date",
        run_date=value.replace(tzinfo=scheduler.timezone),
        args=[target_func, (data,)],
        id=f"date_{target_func.__name__}_{phone_id}_{value:%Y%m%d%H%M%S}",
        replace_existing=True,
    )
    return None


def _schedule_cron_job(target_func, data: dict):
    try:
        value = _resolve_cron_trigger(data)
    except ValueError as exc:
        logging.error("Unable to schedule cron job: %s", exc)
        return False

    if value is None:
        return Process(target=target_func, args=(data,))

    hour, minute, second = value
    phone_id = data.get("Phone ID", "?")
    scheduler.add_job(
        _run_process_later,
        trigger=CronTrigger(hour=hour, minute=minute, second=second, timezone=scheduler.timezone),
        args=[target_func, (data,)],
        id=f"cron_{target_func.__name__}_{phone_id}_{hour:02d}{minute:02d}{second:02d}",
        replace_existing=True,
    )
    return None


def _run_scheduled_batch(schedule_fn, target_func, getter_func, sheet_name: str, label: str):
    spreadsheet_id = get_spreadsheet_id()
    if not spreadsheet_id:
        logging.warning("[%s] Spreadsheet ID is not configured.", label)
        return

    rows = getter_func(spreadsheet_id=spreadsheet_id, sheet_name=sheet_name)
    if not rows:
        logging.info("[%s] No rows to schedule.", label)
        return

    scheduled = skipped = errors = 0
    for data in rows:
        result = schedule_fn(target_func, data)
        if result is False:
            errors += 1
        elif result is None:
            scheduled += 1
        elif isinstance(result, Process):
            # Empty schedules are handled by the immediate /api routes.
            skipped += 1

    logging.info("[%s] scheduled=%d skipped=%d errors=%d", label, scheduled, skipped, errors)


_JOBS = [
    ("up-video", "Up Video", running_post_video, get_bold_phone_rows, "seeding"),
    ("seeding", "Seeding View", running_buff_view, get_bold_phone_rows_2, "seeding_2"),
    ("update-avatar", "Update Avatar", update_avatar, get_bold_phone_rows, "seeding"),
    ("update-bio", "Update Bio", update_bio, get_bold_phone_rows, "seeding"),
    ("update-name", "Update Name", update_name, get_bold_phone_rows, "seeding"),
    ("main-flow", "Main Flow", main_flow, get_bold_phone_rows, "seeding"),
]


def _make_route(blueprint, schedule_fn, route_suffix, label, target_func, getter_func, sheet_name):
    def view():
        threading.Thread(
            target=_run_scheduled_batch,
            args=(schedule_fn, target_func, getter_func, sheet_name, label),
            daemon=True,
        ).start()
        return jsonify({"status": "success", "message": f"Scheduled {label} started"})

    view.__name__ = f"{blueprint.name}_{route_suffix.replace('-', '_')}"
    blueprint.add_url_rule(f"/{route_suffix}", view_func=view, methods=["GET", "POST"])


for suffix, label, func, getter, sheet in _JOBS:
    _make_route(cron_bp, _schedule_cron_job, suffix, label, func, getter, sheet)
    _make_route(date_bp, _schedule_date_job, suffix, label, func, getter, sheet)


def _register_job_management(blueprint):
    @blueprint.route("/clear-jobs", methods=["GET", "POST"])
    def clear_jobs():
        scheduler.remove_all_jobs()
        return jsonify({"status": "success", "message": "All scheduled jobs cleared"})

    @blueprint.route("/jobs/<job_id>", methods=["DELETE"])
    def remove_job(job_id):
        if scheduler.get_job(job_id) is None:
            return jsonify({"status": "error", "message": "Job not found"}), 404
        scheduler.remove_job(job_id)
        return jsonify({"status": "success", "message": "Job removed", "id": job_id})

    @blueprint.route("/list-jobs", methods=["GET"])
    def list_jobs():
        jobs = []
        for job in scheduler.get_jobs():
            next_run = getattr(job, "next_run_time", None)
            jobs.append({
                "id": job.id,
                "func": str(job.func_ref),
                "next_run": next_run.isoformat() if next_run else None,
                "pending": next_run is None,
                "trigger": str(job.trigger),
            })
        return jsonify({
            "status": "success",
            "jobs": jobs,
            "count": len(jobs),
            "timezone": str(scheduler.timezone),
            "current_time": datetime.now(scheduler.timezone).isoformat(),
        })


_register_job_management(cron_bp)
_register_job_management(date_bp)
