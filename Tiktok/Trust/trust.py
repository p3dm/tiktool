import random
from adbutils import device
import uiautomator2 as u2
import time
import requests
from google.oauth2 import service_account
from googleapiclient.discovery import build
import subprocess
import json
import re
import logging

from Boost.worker_seeding import ADB_PATH, _get_service

#//*[@content-desc="Dismiss update dialog"]
Xpath = {
    
    "search": "//*[@text='Search']|//*[@text='Tìm kiếm']",
    "comment_button": '//*[contains(@content-desc, "Read or add comments")]',
    "like_button": '//*[@content-desc="Like"]',
    "send_comment": '//*[@content-desc="Post comment"]',
    "send_comment_1": '//*[@resource-id="com.zhiliaoapp.musically:id/cg8" or @content-desc="@2131888260"]',
    "search_button": "//*[@resource-id='com.zhiliaoapp.musically:id/j4d' and @content-desc='Search']|//*[@resource-id='com.zhiliaoapp.musically:id/j4d' and @content-desc='Tìm kiếm']",
    "search_button_2": "//*[@resource-id='com.ss.android.ugc.trill:id/g8v'][2]", 
    "search_button_3": '//*[@resource-id="com.zhiliaoapp.musically:id/j2p" and @content-desc="Search"]',
    "search_button_4": '//*[@resource-id="com.ss.android.ugc.trill:id/jb1" and @content-desc="Tìm kiếm"]|//*[@resource-id="com.ss.android.ugc.trill:id/jbh" and @content-desc="Tìm kiếm"]|//*[@resource-id="com.zhiliaoapp.musically:id/jhs"]',
    "post_1_3": "//*[@resource-id='com.ss.android.ugc.trill:id/s94']",
    "post_1_1":"//*[@resẽource-id='com.ss.android.ugc.trill:id/sj7']",
    "post_1_2":"//*[@resource-id='com.ss.android.ugc.trill:id/n22']",
    "post_1_4":'//*[@resource-id="com.zhiliaoapp.musically:id/soy"]|//*[@resource-id="com.zhiliaoapp.musically:id/ssj"]',
    "post_1_5":'//*[@resource-id="com.ss.android.ugc.trill:id/t4i"]|//*[@resource-id="com.ss.android.ugc.trill:id/t2v"]|//*[@resource-id="com.zhiliaoapp.musically:id/txw"]',
    "share_button": '//*[contains(@content-desc, "Share video")]',
    "reup_button": '//*[contains(@content-desc,"Add or remove this video from Favorites")]',
    "profile_button": '//*[@content-desc="Profile"]',
    "edit_button" : '//*[@text="Edit"]|//*[@resource-id="com.ss.android.ugc.trill:id/d76"]',
    "update_bio":'//*[@text="Bio"]|//*[@resource-id="com.ss.android.ugc.trill:id/b2b"]',
    "bio_field": "//*[@resource-id='com.ss.android.ugc.trill:id/ekb']|//*[@resource-id='com.zhiliaoapp.musically:id/grs']",
    "name_field": "//*[@resource-id='com.zhiliaoapp.musically:id/gt7']|//*[@resource-id='com.ss.android.ugc.trill:id/hdf']|//*[@resource-id='com.ss.android.ugc.trill:id/ekb']",
    "save_button": '//*[@text="Save"]|//*[@resource-id="com.ss.android.ugc.trill:id/jv8"]',
    "close_button": '//*[@content-desc="Close"]',
    "x_button": "//*[@resource-id='com.ss.android.ugc.trill:id/jvf']",
    "share_button": '//*[@resource-id="com.ss.android.ugc.trill:id/nwg"]',
    "share_button_1":'//*[@resource-id="com.zhiliaoapp.musically:id/u2_"]',
    "repost_button": '//*[@content-desc="Repost"]/android.widget.FrameLayout[1]',
    "save_video": '//*[contains(@content-desc,"Add or remove this video from Favorites") and @selected="false"]',
    "clear": '//*[@resource-id="com.zhiliaoapp.musically:id/kpe"]|//*[@resource-id="com.ss.android.ugc.trill:id/hdf"]|//*[@resource-id="com.zhiliaoapp.musically:id/lar"]',
}

