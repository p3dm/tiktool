import uiautomator2 as u2
import sys
import json
import time
import uiautomator2 as u2
import subprocess
import time
import random
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from Tool import *

sheet_id = "14A4XmH66m5bckyGmudP8EJB_xKtsurA7BA4R54aTVz8"
sheet_name = "seeding"

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

creds = Credentials.from_service_account_file(
    'aber-129b1-d3ca26ba130a.json',
    scopes=SCOPES
)

service = build('sheets', 'v4', credentials=creds)


def get_bold_phone_rows(spreadsheet_id, sheet_name):
    res = service.spreadsheets().get(
        spreadsheetId=spreadsheet_id,
        ranges=[sheet_name],
        includeGridData=True
    ).execute()

    rows = res['sheets'][0]['data'][0]['rowData']
    print(rows)
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
            "Posting link (drive)": cell(1),
            "caption/hashtag": cell(2),
            "Tool session": cell(3),
            "Status": cell(4),
            "Music keyword": cell(5),
            "Running results": cell(6)
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
    comments = data["Tool session"]
    status = data["Status"]
    music = data["Music keyword"]
    results = data["Running results"]
    subprocess.run([
        "adb", "-s", device_id,
        "shell", "am", "start",
        "-a", "android.intent.action.VIEW",
        "-d", link+ " com.android.chrome"
    ])
    time.sleep(15)
    device = u2.connect(device_id)
    device.xpath("Tải xuống").click()
    time.sleep(60)
    update_running_result(
        sheet_id,
        sheet_name,
        device_id,
        "Đang Scam")

    try:
        upload_video(device,music,caption)
        update_running_result(
            sheet_id,
            sheet_name,
            device_id,
            "Đã xong"
        )
    except Exception as e:
        update_running_result(
            sheet_id,
            sheet_name,
            device_id,
            f"Lỗi: {e}"
        )
