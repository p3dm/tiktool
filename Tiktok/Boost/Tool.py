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

Like_xpath = '//*[@content-desc="Like" and @selected="false"]'
commentButton_xpath='//*[contains(@content-desc, "Read or add comments")]'
shareButton_xpath='//*[contains(@content-desc, "Share video")]'
reupButton_xpath = '//*[contains(@content-desc,"Add or remove this video from Favorites") and @selected="false"]'

def do_like(d):
    d.xpath(Like_xpath).click_exists(2)

def do_comment(d,listComment):
    d.xpath(commentButton_xpath).click()
    time.sleep(2)
    d.xpath('//*[@text="Add comment..."]').click()
    time.sleep(3)
    comments = listComment.split("|")
    random_comment = random.choice(comments)
    d.send_keys(random_comment)
    print(random_comment)
    d.xpath('//*[@content-desc="@2131888199"]|//*[@content-desc="@2131888218"]|//*[@content-desc="@2131888231"]|//*[@content-desc="Post comment"]|//*[@resource-id="com.zhiliaoapp.musically:id/cg8" or @content-desc="@2131888260"]').click()
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
    d.press("home")
    d.app_stop("com.zhiliaoapp.musically")
    d.app_clear("com.genfarmer.uiautomator")
    special_actions = [
        "comment",
        "share",
        "repost",
        "save"
    ]
    actions = special_actions + ["view"] * (view_buff - len(special_actions))
    random.shuffle(actions)

    for i in range(1, view_buff + 1):
        if i > 2:
            action = actions[i - 1]
        else: 
            action_first = ["view","comment", "like"]
            action = random.choice(action_first)
            action_first.remove(action)
            
        w, h = d.window_size()
        time.sleep(sleep_time)
        d.swipe(w * 0.5, h * 0.88, w * 0.5, h * 0.3, 0.2)
        time.sleep(5)
        d.swipe(w * 0.5, h * 0.3, w * 0.5, h * 0.7, 0.2)
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

def upload_video(d,music,caption):
    installed = set(d.app_list())  # all installed packages
    for pkg in pkgs:
        if pkg in installed:
            d.app_start(pkg)
            break
    print("[LOG] Start TikTok app")

    time.sleep(random.uniform(7, 8))

    d.xpath('//*[@content-desc="Create"]|//*[@resource-id="com.ss.android.ugc.trill:id/mva"]|//*[@resource-id="com.zhiliaoapp.musically:id/myb"]').click()
    print("[LOG] Click Create (+)")

    time.sleep(2)

    d.xpath('//*[@resource-id="com.ss.android.ugc.trill:id/ch5"]|//*[@resource-id="com.ss.android.ugc.trill:id/f49"]|//*[@resource-id="com.zhiliaoapp.musically:id/cib"]|//*[@resource-id="com.zhiliaoapp.musically:id/chq"]').click()
    print("[LOG] Click Upload")

    d.xpath('//android.widget.GridView/android.widget.FrameLayout[1]/android.widget.FrameLayout[2]/*[@resource-id="com.zhiliaoapp.musically:id/fsq"]|//*[@resource-id="com.ss.android.ugc.trill:id/n56"]').click()
    print("[LOG] Click first image in GridView")
    time.sleep(3)

    d.xpath('//*[@text="Next" and @resource-id="com.zhiliaoapp.musically:id/o__"]|//*[@resource-id="com.ss.android.ugc.trill:id/o67"]').click()
    print("[LOG] Click Next (step 1)")
    time.sleep(2)
    if(music != None):
        d.xpath('//*[@resource-id="com.zhiliaoapp.musically:id/ycm"]|//*[@resource-id="com.ss.android.ugc.trill:id/z0v"]|//*[@content-desc="Music"]').click()
        print("[LOG] Click Next / Continue (step 2)")
        time.sleep(3)
        d.xpath('//*[@resource-id="com.zhiliaoapp.musically:id/h1x"]').click()
        print("[LOG] Focus search / input field")

        time.sleep(3)

        d.send_keys(music, clear=True)
        print("[LOG] Type search text: That girl")

        time.sleep(3)

        d.xpath('//*[@text="Search"]').click()
        print("[LOG] Click Search")

        time.sleep(3)

        d.xpath('//android.widget.FrameLayout/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[@focusable="true"]').click()
        print("[LOG] Select first search result")

        time.sleep(3)

        w, h = d.window_size()
        x = w * random.uniform(0.48, 0.52)
        y = h * random.uniform(0.30, 0.33)
        d.click(x, y)
        print("[LOG] Click position 50% width - 65% height")

    time.sleep(3)
    d.xpath('//*[@text="Next"]|//*[@resource-id="com.ss.android.ugc.trill:id/o6e"]|//*[@resource-id="com.ss.android.ugc.trill:id/o6h"]').click()
    time.sleep(3)
    d.xpath('//*[@text="Add description..."]|//*[@text="Writing a long description can help get 3x more views on average."]').click(10)
    print("[LOG] Description hint detected")

    time.sleep(2)
    d.send_keys(caption+" ")
    print("[LOG] Type caption text")
    d.xpath('//*[@text="Post"]|//*[@resource-id="com.zhiliaoapp.musically:id/rd1"]').click()
    time.sleep(15)
    d.press("home")

def open_link(link, device_id):
    command = ["adb", "-s", device_id, "shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", link]
    subprocess.run(command)

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


