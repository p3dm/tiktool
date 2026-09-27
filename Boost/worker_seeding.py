from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import sys
import time
import uiautomator2 as u2
import subprocess
import time
import random
from Tool import getCommentByAI, buff_view
import os
import logging



from config import load_config

if getattr(sys, "frozen", False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ADB_PATH = os.path.join(BASE_DIR, "adb", "windows", "adb.exe")
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# ================== INIT SERVICE ==================
_service_cache = None
pkgs = ["com.ss.android.ugc.trill","com.zhiliaoapp.musically"]

def _get_service():
    global _service_cache
    if _service_cache is not None:
        return _service_cache

    cfg      = load_config()
    json_path = cfg.get("service_account_path", "")

    if not json_path or not os.path.exists(json_path):
        raise RuntimeError(
            f"Không tìm thấy file service account tại: '{json_path}'\n"
            "Vui lòng upload file JSON trong phần cấu hình."
        )

    creds          = Credentials.from_service_account_file(json_path, scopes=SCOPES)
    _service_cache = build('sheets', 'v4', credentials=creds)
    return _service_cache


def reset_service():
    global _service_cache
    _service_cache = None

# ================== READ BOLD PHONE ID ROWS ==================
def get_bold_phone_rows_2(spreadsheet_id, sheet_name):
    service = _get_service()
    res = service.spreadsheets().get(
        spreadsheetId=spreadsheet_id,
        ranges=[sheet_name],
        includeGridData=True
    ).execute()

    sheet = res["sheets"][0]
    rows = sheet["data"][0].get("rowData", [])

    result = []

    for row_index, row in enumerate(rows[1:], start=2):  # bỏ header
        cells = row.get("values", [])
        if not cells:
            continue

        phone_cell = cells[0]
        phone_id = phone_cell.get("formattedValue")

        text_format = (
            phone_cell  
            .get("userEnteredFormat", {})
            .get("textFormat", {})
        )

        # chỉ lấy Phone ID in đậm (Ctrl+B)
        if not text_format.get("bold"):
            continue

        def cell_value(i):
            if i < len(cells):
                return cells[i].get("formattedValue", "")
            return ""

        result.append({
            "Phone ID": phone_id,
            "view each phone": cell_value(1),
            "schedule": cell_value(3),
            "Comment/ @/ icon (enter)": cell_value(4),
            "seeding language": cell_value(5),
            "niche, topic": cell_value(6),
            "customer portrait": cell_value(7),
            "goalOfInteraction": cell_value(8),
            "interaction orientation": cell_value(9),
            "link": cell_value(10),
            "api_key": cell_value(2)
        })

    return result

# ================== RUN ==================

def running_buff_view(data):
    device_id = str(data["Phone ID"])
    device = u2.connect(device_id)
    device.press("home")
    device.app_clear("com.genfarmer.uiautomator")
    view_target = data["view each phone"]
    comments = data["Comment/ @/ icon (enter)"]
    link = data["link"]
    installed = set(device.app_list())  # all installed packages
    if pkgs[1] in installed:
        subprocess.run([
                ADB_PATH, "-s", device_id,
                "shell", "am", "start",
                "-a", "android.intent.action.VIEW",
                "-d", link,
                "-p", pkgs[1]
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NO_WINDOW
        )
    else:
        subprocess.run([
            ADB_PATH, "-s", device_id,
            "shell", "am", "start",
            "-a", "android.intent.action.VIEW",
            "-d", link,
            "-p", pkgs[0]
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NO_WINDOW,
        )
    time.sleep(10)
    if(comments!=""):
        commentInPost = comments
    else:
        try:
            language = data["seeding language"]
            topic = data["niche, topic"]
            customerPortrait = data["customer portrait"]
            goalOfInteractio = data["goalOfInteraction"]
            interactionOrientation = data["interaction orientation"]
            api_key = data["api_key"]
            post_data = device.xpath("//*[@resource-id='com.zhiliaoapp.musically:id/desc']|//*[@resource-id='com.ss.android.ugc.trill:id/desc']").get_text()
            if not api_key:
                commentInPost = None
            else:
                commentInPost = getCommentByAI(api_key, post_data, language, topic, customerPortrait, goalOfInteractio,
                                    interactionOrientation)
        except Exception as e:
            logging.exception("Worker crashed")
    time.sleep(10)
    buff_view(int(view_target.strip()), random.randint(25, 45), device, commentInPost)
    device.press("home")
# ================== RESULT ==================

def update_running_result(spreadsheet_id, sheet_name, phone_id, status):
    # Lấy toàn bộ cột A (Phone ID)
    service = _get_service()
    res = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=f"{sheet_name}!A:A"
    ).execute()

    rows = res.get("values", [])

    for idx, row in enumerate(rows, start=1):
        if row and row[0] == phone_id:
            service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=f"{sheet_name}!G{idx}",  # cột Running results
                valueInputOption="RAW",
                body={"values": [[status]]}
            ).execute()
            return True

    return False