pkgs = ["com.ss.android.ugc.trill", "com.zhiliaoapp.musically"]

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']


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

        if not text_fmt.get('bold') or not phone_id:
            continue


        def cell(i):
            return cells[i].get('formattedValue') if i < len(cells) else None

        result.append({
            "Phone_ID": phone_id,
            "Link_driver":cell(1),
        })
    return result

def dowload_img_by_link(drive_link):
    SERVICE_ACCOUNT_FILE = 'aber-129b1-d3ca26ba130a.json'
    SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly']
    prefix = "https://drive.google.com/file/d/"
    # Bỏ query string nếu có
    url = drive_link.split("?")[0]

    if "/drive/u/" in url and "/folders/" in url:
        # case: /drive/u/1/folders/ID
        drive_id = url.split("/folders/")[1].rstrip("/")

    elif "/drive/folders/" in url:
        # case: /drive/folders/ID
        drive_id = url.split("/drive/folders/")[1].rstrip("/")

    elif "/file/d/" in url:
        # case: /file/d/ID/view
        drive_id = url.split("/file/d/")[1].split("/")[0]

    else:
        raise ValueError("Link Google Drive không hỗ trợ")
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=SCOPES
    )
    service = build('drive', 'v3', credentials=creds)

    query = f"'{drive_id}' in parents and mimeType contains 'image/' and trashed = false"

    results = service.files().list(
        q=query,
        pageSize=1000,
        fields="files(id, name)"
    ).execute()

    items = results.get('files', [])

    if not items:
        return
    else:
        download_links = []
        for file in items:
            file_id = file['id']
            download_url = f"https://drive.google.com/file/d/{file_id}"
            download_links.append(download_url)
        return download_links

def get_phone_ids(spreadsheet_id, sheet_name):
    rows = get_bold_phone_rows(spreadsheet_id, sheet_name)
    return [row["Phone ID"] for row in rows if row.get("Phone ID")]


def distribute_links(phone_ids, download_links):
    result = []

    phone_count = len(phone_ids)
    link_count = len(download_links)

    for i in range(phone_count):
        link = download_links[i] if i < link_count else None

        result.append({
            "Phone ID": phone_ids[i],
            "Link": link
        })
    return result
def random_sleep(min_seconds, max_seconds):
    return time.sleep(random.uniform(min_seconds, max_seconds))

def generate_comment(comment_language, post_caption,api_key):

    prompt = (
        f"Tạo cho tôi bình luận \n"
        f"Lưu ý: comment bằng tiếng {comment_language} chỉ đưa ra kết quả duy nhất là 1 bình luận từ 5 đến 15 từ, Chỉ trả về kết quả, không giải thích. \n"
        f"không dùng icon\n"
        f"Dựa trên video ngắn trên Tiktok có caption: '{post_caption}',\n"
        f"hãy đưa ra một bình luận vui vẻ, tích cực, với góc nhìn khi tôi là người dùng tiktok lướt thấy video có captop này \n"
    )
    URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key={api_key}"

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}]
            }
        ]
    }

    headers = {
        "Content-Type": "application/json"
    }

    res = requests.post(URL, headers=headers, data=json.dumps(payload))

    if res.status_code == 200:
        data = res.json()
        try:
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return text
        except Exception as e:
            logging.exception(f"Error: {e}")
            return
    else:
        return
