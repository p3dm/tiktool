import threading, logging
from multiprocessing import Process
from flask import Blueprint, jsonify
from scheduler_instance import scheduler
from config import load_config, get_spreadsheet_id, save_config
from Boost.worker import running_post_video
from Boost.worker_seeding import running_buff_view, get_bold_phone_rows_2
from Boost.worker import get_bold_phone_rows
from Trust.trust import update_avatar, update_bio, update_name, main_flow

main_run_bp = Blueprint('main_run_bp', __name__)

import threading as _threading
_process_lock    = _threading.Lock()
_active_processes: list = []

def _register_and_run(processes: list):
    with _process_lock:
        _active_processes.extend(processes)
    for p in processes:
        p.start()
    for p in processes:
        p.join()
    with _process_lock:
        for p in processes:
            try:
                _active_processes.remove(p)
            except ValueError:
                pass

# ── Batch functions ───────────────────────────────────────────────────────────

def _run_immediate_batch(target_func, getter_func, sheet_name: str):
    """
    Chạy ngay tất cả rows không có trigger.
    Phần có lịch sẽ được xử lý bởi date/cron blueprints.
    Hàm này chỉ xử lý rows không có giá trị ở cột ``schedule``.
    """
    sid = get_spreadsheet_id()
    if not sid:
        logging.exception("Worker crashed")
        return

    rows = getter_func(spreadsheet_id=sid, sheet_name=sheet_name)
    if not rows:
        logging.exception("No rows's choosed")
        return 

    processes = [
        Process(target=target_func, args=(row,))
        for row in rows
    ]
    if processes:
        _register_and_run(processes)

# ── API Routes ────────────────────────────────────────────────────────────────
# Tất cả route dưới /api/ prefix (được set khi register_blueprint)

@main_run_bp.route('/start-up-video', methods=['GET', 'POST'])
def trigger_up_video():
    """POST /api/start-up-video — chạy ngay các row không có schedule"""
    threading.Thread(
        target=_run_immediate_batch,
        args=(running_post_video, get_bold_phone_rows, "seeding"),
        daemon=True
    ).start()
    return jsonify({"status": "success", "message": "Up video started"})


@main_run_bp.route('/start-seeding', methods=['GET', 'POST'])
def trigger_seeding():
    """POST /api/start-seeding"""
    threading.Thread(
        target=_run_immediate_batch,
        args=(running_buff_view, get_bold_phone_rows_2, "seeding_2"),
        daemon=True
    ).start()
    return jsonify({"status": "success", "message": "Seeding started"})


@main_run_bp.route('/update-avatar', methods=['GET', 'POST'])
def trigger_update_avatar():
    """POST /api/update-avatar"""
    threading.Thread(
        target=_run_immediate_batch,
        args=(update_avatar, get_bold_phone_rows, "seeding"),
        daemon=True
    ).start()
    return jsonify({"status": "success", "message": "Update avatar started"})


@main_run_bp.route('/update-bio', methods=['GET', 'POST'])
def trigger_update_bio():
    """POST /api/update-bio"""
    threading.Thread(
        target=_run_immediate_batch,
        args=(update_bio, get_bold_phone_rows, "seeding"),
        daemon=True
    ).start()
    return jsonify({"status": "success", "message": "Update bio started"})


@main_run_bp.route('/update-name', methods=['GET', 'POST'])
def trigger_update_name():
    """POST /api/update-name"""
    threading.Thread(
        target=_run_immediate_batch,
        args=(update_name, get_bold_phone_rows, "seeding"),
        daemon=True
    ).start()
    return jsonify({"status": "success", "message": "Update name started"})


@main_run_bp.route('/start-main-flow', methods=['GET', 'POST'])
def trigger_main_flow():
    """POST /api/start-main-flow"""
    threading.Thread(
        target=_run_immediate_batch,
        args=(main_flow, get_bold_phone_rows, "seeding"),
        daemon=True
    ).start()
    return jsonify({"status": "success", "message": "Main flow started"})

@main_run_bp.route('/stop', methods=['GET','POST'])
def stop_tool():
    """Dừng tất cả process đang chạy + xóa scheduled jobs."""
    with _process_lock:
        targets = list(_active_processes)

    if not targets:
        return jsonify({"status": "success", "message": "No active processes to stop.", "stopped": 0})

    for p in targets:
        if p.is_alive():
            p.terminate()
            p.join(timeout=5)
            if p.is_alive():
                p.kill()  # force-kill if still alive after 5 s

    with _process_lock:
        for p in targets:
            try:
                _active_processes.remove(p)
            except ValueError:
                pass

    return jsonify({"status": "success", "message": f"Stopped {len(targets)} process(es).", "stopped": len(targets)})
