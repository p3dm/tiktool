from flask import Flask, jsonify, request, redirect
from multiprocessing import Process
import threading
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Boost'))
from worker import *
from worker_seeding import *
from Tool import *
from worker import running_post_video
import webbrowser

# Add Trust folder to path to import Trust functions
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Trust'))
from Trust import update_avatar, update_bio, update_name, main_flow

app = Flask(__name__)

SPREADSHEET_ID = "14A4XmH66m5bckyGmudP8EJB_xKtsurA7BA4R54aTVz8"

# Global process registry
_process_lock = threading.Lock()
_active_processes: list = []  # list of multiprocessing.Process


def _register_and_run(processes: list):
    """Start processes, register them globally, wait for completion, then deregister."""

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

def run_worker_batch():
    """
    Hàm này sẽ chạy ngầm (background).
    Nó lấy dữ liệu mới nhất và khởi tạo các Process.
    """
    print("--- Bắt đầu lấy dữ liệu từ Sheet ---")
    # Lấy rows ở đây để đảm bảo mỗi lần gọi API đều lấy dữ liệu mới nhất
    rows = get_bold_phone_rows(
        spreadsheet_id=SPREADSHEET_ID,
        sheet_name="seeding"
    )

    if not rows:
        print("Không có dữ liệu để chạy.")
        return

    print(f"--- Tìm thấy {len(rows)} dòng dữ liệu. Bắt đầu chạy Multiprocessing ---")

    processes = [Process(target=running_post_video, args=(data,)) for data in rows]
    _register_and_run(processes)
    print("--- Hoàn tất tất cả các tiến trình ---")

def get_device_data(phone_id, sheet_name="seeding"):
    """
    Lấy dữ liệu của một thiết bị cụ thể từ Google Sheet dựa trên Phone ID
    """
    rows = get_bold_phone_rows(
        spreadsheet_id=SPREADSHEET_ID,
        sheet_name=sheet_name
    )
    
    for row in rows:
        if row.get("Phone ID") == phone_id:
            return row
    
    return None

# Batch processing functions with multiprocessing
def update_avatar_batch():
    """
    Hàm này sẽ chạy ngầm (background).
    Nó lấy dữ liệu mới nhất và khởi tạo các Process để cập nhật avatar.
    """
    print("--- Bắt đầu cập nhật Avatar cho tất cả thiết bị ---")
    rows = get_bold_phone_rows(
        spreadsheet_id=SPREADSHEET_ID,
        sheet_name="seeding"
    )

    if not rows:
        print("Không có dữ liệu để chạy.")
        return

    print(f"--- Tìm thấy {len(rows)} dòng dữ liệu. Bắt đầu chạy Multiprocessing ---")

    processes = [Process(target=update_avatar, args=(data,)) for data in rows]
    _register_and_run(processes)
    print("--- Hoàn tất cập nhật Avatar cho tất cả thiết bị ---")

def update_bio_batch():
    """
    Hàm này sẽ chạy ngầm (background).
    Nó lấy dữ liệu mới nhất và khởi tạo các Process để cập nhật bio.
    """
    print("--- Bắt đầu cập nhật Bio cho tất cả thiết bị ---")
    rows = get_bold_phone_rows(
        spreadsheet_id=SPREADSHEET_ID,
        sheet_name="seeding"
    )

    if not rows:
        print("Không có dữ liệu để chạy.")
        return

    print(f"--- Tìm thấy {len(rows)} dòng dữ liệu. Bắt đầu chạy Multiprocessing ---")

    processes = [Process(target=update_bio, args=(data,)) for data in rows]
    _register_and_run(processes)
    print("--- Hoàn tất cập nhật Bio cho tất cả thiết bị ---")

def update_name_batch():
    """
    Hàm này sẽ chạy ngầm (background).
    Nó lấy dữ liệu mới nhất và khởi tạo các Process để cập nhật tên.
    """
    print("--- Bắt đầu cập nhật Name cho tất cả thiết bị ---")
    rows = get_bold_phone_rows(
        spreadsheet_id=SPREADSHEET_ID,
        sheet_name="seeding"
    )

    if not rows:
        print("Không có dữ liệu để chạy.")
        return

    print(f"--- Tìm thấy {len(rows)} dòng dữ liệu. Bắt đầu chạy Multiprocessing ---")

    processes = [Process(target=update_name, args=(data,)) for data in rows]
    _register_and_run(processes)
    print("--- Hoàn tất cập nhật Name cho tất cả thiết bị ---")