def generate_keyword(comment_language, keyWord, api_key):
    """Generate 5 related keywords and return as list"""
    prompt = (
        f"Tạo cho tôi 5 từ khóa tìm kiếm trên tiktok liên quan đến '{keyWord}' bằng tiếng {comment_language}.\n"
        f"Lưu ý: \n"
        f"- Trả về 5 từ khóa, mỗi từ khóa trên một dòng\n"
        f"- Mỗi từ khóa ngắn gọn từ 1 đến 3 từ khác biệt so với từ ban đầu (unique)\n"
        f"- Chỉ trả về danh sách từ khóa, không đánh số, không giải thích\n"
    )
    URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key={api_key}"

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}]
            }
        ]
    }

    headers = {
        "Content-Type": "application/json"
    }

    res = requests.post(URL, headers=headers, data=json.dumps(payload))

    if res.status_code == 200:
        data = res.json()
        try:
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            # Parse kết quả thành list, loại bỏ dòng rỗng và khoảng trắng thừa
            keywords = [line.strip() for line in text.strip().split('\n') if line.strip()]
            return keywords
        except Exception as e:
            return []
    else:
        return []

def searchByKeyWord(d, keyWord):
    try:
        d.xpath(Xpath["search_button"] + " | " + Xpath["search_button_2"] + " | " + Xpath["search_button_3"] + " | " + Xpath["search_button_4"]).click()
        random_sleep(6,15)
        d.send_keys(keyWord)
        random_sleep(6,15)
        d.xpath(Xpath["search"]).click()
        random_sleep(10,20)
        d.xpath(Xpath["post_1_2"] + " | " + Xpath["post_1_3"] + " | " + Xpath["post_1_1"] + " | " + Xpath["post_1_4"] + " | " + Xpath["post_1_5"]).click()
        random_sleep(6,15)
        if d.xpath(Xpath["close_button"]).exists:
            d.xpath(Xpath["close_button"]).click()
            random_sleep(2,3)
    except Exception as e:
        return
def like(d):
    try:
        d.xpath(Xpath["like_button"]).click()
        random_sleep(10, 12)
    except Exception as e:
        return
def comment(d, comment_language,api_key):

    try:
        post_caption = d.xpath("//*[@resource-id='com.zhiliaoapp.musically:id/desc']|//*[@resource-id='com.ss.android.ugc.trill:id/desc']").get_text()
        d.xpath(Xpath["comment_button"]).click()
        random_sleep(3,6)
        # Generate comment mới từ API (chỉ truyền 2 tham số)
        commentText = generate_comment(comment_language, post_caption,api_key)
        d.xpath('//*[@text="Add comment..."]|//*[@text="Thêm bình luận..."]').click()
        d.send_keys(commentText)
        random_sleep(3,6)
        d.xpath('//*[@content-desc="@2131953937"]|//*[@content-desc="@2131888501"]|//*[@content-desc="@2131888199"]|//*[@content-desc="@2131888218"]|//*[@content-desc="@2131888231"]|//*[@content-desc="Post comment"]|//*[@resource-id="com.zhiliaoapp.musically:id/cg8" or @content-desc="@2131888260"]|//*[@content-desc="@2131888282"]|//*[@content-desc="@2131888272"]|//*[@resource-id="com.zhiliaoapp.musically:id/cgt"]'+ " | " + Xpath["send_comment"] + "|" + Xpath["send_comment_1"]).click()
        random_sleep(5,8)
        w, h = d.window_size()
        x = int(w * 0.5)
        y = int(h * 0.2)
        d.click(x, y)
        
    except Exception as e:
        return
    
def save_video(d):
    try:
        d.xpath(Xpath["save_button"]).click()
    except Exception as e:
        return
def repost(d):
    try:
        d.xpath(Xpath["share_button_1"]).click()
        random_sleep(2, 4)
        if d.xpath('//*[@content-desc="Remove repost"]/android.widget.FrameLayout[1]').exists:
            d.press("back")
        else:
            d.xpath(Xpath["repost_button"]).click()
    except Exception as e:
        return
    
