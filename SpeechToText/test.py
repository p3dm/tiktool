import requests, base64, json
import requests
import base64
import subprocess
import json
import sqlite3

import requests
import json

# ====== Cấu hình ======
API_KEY = "AIzaSyDj-EHr9kh-0q50Z-ygDrzAwVuOvjW906U"   # thay bằng API key của bạn
MODEL = "gemini-2.5-flash-lite"
TARGET_LANG = "Vietnamese"

TRANSLATION_RULE = (
    f"Translate the text into {TARGET_LANG}.\n"
    "IMPORTANT CONSTRAINTS:\n"
    "- Preserve meaning with high fidelity; do not omit essential information.\n"
    "- The translation may be slightly longer, but aim to stay close to the original length.\n"
    "- Prefer concise paraphrasing over literal expansion.\n"
    "- The output should sound natural when spoken aloud.\n"
    "- Avoid long compound sentences.\n"
    "- Do NOT use abbreviations.\n"
)

# ====== Văn bản cần dịch (~100 từ) ======
text_to_translate = (
    "Artificial intelligence is rapidly transforming the way we live and work. "
    "From healthcare to education, AI systems are being used to analyze data, "
    "make predictions, and provide personalized recommendations. "
    "In healthcare, AI can help doctors detect diseases earlier and suggest "
    "treatment options more accurately. In education, intelligent tutoring "
    "systems can adapt lessons to the needs of each student, making learning "
    "more effective. However, the rise of AI also raises important ethical "
    "questions, such as how to ensure fairness, protect privacy, and prevent "
    "misuse. Addressing these challenges will be critical for building trust "
    "in AI technologies."
)

# ====== Prompt dịch ======
prompt_text = (
    "Please translate the following passage into Vietnamese.\n"
    f"{TRANSLATION_RULE}\n\n"
    f"{text_to_translate}"
)

payload = {
    "contents": [
        {
            "parts": [
                {"text": prompt_text}
            ]
        }
    ]
}

headers = {
    "x-goog-api-key": API_KEY,
    "Content-Type": "application/json"
}

# ====== Đo token input ======
count_url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:countTokens"
resp_count = requests.post(count_url, headers=headers, json=payload).json()
print("Token input:", resp_count)

# ====== Gửi request dịch ======
url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
resp = requests.post(url, headers=headers, json=payload).json()

print(resp)
# print("Đã tạo file out.wav")