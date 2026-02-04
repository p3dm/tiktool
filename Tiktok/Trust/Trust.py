import random
import uiautomator2 as u2
import time
import requests
from google.oauth2 import service_account
from googleapiclient.discovery import build
import subprocess
import json
keyWord = []
total_time = 0
# API keys cho Gemini - Thêm keys của bạn vào đây

Xpath = {
    "search": "//*[@content-desc='Search']",
    "comment_button": '//*[contains(@content-desc, "Read or add comments")]',
    "like_button": '//*[@content-desc="Like"]',
    "send_comment": '//*[@content-desc="@2131888199]',
    "search_button": "//*[@resource-id='com.ss.android.ugc.trill:id/nil']",
    "post_1": "//*[@resource-id='com.ss.android.ugc.trill:id/n22']",
    "share_button": '//*[contains(@content-desc, "Share video")]',
    "reup_button": '//*[contains(@content-desc,"Add or remove this video from Favorites")]',
    "profile_button": '//*[@content-desc="Profile"]',
    "edit_button" : "//*[@resource-id='com.ss.android.ugc.trill:id/d76']",
    "update_bio":'//*[@text="Add a bio"]',
    "bio_field": "//*[@resource-id='com.ss.android.ugc.trill:id/ekb']",
    "save_button": "//*[@resource-id='com.ss.android.ugc.trill:id/jv8']"
}

sheet_id = "14A4XmH66m5bckyGmudP8EJB_xKtsurA7BA4R54aTVz8"
sheet_name = "seeding"

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

        # ❗ chỉ lấy Phone ID được Ctrl+B
        if not text_fmt.get('bold') or not phone_id:
            continue


        def cell(i):
            return cells[i].get('formattedValue') if i < len(cells) else None

        result.append({
            "Phone ID": phone_id,
            "Link_driver":cell(1),
            "Status": cell(4),
            "comment language": cell(10),
            "Bio": cell(8),
            "Name": cell(9),
            "Key Word": cell(11),
            "Total Time": cell(12), # Cột chứa API keys (cách nhau bởi | hoặc \n)
            "API_KEY" : cell(13)
        })
    return result

# Fetch dữ liệu từ Google Sheet
print("📊 Đang fetch dữ liệu từ Google Sheet...")
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


def searchByKeyWord(d, keyWord):
    try:
        print("Searching")
        d.xpath(Xpath["search"]+'|//*[@resource-id="com.ss.android.ugc.trill:id/n0_"]/android.widget.ImageView[2]').click()
        random_sleep(3,6)
        print(f"Keyword: {keyWord}")
        d.send_keys(keyWord)
        random_sleep(3,6)
        d.xpath('//*[@text="Search"]').click()
        time.sleep(2)
        d.xpath(Xpath["post_1"]).click()
        print("Clicked post 1")
    except Exception as e:
        print(f"Error in searchByKeyWord: {e}")

def like(d):
    try:
        print("Liking post")
        d.xpath(Xpath["like_button"]).click()
        time.sleep(1)
    except Exception as e:
        print(f"Error in like: {e}")