def scroll(d):
    try:
        d.swipe(500, 1500, 500, 500, duration=0.2)
    except Exception as e:
        return
def view(d):
    try:
        random_sleep(2, 4)
    except Exception as e:
        return
    
def update_avatar(data):
    link = str(data["Avatar"])
    device_id = str(data["Phone ID"])

    d = u2.connect(device_id)
    d.press("home")
    d.app_stop("com.zhiliaoapp.musically")
    d.app_clear("com.genfarmer.uiautomator")
    try:
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
        d.xpath('//*[@resource-id="com.android.chrome:id/negative_button"]').click_exists(timeout=7)
        random_sleep(3,6)
        if d.xpath('//*[@resource-id="com.android.chrome:id/message"]').exists:
            d.xpath('//*[@resource-id="com.android.chrome:id/message"]').click_exists(timeout=7)
        time.sleep(10)
        d.xpath('//*[@content-desc="Download"]|//*[@text="Tải xuống"]|//*[@scontent-desc="Tải xuống"]|//*[@text="Showing viewer."]/android.view.View[2]/android.view.View[1]/android.view.View[2]/android.view.View[1]/android.widget.Button[1]').click_exists(timeout=15)
        time.sleep(10)
        d.xpath('//*[@text="Download again"]|//*[@text="Tải xuống lần nữa"]|//*[@text="Download"]|//*[@text="Download anyway"]|//*[@text="Tải xuống"]').click_exists(timeout=7)
        d.xpath('//*[@resource-id="com.android.chrome:id/positive_button"]|//*[@text="Download"]').click_exists(timeout=7)
        random_sleep(3,6)
        if d.xpath('//*[@resource-id="com.android.chrome:id/positive_button"]').exists:
            d.xpath('//*[@resource-id="com.android.chrome:id/positive_button"]').click_exists(timeout=7)
        
        random_sleep(8, 12)
        d.press("home")
        installed = set(d.app_list())
        for pkg in pkgs:
            if pkg in installed:
                d.app_stop(pkg)
                d.app_start(pkg)
                break
        
        d.xpath(Xpath["profile_button"]).click()
        random_sleep(2, 4)
        d.xpath(Xpath["edit_button"]).click()
        time.sleep(2)
        d.xpath('//*[@text="Change photo"]|//*[@text="Edit photo or avatar"]|//*[@resource-id="com.ss.android.ugc.trill:id/pq1"]').click()
        time.sleep(3)
        d.xpath('//*[@text="Upload photo"]').click()
        random_sleep(3,5)
        d.xpath('//android.widget.GridView/android.widget.FrameLayout[1]/android.widget.FrameLayout[1]/android.widget.Button[1]').click()
        random_sleep(4,5)
        d.xpath('//*[@text="Next (1)"]').click_exists(timeout=7)
        random_sleep(3,5)
        d.xpath("//*[contains(@text, 'post')]|//*[@resource-id='com.ss.android.ugc.trill:id/qxb']").click()
        if d.xpath("//*[contains(@text, 'post')]|//*[@resource-id='com.ss.android.ugc.trill:id/qxb']").exists:
            d.xpath("//*[contains(@text, 'post')]|//*[@resource-id='com.ss.android.ugc.trill:id/qxb']").click()
        time.sleep(20)
        d.press('back')
        time.sleep(10)
        d.press('home')
        d.app_stop("com.ss.android.ugc.trill")
    except Exception as e:
        return
    
