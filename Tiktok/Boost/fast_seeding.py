from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import sys
import json
import time
import uiautomator2 as u2
import subprocess
import time
import random
from Tool import *

# ================== CONFIG ==================
BATCH_SIZE = 50

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADB_PATH = os.path.join(BASE_DIR, "adb", "windows", "adb.exe")
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
pkgs = ["com.ss.android.ugc.trill", "com.zhiliaoapp.musically"]

# ================== RUN ==================
def fast_buff_view(data):
    device_id = str(data["Phone ID"])   
    device = u2.connect(device_id)
    device.press("home")
    link = data["link"]
    links = link.splitlines()
    view_buff = int(str(data["view each phone"]).strip())
    total_done = 0  # tổng số view đã thực hiện
    for l in links:
        while total_done < view_buff:
            # === Mở link TikTok ===
            subprocess.run(
                [
                    ADB_PATH,
                    "-s",
                    device_id,
                    "shell",
                    "am",
                    "start",
                    "-a",
                    "android.intent.action.VIEW",
                    "-c",
                    "android.intent.category.BROWSABLE",
                    "-d",
                    l,
                    "com.zhiliaoapp.musically",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            time.sleep(10)
            # === Swipe batch (tối đa BATCH_SIZE hoặc số còn lại) ===
            remaining = view_buff - total_done
            batch = min(BATCH_SIZE, remaining)

            for i in range(1, batch + 1):
                sleep_time = random.uniform(2, 4)
                try:

                    w, h = device.window_size()
                    time.sleep(sleep_time)
                    device.swipe(w * 0.5, h * 0.88, w * 0.5, h * 0.3, 0.25)
                    time.sleep(sleep_time)
                    device.swipe(w * 0.5, h * 0.3, w * 0.5, h * 0.88, 0.25)
                    total_done += 1

                except Exception as e:
                    continue

            # === Sau mỗi batch: về home, clear app, chuẩn bị batch mới ===
            if total_done < view_buff:
                device.press("home")
                time.sleep(2)
                device.app_stop("com.zhiliaoapp.musically")
                time.sleep(3)
        device.press("home")
        time.sleep(2)
        device.app_stop("com.zhiliaoapp.musically")
        time.sleep(3)

    device.press("home")