def comment(d, comment_language,api_key):

    try:
        print("💬 Commenting on post")
        post_caption = d.xpath("//*[@resource-id='com.ss.android.ugc.trill:id/desc']").get_text()
        d.xpath(Xpath["comment_button"]).click()
        random_sleep(2, 3)
        print(f"caption:{post_caption}")
        # Generate comment mới từ API (chỉ truyền 2 tham số)
        commentText = generate_comment(comment_language, post_caption,api_key)
        d.xpath('//*[@text="Add comment..."]').click()
        print("{commentText}")
        d.send_keys(commentText)
        random_sleep(2, 3)
        d.xpath('//*[@content-desc="@2131888199"]|//*[@content-desc="@2131888218"]|//*[@content-desc="@2131888231"]').click()
        random_sleep(1, 2)
        print("✅ Comment posted successfully")
        
    except Exception as e:
        print(f"❌ Error in comment: {e}")

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
def update_avatar(d,d_id,link):
    try:

        subprocess.run([
            "adb", "-s", d_id,
            "shell", "am", "start",
            "-a", "android.intent.action.VIEW",
            "-d", link
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
    except Exception as e:
        print(f"Error in update_bio: {e}")

def update_bio(d, bio_text):
    try:
        print("Update bio")
        d.app_start("com.ss.android.ugc.trill")
        random_sleep(3, 6)
        d.xpath(Xpath["profile_button"]).click()
        random_sleep(2, 4)
        d.xpath(Xpath["edit_button"]).click()
        random_sleep(2, 4)
        d.xpath(Xpath["update_bio"]).click()
        random_sleep(2, 4)
        if d.xpath('//*[@text="Add a bio"]').exists :
            d.xpath('//*[@text="Add a bio"]').click()
            d.send_keys(bio_text)
        else: 
            d.xpath(Xpath["bio_field"]).long_click()
            random_sleep(1, 2)
            d.xpath('//*[@text="Select all"]').click()
            d.clear_text()
            random_sleep(3,6)
            d.send_keys(bio_text)
        random_sleep(1, 2)
        d.xpath(Xpath["save_button"]).click()
        random_sleep(2, 4)
        print("Bio updated successfully")
    except Exception as e:
        print(f"Error in update_bio: {e}")

def update_name(d, name_text):
    try:
        print("Update name")
        d.app_start("com.ss.android.ugc.trill")
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
            d.send_keys(name_text)
            d.xpath(Xpath["save_button"]).click()
            random_sleep(3,6)
            d.xpath('//*[@text="Confirm"]').click()
        else: 
            d.xpath('//*[@resource-id="com.ss.android.ugc.trill:id/ekb"]').click()
            random_sleep(1,2)
            d.send_keys(name_text)
            d.xpath(Xpath["save_button"]).click()
        random_sleep(2, 4)
        print("Name updated successfully")
    except Exception as e:
        print(f"Error in update_name: {e}")


def flow1(d, total_time, keyWord, comment_language,api_key):
    """Flow 1: Search by keyword and interact"""
    actions = ["comment"]
    start_time = time.time()
    try:
        d.app_start("com.ss.android.ugc.trill")
        random_sleep(3, 6)
        
        # Vòng lặp ngoài - tìm từ khóa mới nếu còn thời gian
        while True:
            elapsed_time = time.time() - start_time
            if elapsed_time >= total_time:
                print(f"⏱️ Đã hết thời gian ({total_time}s). Dừng chương trình.")
                break
            d.set_fastinput_ime(True)
            searchByKeyWord(d, keyWord)
            random_sleep(10, 12)
            
            # Vòng lặp trong - thực hiện 8-12 lần các action
            for _ in range(random.randint(8, 12)):
                elapsed_time = time.time() - start_time
                
                # Kiểm tra thời gian
                if elapsed_time >= total_time:
                    print(f"⏱️ Đã hết thời gian ({total_time}s). Dừng chương trình.")
                    return
                
                random_sleep(10, 12)
                
                chosen_action = random.choice(actions)
                try:
                    if(chosen_action == "like"):
                        like(d)
                        print("chon like")
                    if(chosen_action == "view"):
                        view(d)
                        print("chon view")
                    if(chosen_action == "comment"):
                        d.set_fastinput_ime(True)
                        comment(d, comment_language,api_key)
                        time.sleep(2)
                        d.press("back")

                        print("chon comment")
                except Exception as e:
                    print(f"⚠️ Lỗi khi thực hiện action: {e}")
                
                scroll(d)
                random_sleep(2, 3)

            elapsed_time = time.time() - start_time
            if elapsed_time >= total_time:
                print(f"⏱️ Đã hết thời gian ({total_time}s). Dừng chương trình.")
                break
            else:
                print(f"⏳ Thời gian còn lại: {total_time - elapsed_time:.1f}s. Tìm từ khóa tiếp...")
                random_sleep(2, 3)
                
    except Exception as e:
        print(f"❌ Lỗi trong firstflow: {e}")

def flow2(d, total_time, comment_language,api_key):
    """Flow 2: Browse For You feed and interact"""
    
    actions = ["comment"]
    start_time = time.time()
    
    try:
        d.app_start("com.ss.android.ugc.trill")
        print("📱 Mở app TikTok và lướt For You Feed...")
        random_sleep(3, 6)
        
        # Vòng lặp liên tục - không cần tìm kiếm
        video_count = 0
        while True:
            elapsed_time = time.time() - start_time
            
            # Kiểm tra thời gian
            if elapsed_time >= total_time:
                print(f"⏱️ Đã hết thời gian ({total_time}s). Đã xem {video_count} video. Dừng chương trình.")
                break
            
            # Dừng 10-15s ở video hiện tại (xem video)
            random_sleep(10, 15)
            
            chosen_action = random.choice(actions)
            print(f"chosen: {chosen_action}")

            if(chosen_action == "like"):
                like(d)
            if(chosen_action == "view"):
                view(d)
            if(chosen_action == "comment"):
                d.set_fastinput_ime(True)
                comment(d, comment_language,api_key)
                time.sleep(2)
                d.press("back")

            
            scroll(d)
            video_count += 1
            random_sleep(1, 2)
            
            if video_count % 10 == 0:
                remaining_time = total_time - elapsed_time
                print(f"📊 Đã xem {video_count} video. Thời gian còn lại: {remaining_time:.1f}s")      
    except Exception as e:
        print(f"❌ Lỗi trong secondflow: {e}")

def main_flow(data):
    rows = get_bold_phone_rows(
        spreadsheet_id="14A4XmH66m5bckyGmudP8EJB_xKtsurA7BA4R54aTVz8",
        sheet_name="seeding"
    )
    drive_link = rows[0]["Link_driver"]
    phone_ids = get_phone_ids("14A4XmH66m5bckyGmudP8EJB_xKtsurA7BA4R54aTVz8", "seeding")
    items = dowload_img_by_link(drive_link)
    assigned_links = distribute_links(phone_ids, items)
    print(assigned_links)

    device_id = str(data["Phone ID"])
    total_time = int(data["Total Time"])
    keyWord = str(data["Key Word"])
    bio = str(data["Bio"])
    name = str(data["Name"])
    comment_language = str(data["comment language"])
    api_key = str(data["API_KEY"])
    time.sleep(10)
    link_x = None

    for item in assigned_links:
        if item["Phone ID"] == device_id:
            link_x = item["Link"]
            break
    device = u2.connect(device_id)

    print(f"Đang kết nối đến máy : {device_id}")
    print(f"new Name: {name}")
    # end_time = time.time() + total_time
    try:
        flow = random.choice(["flow1", "flow2"])
        # print(f"🎯 Chọn flow: {flow}")
        # update_avatar(device,device_id,link_x)
        if flow == "flow1":
            flow1(device, total_time, keyWord, comment_language,api_key)
        else:
            flow2(device, total_time, comment_language,api_key)
        
        # update_bio(device, bio)
        # update_name(device, name)
            
        update_running_result(sheet_id, sheet_name, device_id, "✅ Hoàn thành")
        
    except Exception as e:
        error_msg = f"❌ Lỗi: {str(e)}"
        print(error_msg)
        update_running_result(sheet_id, sheet_name, device_id, error_msg)