def update_bio(data):
    device_id = str(data["Phone ID"])
    bio = str(data["Bio"])
    d = u2.connect(device_id)
    d.press("home")
    installed = set(d.app_list())
    d.app_clear("com.genfarmer.uiautomator")
    for pkg in pkgs:
        if pkg in installed:
            d.app_stop(pkg)
            d.app_start(pkg)
            break
    try:
        random_sleep(3, 6)
        d.xpath(Xpath["profile_button"]).click()
        random_sleep(2, 4)
        d.xpath(Xpath["edit_button"]).click()
        random_sleep(2, 4)
        d.xpath(Xpath["update_bio"]).click()
        random_sleep(2, 4)
        if d.xpath('//*[@text="Add a bio"]').exists or d.xpath('//*[@text="Write a short description about who you are or what your account is about"]').exists:
            d.xpath('//*[@text="Add a bio"]|//*[@text="Write a short description about who you are or what your account is about"]|//*[@resource-id="com.zhiliaoapp.musically:id/g9_"]').click()
            d.send_keys(bio)
        else: 
            d.xpath(Xpath["bio_field"]).long_click()
            random_sleep(3, 6)
            if d.xpath('//*[@text="Select all"]').exists:
                d.xpath('//*[@text="Select all"]').click()
                random_sleep(3, 6)
                d.clear_text()
                random_sleep(3, 6)
                d.send_keys(bio)
            else:
                d.clear_text()
                random_sleep(3, 6)
                d.send_keys(bio)
        random_sleep(3, 6)
        d.xpath(Xpath["save_button"]).click()
        time.sleep(10)
        d.press('home')
    except Exception as e:
        return

def update_name(data):
    device_id = str(data["Phone ID"])
    name = str(data["Name"])
    d = u2.connect(device_id)
    d.press("home")
    installed = set(d.app_list())
    for pkg in pkgs:
        if pkg in installed:
            d.app_stop(pkg)
            d.app_start(pkg)
            break
    try:
        random_sleep(3, 6)
        d.xpath(Xpath["profile_button"]).click()
        random_sleep(2, 4)
        d.xpath(Xpath["edit_button"]).click()
        random_sleep(2, 4)
        d.xpath('//*[@text="Name"]|//*[@resource-id="com.ss.android.ugc.trill:id/k2_"]').click()
        random_sleep(2, 4)
        if d.xpath(Xpath["clear"]).exists :
            d.xpath(Xpath["clear"]).click()
            random_sleep(3, 6)
            d.xpath(Xpath["name_field"]).click()
            random_sleep(3, 6)
            d.send_keys(name)
            d.xpath(Xpath["save_button"]).click()
            random_sleep(3,6)
            d.xpath('//*[@text="Confirm"]').click()
        else: 
            d.xpath(Xpath["name_field"]).click()
            random_sleep(3, 6)
            d.send_keys(name)
            random_sleep(3, 6)
            d.xpath(Xpath["save_button"]).click()
        time.sleep(10)
        d.press('back')
        time.sleep(10)
        d.press('home')
    except Exception as e:
        return

def flow1(d, keyWord, comment_language, api_key):
    """Flow 1: Search by keyword and interact"""
    actions = ["comment", "like", "view", "view", "view", "like", "like", "like", "save", "save"]  # Tăng tỷ lệ view và like
    try:
        random_sleep(3, 6)
        
        # Generate danh sách từ khóa liên quan
        keyword_list = generate_keyword(comment_language, keyWord, api_key)
        
        if not keyword_list:
            keyword_list = [keyWord]
        
        # Search với từng từ khóa trong list
        for current_keyword in keyword_list:
            d.press("home")
            installed = set(d.app_list())  # all installed packages
            
            for pkg in pkgs:
                if pkg in installed:
                    d.app_stop(pkg)
                    d.app_start(pkg)
                    break
            random_sleep(10, 12)
            searchByKeyWord(d, current_keyword)
            random_sleep(10, 12)
            
            # Tương tác với 6-10 video
            for i in range(random.randint(6, 10)):
                random_sleep(10, 20)
                
                if i > 3:
                    chosen_action = random.choice(actions)
                else: 
                    action = ["view", "like", "repost"]
                    chosen_action = random.choice(action)
                    action.remove(chosen_action)
                try:
                    if d.xpath(Xpath["x_button"]).exists or d.xpath(Xpath["close_button"]).exists:
                        d.xpath(Xpath["x_button"] + " | " + Xpath["close_button"]).click_exists()
                        scroll(d)
                    else:
                        scroll(d)
                    if chosen_action == "like":
                        like(d)
                    if chosen_action == "view":
                        view(d)
                    if chosen_action == "comment":
                        comment(d, comment_language,api_key)
                        w, h = d.window_size()
                        x = int(w * 0.5)
                        y = int(h * 0.2)
                        d.click(x, y)
                    if chosen_action == "repost":
                        repost(d)
                    if chosen_action == "save":
                        save_video(d)
                    scroll(d)
                except Exception as e:    
                    return                
                random_sleep(10, 12)
                scroll(d)
            time.sleep(4)
        time.sleep(4)
        d.press('home')
        installed = set(d.app_list())  # all installed packages
        for pkg in pkgs:
            if pkg in installed:
                d.app_stop(pkg)
                break
    except Exception as e:
        return
