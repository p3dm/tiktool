from flask import Flask, jsonify, request, redirect
from multiprocessing import Process
import threading
from worker import *
from worker_seeding import *
from Tool import *
from worker import running_post_video
import webbrowser
app = Flask(__name__)

SPREADSHEET_ID = "14A4XmH66m5bckyGmudP8EJB_xKtsurA7BA4R54aTVz8"



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

    processes = []
    for data in rows:
        # Giữ nguyên logic Process như code cũ của bạn
        p = Process(target=running_post_video, args=(data,))
        processes.append(p)
        p.start()

    # Chờ các process con chạy xong (block thread này, nhưng không block Flask main thread)
    for p in processes:
        p.join()

    print("--- Hoàn tất tất cả các tiến trình ---")
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

    processes = []
    for data in rows:
        # Giữ nguyên logic Process như code cũ của bạn
        p = Process(target=running_buff_view, args=(data,))
        processes.append(p)
        p.start()
    # Chờ các process con chạy xong (block thread này, nhưng không block Flask main thread)
    for p in processes:
        p.join()

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

@app.route('/', methods=['GET'])
def index():
    target_website = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit?gid=0#gid=0"
    return redirect(target_website)


if __name__ == "__main__":
    # debug=True có thể gây lỗi với multiprocessing, nên để False hoặc mặc định
    target_website = "http://127.0.0.1:5000"
    webbrowser.open(target_website)
    app.run(host="0.0.0.0", port=5000)