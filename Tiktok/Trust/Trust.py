import random
from adbutils import device
from adbutils import device
import uiautomator2 as u2
import time
import requests
from google.oauth2 import service_account
from googleapiclient.discovery import build
import subprocess
import json

#//*[@content-desc="Dismiss update dialog"]
Xpath = {
    
    "search": "//*[@text='Search']|//*[@text='Tìm kiếm']",
    "comment_button": '//*[contains(@content-desc, "Read or add comments")]',
    "like_button": '//*[@content-desc="Like"]',
    "send_comment": '//*[@content-desc="Post comment"]',
    "send_comment_1": '//*[@resource-id="com.zhiliaoapp.musically:id/cg8" or @content-desc="@2131888260"]',
    "search_button": "//*[@resource-id='com.ss.android.ugc.trill:id/nil']",
    "search_button_2": "//*[@resource-id='com.ss.android.ugc.trill:id/g8v'][2]", 
    "search_button_3": '//*[@resource-id="com.zhiliaoapp.musically:id/j2p" and @content-desc="Search"]',
    "search_button_4": '//*[@resource-id="com.ss.android.ugc.trill:id/jb1" and @content-desc="Tìm kiếm"]|//*[@resource-id="com.ss.android.ugc.trill:id/jbh" and @content-desc="Tìm kiếm"]|//*[@resource-id="com.zhiliaoapp.musically:id/jhs"]',
    "post_1_3": "//*[@resource-id='com.ss.android.ugc.trill:id/s94']",
    "post_1_1":"//*[@resource-id='com.ss.android.ugc.trill:id/sj7']",
    "post_1_2":"//*[@resource-id='com.ss.android.ugc.trill:id/n22']",
    "post_1_4":'//*[@resource-id="com.zhiliaoapp.musically:id/soy"]',
    "post_1_5":'//*[@resource-id="com.ss.android.ugc.trill:id/t4i"]|//*[@resource-id="com.ss.android.ugc.trill:id/t2v"]|//*[@resource-id="com.zhiliaoapp.musically:id/txw"]',
    "share_button": '//*[contains(@content-desc, "Share video")]',
    "reup_button": '//*[contains(@content-desc,"Add or remove this video from Favorites")]',
    "profile_button": '//*[@content-desc="Profile"]',
    "edit_button" : '//*[@text="Edit"]',
    "update_bio":'//*[@text="Bio"]',
    "bio_field": "//*[@resource-id='com.ss.android.ugc.trill:id/ekb']|//*[@resource-id='com.zhiliaoapp.musically:id/grs']",
    "save_button": '//*[@text="Save"]',
    "close_button": '//*[@content-desc="Close"]',
    "x_button": "//*[@resource-id='com.ss.android.ugc.trill:id/jvf']",
    "share_button": '//*[@resource-id="com.ss.android.ugc.trill:id/nwg"]',
    "share_button_1":'//*[@resource-id="com.zhiliaoapp.musically:id/u2_"]',
    "repost_button": '//*[@content-desc="Repost"]/android.widget.FrameLayout[1]',
    "save_button": '//*[contains(@content-desc,"Add or remove this video from Favorites") and @selected="false"]'
}

sheet_id = "14A4XmH66m5bckyGmudP8EJB_xKtsurA7BA4R54aTVz8"
sheet_name = "seeding"
pkgs = ["com.ss.android.ugc.trill", "com.zhiliaoapp.musically"]

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

creds = service_account.Credentials.from_service_account_file(
    "aber-129b1-d3ca26ba130a.json",
    scopes=SCOPES
)

service = build('sheets', 'v4', credentials=creds)

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

def get_bold_phone_rows(spreadsheet_id, sheet_name):
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
            "Status": cell(4),
            "comment_language": cell(10),
            "Avatar": cell(7),
            "Bio": cell(8),
            "Name": cell(9),
            "Key_Word": cell(11),
            "Total Time": cell(12), # Cột chứa API keys (cách nhau bởi | hoặc \n)
            "API_KEY" : cell(13)
        })
    return result

# Fetch dữ liệu từ Google Sheet
sheet_data = get_bold_phone_rows(sheet_id, sheet_name)


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
        print('Không tìm thấy file ảnh nào.')
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
        except Exception:
            print("Response không có text:", data)
    else:
        print("Lỗi API key hoặc request thất bại:", res.status_code)

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
            print(f"Response không có text: {data}")
            return []
    else:
        print(f"Lỗi API key hoặc request thất bại: {res.status_code}")
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
        print(f"Error in searchByKeyWord: {e}")

def like(d):
    try:
        print("Liking post")
        d.xpath(Xpath["like_button"]).click()
        random_sleep(10, 12)
    except Exception as e:
        print(f"Error in like: {e}")

