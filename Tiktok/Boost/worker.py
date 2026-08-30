import os
import sys
import json
import time
import uiautomator2 as u2
import subprocess
import random
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from Tool import *
from config import load_config


if getattr(sys, "frozen", False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ADB_PATH = os.path.join(BASE_DIR, "adb", "windows", "adb.exe")
SCOPES=["https://www.googleapis.com/auth/spreadsheets"]
_service_cache = None


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



def get_bold_phone_rows(spreadsheet_id, sheet_name):
    service = _get_service()
    res = service.spreadsheets().get(
        spreadsheetId=spreadsheet_id,
        ranges=[sheet_name],
        includeGridData=True
    ).execute()

    rows = res['sheets'][0]['data'][0]['rowData']
    result = []

    for row_index, row in enumerate(rows[1:], start=2):  # bỏ header
        cells = row.get('values', [])
        if len(cells) < 1:
            continue

        phone_cell = cells[0]
        phone_id = phone_cell.get('formattedValue')

        text_fmt = phone_cell.get('userEnteredFormat', {}) \
                              .get('textFormat', {})

        # ❗ chỉ lấy Phone ID được Ctrl+B
        if not text_fmt.get('bold'):
            continue

        def cell(i):
            return cells[i].get('formattedValue') if i < len(cells) else None

        result.append({
            "Phone ID": phone_id,
            "Posting link (drive)": cell(2),
            "caption/hashtag": cell(3),
            "posting time": cell(7),
            "Status": cell(4),
            "Music keyword": cell(5),
            "Running results": cell(6),
            "Avatar": cell(8),
            "Bio": cell(9),
            "Name": cell(10),
            "comment_language": cell(11),
            "Key Word": cell(12),
            "Total Time": cell(13),
            "API_KEY" : cell(1),
            "schedule": cell(14)
        })

    return result

# def running_buff_view(data):
#
#     device_id = str(data["DEVICE ID"])
#     link = data["Link"]
#     view_target = data["View"]
#     comments = data["Comment"]
#     device = u2.connect(device_id)
#     print(f"[DEVICE {device_id}] START")
#     open_link(link,device_id)
#     buff_view(view_target,3,device,comments)
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

def running_post_video(data):
    device_id = str(data["Phone ID"])
    link = data["Posting link (drive)"]
    caption = data["caption/hashtag"]
    status = data["Status"]
    music = data["Music keyword"]
    results = data["Running results"]
    device = u2.connect(device_id)
    device.press("home")
    device.app_stop("com.zhiliaoapp.musically|com.ss.android.ugc.trill")
    device.app_clear("com.genfarmer.uiautomator")
    time.sleep(2)
    subprocess.run([
        ADB_PATH, "-s", device_id,
        "shell", "am", "start",
        "-a", "android.intent.action.VIEW",
        "-d", link + "com.android.chrome"
    ],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    creationflags=subprocess.CREATE_NO_WINDOW
    )
    device.xpath('//*[@resource-id="com.android.chrome:id/negative_button"]').click_exists(timeout=7)
    time.sleep(10)
    if device.xpath('//*[@resource-id="com.android.chrome:id/message"]').exists:
        device.xpath('//*[@resource-id="com.android.chrome:id/message"]').click_exists(timeout=7)
    time.sleep(10)
    device.xpath('//*[@content-desc="Download"]|//*[@text="Tải xuống"]|//*[@scontent-desc="Tải xuống"]|//*[@text="Showing viewer."]/android.view.View[2]/android.view.View[1]/android.view.View[2]/android.view.View[1]/android.widget.Button[1]').click_exists(timeout=15)
    time.sleep(10)
    device.xpath('//*[@text="Download again"]|//*[@text="Tải xuống lần nữa"]|//*[@text="Download"]|//*[@text="Download anyway"]|//*[@text="Tải xuống"]').click_exists(timeout=7)
    device.xpath('//*[@resource-id="com.android.chrome:id/positive_button"]|//*[@text="Download"]').click_exists(timeout=7)
    time.sleep(10)
    if device.xpath('//*[@resource-id="com.android.chrome:id/positive_button"]').exists:
        device.xpath('//*[@resource-id="com.android.chrome:id/positive_button"]').click_exists(timeout=7)

    time.sleep(60)
    service = _get_service()
    # update_running_result(
    #     sheet_id,
    #     sheet_name,
    #     device_id,
    #     "Tải xuống thành công")

    try:
        upload_video(device,music,caption)
        # update_running_result(
        #     sheet_id,
        #     sheet_name,
        #     device_id,
        #     "Đã xong"
        # )
    except Exception as e:
        return