def flow2(d, comment_language, api_key):
    """Flow 2: Browse For You feed and interact"""
    actions = ["comment", "like", "view", "view", "view", "view", "like", "like", "like"]  # Tăng tỷ lệ view và like
    
    try:
        d.press("home")
        installed = set(d.app_list())  # all installed packages
        for pkg in pkgs:
            if pkg in installed:
                d.app_stop(pkg)
                d.app_start(pkg)
                break
        random_sleep(3, 6)
        
        # Vòng lặp liên tục - không cần tìm kiếm
        for i in range(random.randint(6, 10)):
            random_sleep(10, 20)

            if i > 3:
                chosen_action = random.choice(actions)
            else: 
                action = ["view", "like", "repost"]
                chosen_action = random.choice(action)
                action.remove(chosen_action)

            if d.xpath(Xpath["x_button"]).exists or d.xpath(Xpath["close_button"]).exists or not d.xpath(Xpath["comment_button"]).exists or not d.xpath(Xpath["like_button"]).exists:
                d.xpath(Xpath["x_button"] + " | " + Xpath["close_button"]).click_exists()
                scroll(d)
            if chosen_action == "like":
                like(d)
            if chosen_action == "view":
                view(d)
            if chosen_action == "comment":
                comment(d, comment_language,api_key)
                w, h = d.window_size()
                x = int(w * 0.5)
                y = int(h * 0.2)
                d.click(x, y)
            if chosen_action == "repost":
                repost(d)
            if chosen_action == "save":
                save_video(d)
            scroll(d)
        d.press('home')
        installed = set(d.app_list())  # all installed packages
        for pkg in pkgs:
            if pkg in installed:
                d.app_stop(pkg)
                break

    except Exception as e:
        return

def normalize_int(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return int(value)

    text = str(value).strip()
    if not text:
        return None

    digits = re.sub(r"\D", "", text)
    if not digits:
        return None
    return int(digits)
       
    
def main_flow(data):
    device_id = str(data["Phone ID"])
    keyWord = str(data["Key Word"])
    comment_language = str(data["comment_language"])
    api_key = str(data["API_KEY"])
    total_time = normalize_int(data["Total Time"])
    time.sleep(10)

    device = u2.connect(device_id)

    try:
        if not total_time:
            while True:
                # Chạy flow1
                flow1(device, keyWord, comment_language, api_key)
                
                # Chạy flow2
                flow2(device, comment_language, api_key)
        else:
            end_time = time.time() + total_time * 60
            while time.time() < end_time:
                # Chạy flow1
                flow1(device, keyWord, comment_language, api_key)
                
                # Chạy flow2
                flow2(device, comment_language, api_key)
            
            device.press('home')
        
        # update_running_result(sheet_id, sheet_name, device_id, "✅ Hoàn thành")
        
    except Exception as e:
        return
        # update_running_result(sheet_id, sheet_name, device_id, error_msg)