def comment(d, comment_language,api_key):

    try:
        print("💬 Commenting on post")
        post_caption = d.xpath("//*[@resource-id='com.zhiliaoapp.musically:id/desc']|//*[@resource-id='com.ss.android.ugc.trill:id/desc']").get_text()
        d.xpath(Xpath["comment_button"]).click()
        random_sleep(3,6)
        print(f"caption:{post_caption}")
        # Generate comment mới từ API (chỉ truyền 2 tham số)
        commentText = generate_comment(comment_language, post_caption,api_key)
        d.xpath('//*[@text="Add comment..."]|//*[@text="Thêm bình luận..."]').click()
        print(f"Generated comment: {commentText}")
        d.send_keys(commentText)
        random_sleep(3,6)
        d.xpath('//*[@content-desc="@2131953937"]|//*[@content-desc="@2131888501"]|//*[@content-desc="@2131888199"]|//*[@content-desc="@2131888218"]|//*[@content-desc="@2131888231"]|//*[@content-desc="Post comment"]|//*[@resource-id="com.zhiliaoapp.musically:id/cg8" or @content-desc="@2131888260"]|//*[@content-desc="@2131888282"]|//*[@content-desc="@2131888272"]|//*[@resource-id="com.zhiliaoapp.musically:id/cgt"]'+ " | " + Xpath["send_comment"] + "|" + Xpath["send_comment_1"]).click()
        random_sleep(5,8)
        w, h = d.window_size()
        x = int(w * 0.5)
        y = int(h * 0.2)
        d.click(x, y)
        print("✅ Comment posted successfully")
        
    except Exception as e:
        print(f"❌ Error in comment: {e}")

def save_video(d):
    try:
        print("Saving video")
        d.xpath(Xpath["save_button"]).click()
    except Exception as e:
        print(f"Error in save video: {e}")

def repost(d):
    try:
        print("Reposting video")
        d.xpath(Xpath["share_button_1"]).click()
        random_sleep(2, 4)
        if d.xpath('//*[@content-desc="Remove repost"]/android.widget.FrameLayout[1]').exists:
            d.press("back")
        else:
            d.xpath(Xpath["repost_button"]).click()
    except Exception as e:
        print(f"Error in repost: {e}")

def scroll(d):
    try:
        print("Scrolling to next post")
        d.swipe(500, 1500, 500, 500, duration=0.2)
    except Exception as e:
        print(f"Error in scroll: {e}")

def view(d):
    try:
        print("Viewing post only")
        random_sleep(2, 4)
    except Exception as e:
        print(f"Error in view: {e}")
def update_avatar(data):
    drive_link = str(data["Avatar"])
    phone_ids = get_phone_ids("14A4XmH66m5bckyGmudP8EJB_xKtsurA7BA4R54aTVz8", "seeding")
    items = dowload_img_by_link(drive_link)
    assigned_links = distribute_links(phone_ids, items)
    device_id = str(data["Phone ID"])
    link_x = None
    for item in assigned_links:
        if item["Phone ID"] == device_id:
            link_x = item["Link"]
            break
    d = u2.connect(device_id)
    d.press("home")
    d.app_stop("com.zhiliaoapp.musically")
    d.app_clear("com.genfarmer.uiautomator")
    try:
        subprocess.run([
            "adb", "-s", device_id,
            "shell", "am", "start",
            "-a", "android.intent.action.VIEW",
            "-d", link_x
        ])
        random_sleep(5, 7)
        d.xpath('//*[@content-desc="Tải xuống"]|//*[@content-desc="Download"]|//*[@text="Download"]').click_exists()
        random_sleep(10,12)
        print("Update avatar")
        d.app_start("com.ss.android.ugc.trill")
        random_sleep(3, 6)
        d.xpath(Xpath["profile_button"]).click()
        random_sleep(2, 4)
        d.xpath('//*[@text="Edit"]').click()
        time.sleep(2)
        d.xpath('//*[@text="Change photo"]').click()
        time.sleep(3)
        d.xpath('//*[@text="Upload photo"]').click()
        random_sleep(3,5)
        d.xpath('//android.widget.GridView/android.widget.FrameLayout[1]').click()
        random_sleep(4,5)
        d.xpath('//*[@text="Next"]').click()
        random_sleep(1,2)
        d.xpath('//*[@text="Next (1)"]').click()
        random_sleep(4,5)
        d.xpath("//*[contains(@text, 'post')]").click()
        time.sleep(2)
        d.xpath("//*[contains(@text, 'post')]").click_exists(5)
        print("Avatar updated successfully")
        time.sleep(4)
        d.press('home')
        d.app_stop("com.ss.android.ugc.trill")
    except Exception as e:
        print(f"Error in update_bio: {e}")

