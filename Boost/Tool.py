import uiautomator2 as u2
import subprocess
import time
import random
import os
import requests
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
from jinja2 import Template
import json

pkgs = ["com.ss.android.ugc.trill", "com.zhiliaoapp.musically"]

Like_xpath = '//*[@content-desc="Like" and @selected="false"]|//*[@content-desc="Thích" and @selected="false"]'
commentButton_xpath='//*[contains(@content-desc, "Read or add comments")]'
shareButton_xpath='//*[contains(@content-desc, "Share video")]'
reupButton_xpath = '//*[contains(@content-desc,"Add or remove this video from Favorites") and @selected="false"]|//*[contains(@content-desc,"Thêm hoặc xóa video này khỏi mục Yêu thích.") and @selected="false"]'

def do_like(d):
    if d.xpath(Like_xpath).exists:
        d.xpath(Like_xpath).click()

def do_comment(d,listComment):
    d.xpath(commentButton_xpath).click()
    time.sleep(2)
    d.xpath('//*[@text="Add comment..."]|//*[@text="Thêm bình luận..."]').click()
    time.sleep(3)
    comments = listComment.split("|")
    random_comment = random.choice(comments)
    d.send_keys(random_comment)
    d.xpath('//*[@content-desc="@2131953937"]|//*[@content-desc="@2131888501"]|//*[@content-desc="@2131888199"]|//*[@content-desc="@2131888218"]|//*[@content-desc="@2131888231"]|//*[@content-desc="Post comment"]|//*[@resource-id="com.zhiliaoapp.musically:id/cg8" or @content-desc="@2131888260"]|//*[@content-desc="@2131888282"]|//*[@content-desc="@2131888272"]|//*[@resource-id="com.zhiliaoapp.musically:id/cgt"]').click()
    time.sleep(2)
    w, h = d.window_size()
    x = int(w * 0.5)
    y = int(h * 0.2)
    d.click(x, y)
def do_repost(d):
    d.xpath(shareButton_xpath).click()
    time.sleep(2)
    d.xpath('//*[@content-desc="Copy link"]').click()
def do_save(d):
    d.xpath(reupButton_xpath).click_exists(2)
def buff_view(view_buff,sleep_time,d,listComment):
    special_actions = [
        "like",
        "comment",
        "save"
    ]
    if listComment == "":
        special_actions.remove("comment")
    actions = special_actions + ["view"] * (view_buff - len(special_actions))
    random.shuffle(actions)

    for i in range(1, view_buff + 1):
        try:
            action = actions[i - 1]
            w, h = d.window_size()
            time.sleep(sleep_time)
            d.swipe(w * 0.5, h * 0.88, w * 0.5, h * 0.3, 0.2)
            time.sleep(5)
            d.swipe(w * 0.5, h * 0.3, w * 0.5, h * 0.7, 0.2)
            print(f"{action}")
            if action == "like":
                do_like(d)
            elif action == "comment":
                do_comment(d,listComment)
            elif action == "repost":
                do_repost(d)
            elif action == "save":
                do_save(d)
            else:
                time.sleep(sleep_time)
                continue
            time.sleep(sleep_time)
        except Exception as e:
            continue