def main_flow_batch():
    """
    Hàm này sẽ chạy ngầm (background).
    Nó lấy dữ liệu mới nhất và khởi tạo các Process để chạy main flow.
    """
    print("--- Bắt đầu Main Flow cho tất cả thiết bị ---")
    rows = get_bold_phone_rows(
        spreadsheet_id=SPREADSHEET_ID,
        sheet_name="seeding"
    )

    if not rows:
        print("Không có dữ liệu để chạy.")
        return

    print(f"--- Tìm thấy {len(rows)} dòng dữ liệu. Bắt đầu chạy Multiprocessing ---")

    processes = [Process(target=main_flow, args=(data,)) for data in rows]
    _register_and_run(processes)
    print("--- Hoàn tát Main Flow cho tất cả thiết bị ---")

# API Endpoints
@app.route('/update-avatar', methods=['GET', 'POST'])
def trigger_update_avatar():
    """
    API để cập nhật avatar trên TikTok cho tất cả thiết bị
    Usage GET: http://localhost:5000/update-avatar
    Usage POST: {}
    """
    task_thread = threading.Thread(target=update_avatar_batch)
    task_thread.start()
    
    return jsonify({
        "status": "success",
        "message": "Avatar update started for all devices"
    })

@app.route('/update-bio', methods=['GET', 'POST'])
def trigger_update_bio():
    """
    API để cập nhật bio trên TikTok cho tất cả thiết bị
    Usage GET: http://localhost:5000/update-bio
    Usage POST: {}
    """
    task_thread = threading.Thread(target=update_bio_batch)
    task_thread.start()
    
    return jsonify({
        "status": "success",
        "message": "Bio update started for all devices"
    })

@app.route('/update-name', methods=['GET', 'POST'])
def trigger_update_name():
    """
    API để cập nhật tên trên TikTok cho tất cả thiết bị
    Usage GET: http://localhost:5000/update-name
    Usage POST: {}
    """
    task_thread = threading.Thread(target=update_name_batch)
    task_thread.start()
    
    return jsonify({
        "status": "success",
        "message": "Name update started for all devices"
    })

@app.route('/start-main-flow', methods=['GET', 'POST'])
def trigger_main_flow():
    """
    API để bắt đầu main flow (search + comment + like + view) cho tất cả thiết bị
    Usage GET: http://localhost:5000/start-main-flow
    Usage POST: {}
    """
    task_thread = threading.Thread(target=main_flow_batch)
    task_thread.start()
    
    return jsonify({
        "status": "success",
        "message": "Main flow started for all devices"
    })
def run_worker_seeing_batch():
    """
    Hàm này sẽ chạy ngầm (background).
    Nó lấy dữ liệu mới nhất và khởi tạo các Process.
    """
    print("--- Bắt đầu lấy dữ liệu từ Sheet ---")
    # Lấy rows ở đây để đảm bảo mỗi lần gọi API đều lấy dữ liệu mới nhất
    rows = get_bold_phone_rows_2(
        spreadsheet_id=SPREADSHEET_ID,
        sheet_name="seeding_2"
    )

    if not rows:
        print("Không có dữ liệu để chạy.")
        return

    print(f"--- Tìm thấy {len(rows)} dòng dữ liệu. Bắt đầu chạy Multiprocessing ---")

    processes = [Process(target=running_buff_view, args=(data,)) for data in rows]
    _register_and_run(processes)
    print("--- Hoàn tất tất cả các tiến trình ---")

@app.route('/start-seeding', methods=['GET', 'POST'])
def trigger_seeding():
    """
    Endpoint để kích hoạt tool.
    Truy cập: http://localhost:5000/start-seeding
    """
    # Sử dụng Thread để chạy hàm run_worker_batch ở chế độ nền
    # Điều này giúp API trả về kết quả ngay lập tức mà không bị treo
    task_thread = threading.Thread(target=run_worker_seeing_batch)
    task_thread.start()

    return jsonify({
        "status": "success",
        "message": "Running"
    })
@app.route('/start-up-video', methods=['GET', 'POST'])
def trigger_seeding_up_video():
    """
    Endpoint để kích hoạt tool.
    Truy cập: http://localhost:5000/start-seeding
    """
    # Sử dụng Thread để chạy hàm run_worker_batch ở chế độ nền
    # Điều này giúp API trả về kết quả ngay lập tức mà không bị treo
    task_thread = threading.Thread(target=run_worker_batch)
    task_thread.start()

    return jsonify({
        "status": "success",
        "message": "Running"
    })

@app.route('/stop', methods=['GET', 'POST'])
def stop_all():
    """
    Dừng tất cả các tiến trình đang chạy mà không tắt Flask server.
    Usage: http://localhost:5000/stop
    """
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



@app.route('/', methods=['GET'])
def index():
    target_website = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit?gid=0#gid=0"
    return redirect(target_website)


if __name__ == "__main__":
    # debug=True có thể gây lỗi với multiprocessing, nên để False hoặc mặc định
    target_website = "http://127.0.0.1:5000"
    webbrowser.open(target_website)
    app.run(host="0.0.0.0", port=5000)