def update_bio(data):
    device_id = str(data["Phone ID"])
    bio = str(data["Bio"])
    d = u2.connect(device_id)
    d.press("home")
    d.app_stop("com.zhiliaoapp.musically")
    d.app_clear("com.genfarmer.uiautomator")
    try:
        print("Update bio")
        d.app_start("com.zhiliaoapp.musically")
        random_sleep(3, 6)
        d.xpath(Xpath["profile_button"]).click()
        random_sleep(2, 4)
        d.xpath(Xpath["edit_button"]).click()
        random_sleep(2, 4)
        d.xpath(Xpath["update_bio"]).click()
        random_sleep(2, 4)
        if d.xpath('//*[@text="Add a bio"]').exists or d.xpath('//*[@text="Write a short description about who you are or what your account is about"]').exists:
            d.xpath('//*[@text="Add a bio"]').click()
            d.send_keys(bio)
        else: 
            d.xpath(Xpath["bio_field"]).long_click()
            random_sleep(1, 2)
            d.xpath('//*[@text="Select all"]').click()
            d.clear_text()
            random_sleep(3,6)
            d.send_keys(bio)
        random_sleep(1, 2)
        d.xpath(Xpath["save_button"]).click()
        time.sleep(4)
        d.press('home')
        d.app_stop("com.zhiliaoapp.musically")

        print("Bio updated successfully")
    except Exception as e:
        print(f"Error in update_bio: {e}")

def update_name(data):
    device_id = str(data["Phone ID"])
    name = str(data["Name"])
    d = u2.connect(device_id)
    d.press("home")
    d.app_stop("com.zhiliaoapp.musically")
    d.app_clear("com.genfarmer.uiautomator")
    try:
        print("Update name")
        d.app_start("com.zhiliaoapp.musically")
        random_sleep(3, 6)
        d.xpath(Xpath["profile_button"]).click()
        random_sleep(2, 4)
        d.xpath(Xpath["edit_button"]).click()
        random_sleep(2, 4)
        d.xpath('//*[@text="Name"]').click()
        random_sleep(2, 4)
        if d.xpath('//*[@resource-id="com.ss.android.ugc.trill:id/hdf"]').exists :
            d.xpath('//*[@resource-id="com.ss.android.ugc.trill:id/hdf"]').click()
            random_sleep(1, 2)
            d.xpath('//*[@resource-id="com.ss.android.ugc.trill:id/ekb"]').click()
            random_sleep(1,2)
            d.send_keys(name)
            d.xpath(Xpath["save_button"]).click()
            random_sleep(3,6)
            d.xpath('//*[@text="Confirm"]').click()
        else: 
            d.xpath('//*[@resource-id="com.ss.android.ugc.trill:id/ekb"]').click()
            random_sleep(1,2)
            d.send_keys(name)
            d.xpath(Xpath["save_button"]).click()
        time.sleep(4)
        d.press('home')
        d.app_stop("com.ss.android.ugc.trill")
        print("Name updated successfully")
    except Exception as e:
        print(f"Error in update_name: {e}")


def flow1(d, keyWord, comment_language, api_key):
    """Flow 1: Search by keyword and interact"""
    actions = ["comment", "like", "view", "view", "view", "like", "like", "like", "save", "save"]  # Tăng tỷ lệ view và like
    try:
        random_sleep(3, 6)
        
        # Generate danh sách từ khóa liên quan
        print(f"🔍 Đang generate từ khóa liên quan đến '{keyWord}'...")
        keyword_list = generate_keyword(comment_language, keyWord, api_key)
        print(keyword_list)
        
        if not keyword_list:
            print("⚠️ Không generate được từ khóa, sử dụng từ khóa gốc")
            keyword_list = [keyWord]
        
        print(f"📝 Danh sách từ khóa: {keyword_list}")
        
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
            print(f"🔎 Search với từ khóa: {current_keyword}")
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
                    print(f"⚠️ Lỗi khi thực hiện action: {e}")
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
        print(f"❌ Lỗi trong firstflow: {e}")

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
        print("📱 Mở app TikTok và lướt For You Feed...")
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

            print(f"chosen: {chosen_action}")
            
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
        print(f"❌ Lỗi trong secondflow: {e}")

def main_flow(data):
    device_id = str(data["Phone ID"])
    keyWord = str(data["Key Word"])
    comment_language = str(data["comment_language"])
    api_key = str(data["API_KEY"])
    total_time = str(data["Total Time"])
    time.sleep(10)

    device = u2.connect(device_id)

    print(f"Đang kết nối đến máy : {device_id}")
    
    try:
        if not total_time:
            while True:
                # Chạy flow1
                print("🔄 Bắt đầu Flow 1...")
                flow1(device, keyWord, comment_language, api_key)
                
                # Chạy flow2
                print("🔄 Bắt đầu Flow 2...")
                flow2(device, comment_language, api_key)
        else:
            end_time = time.time() + int(total_time) * 60
            while time.time() < end_time:
                # Chạy flow1
                print("🔄 Bắt đầu Flow 1...")
                flow1(device, keyWord, comment_language, api_key)
                
                # Chạy flow2
                print("🔄 Bắt đầu Flow 2...")
                flow2(device, comment_language, api_key)
            
            device.press('home')
        
        # update_running_result(sheet_id, sheet_name, device_id, "✅ Hoàn thành")
        
    except Exception as e:
        error_msg = f"❌ Lỗi: {str(e)}"
        print(error_msg)
        update_running_result(sheet_id, sheet_name, device_id, error_msg)