def upload_video(d,music,caption):
    installed = set(d.app_list())  # all installed packages
    for pkg in pkgs:
        if pkg in installed:
            d.press("home")
            d.app_stop(pkg)
            d.app_start(pkg)
            break

    time.sleep(random.uniform(7, 8))

    d.xpath('//*[@content-desc="Create"]|//*[@content-desc="Quay"]|//*[@resource-id="com.ss.android.ugc.trill:id/mva"]|//*[@resource-id="com.zhiliaoapp.musically:id/myb"]').click()
    time.sleep(5)

    d.xpath('//*[@resource-id="com.ss.android.ugc.trill:id/lhv"]|//*[@resource-id="com.ss.android.ugc.trill:id/lh7"]|//*[@resource-id="com.ss.android.ugc.trill:id/hqn"]|//*[@resource-id="com.ss.android.ugc.trill:id/ch5"]|//*[@resource-id="com.ss.android.ugc.trill:id/f49"]|//*[@resource-id="com.zhiliaoapp.musically:id/cib"]|//*[@resource-id="com.zhiliaoapp.musically:id/chq"]|//*[@resource-id="com.zhiliaoapp.musically:id/l_n"]|//*[@resource-id="com.zhiliaoapp.musically:id/l_p"]').click()
    time.sleep(5)

    d.xpath('//android.widget.GridView/android.widget.FrameLayout[1]/android.widget.FrameLayout[1]/*[@resource-id="com.zhiliaoapp.musically:id/fsq"]|//android.widget.GridView/android.widget.FrameLayout[1]/android.widget.FrameLayout[2]/*[@resource-id="com.ss.android.ugc.trill:id/g13"]|//android.widget.GridView/android.widget.FrameLayout[1]/android.widget.FrameLayout[2]/*[@resource-id="com.ss.android.ugc.trill:id/fzs"]|//*[@resource-id="com.ss.android.ugc.trill:id/g13"]|//*[@resource-id="com.ss.android.ugc.trill:id/n56"]|//android.widget.GridView/android.widget.FrameLayout[1]/android.widget.FrameLayout[2]/*[@resource-id="com.zhiliaoapp.musically:id/fvf"]|//android.widget.GridView/android.widget.FrameLayout[1]/android.widget.FrameLayout[2]/*[@resource-id="com.zhiliaoapp.musically:id/fu_"]|//android.widget.GridView/android.widget.FrameLayout[1]/android.widget.FrameLayout[2]/*[@resource-id="com.ss.android.ugc.trill:id/dwo"]').click()
    time.sleep(5)

    d.xpath('//*[@text="Next"]|//*[@text="Tiếp"]|//*[@text="Next (1)"]|//*[@resource-id="com.ss.android.ugc.trill:id/p9b"]').click()
    time.sleep(5)
    if(music != None):
        time.sleep(5)
        d.xpath('//*[@text="Add sound"]|//*[@resource-id="com.ss.android.ugc.trill:id/rqh"]').click()
        time.sleep(5)
        d.xpath('//*[@content-desc="Search"]').click()
        time.sleep(5)
        d.send_keys(music, clear=True)

        time.sleep(5)

        d.xpath('//*[@text="Search"]').click()

        time.sleep(5)
        d.xpath('//androidx.recyclerview.widget.RecyclerView/android.widget.FrameLayout[2]/android.view.ViewGroup[1]/android.view.ViewGroup[1]/android.view.ViewGroup[2]').click()
        time.sleep(5)
        w, h = d.window_size()
        x = w * random.uniform(0.48, 0.52)
        y = h * random.uniform(0.30, 0.33)
        d.click(x, y)   

    time.sleep(5)
    if d.xpath('//*[@text="Next"]|//*[@text="Tiếp"]|//*[@resource-id="com.ss.android.ugc.trill:id/o6e"]|//*[@resource-id="com.ss.android.ugc.trill:id/o6h"]|//*[@resource-id="com.ss.android.ugc.trill:id/p9b"]').exists:
        d.xpath('//*[@text="Next"]|//*[@text="Tiếp"]|//*[@resource-id="com.ss.android.ugc.trill:id/o6e"]|//*[@resource-id="com.ss.android.ugc.trill:id/o6h"]|//*[@resource-id="com.ss.android.ugc.trill:id/p9b"]').click()

    time.sleep(5)
    if(caption != None):
        d.xpath('//*[@text="Add description..."]|//*[@text="Thêm mô tả..."]|//*[@text="Writing a long description can help get 3x more views on average."]|//*[@resource-id="com.ss.android.ugc.trill:id/e7f"]').click(10)
        time.sleep(5)
        d.send_keys(caption +"")
    d.xpath('//*[@text="Post"]|//*[@text="Đăng"]|//*[@resource-id="com.zhiliaoapp.musically:id/rd1"]').click()
    time.sleep(90-120)
    d.xpath('//*[@resource-id="com.ss.android.ugc.trill:id/j4y"]|//*[@resource-id="com.zhiliaoapp.musically:id/n19"]').click()
    time.sleep(30)
    d.swipe(w * 0.5, h * 0.3, w * 0.5, h * 0.7, 0.2)
    d.press("home")
    

def open_link(link, device_id):
    command = ["adb", "-s", device_id, "shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", link]
    subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NO_WINDOW)

def getCommentByAI(api_key, post_data,seeding_language,niche,topic,customer_portrait,goal_of_interaction):
    prompt = f"""
    Bạn là một AI chuyên tạo comment trên TikTok.  
    Dữ liệu đầu vào:  
    - post_data: {post_data}  
    - seeding_language: {seeding_language}  
    - niche: {niche}  
    - topic: {topic}  
    - customer_portrait: {customer_portrait}  
    - goal_of_interaction: {goal_of_interaction}  

    Yêu cầu:  
    - Sinh ra một comment ngắn gọn, tự nhiên, phù hợp với nội dung post_data.  
    - Comment phải sử dụng đúng seeding_language.  
    - Nội dung phải liên quan đến niche và topic.  
    - Phù hợp với customer_portrait.  
    - Đáp ứng goal_of_interaction.  
    - Chỉ trả về comment, không giải thích gì thêm.
    """


    url = (
        "https://generativelanguage.googleapis.com/v1beta/"
        "models/gemini-2.5-flash-lite:generateContent"
        f"?key={api_key}"
    )

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 100
        }
    }

    headers = {
        "Content-Type": "application/json"
    }

    response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)

    try:
        result = response.json()
    except ValueError:
        raise Exception(f"Gemini API trả về dữ liệu không phải JSON. HTTP {response.status_code}: {response.text}")

    # API có thể trả về error thay vì candidates (ví dụ: invalid key, quota exceeded)
    if "error" in result:
        error_info = result.get("error", {})
        error_message = error_info.get("message", "Unknown Gemini API error")
        error_status = error_info.get("status", "UNKNOWN")
        raise Exception(f"Gemini API error [{error_status}]: {error_message}")

    candidates = result.get("candidates")
    if not candidates:
        raise Exception(f"Gemini API không có candidates. HTTP {response.status_code}. Response: {json.dumps(result, ensure_ascii=False)}")

    content = candidates[0].get("content", {})
    parts = content.get("parts", [])
    if not parts:
        raise Exception(f"Gemini API candidates không có parts. Response: {json.dumps(result, ensure_ascii=False)}")

    comment = parts[0].get("text", "").strip()
    if not comment:
        raise Exception(f"Gemini API trả về comment rỗng. Response: {json.dumps(result, ensure_ascii=False)}")

    return comment


