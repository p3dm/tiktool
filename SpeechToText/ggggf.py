import requests
import json
import base64
import sqlite3

API_KEY = "AIzaSyDZKjNnRKeZ3Qh0jPAByvzUt28BtQzaMNE"
url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"

# Đọc file WAV và encode base64
with open("output_asr.wav", "rb") as f:
    audio_base64 = base64.b64encode(f.read()).decode("utf-8")

headers = {"Content-Type": "application/json"}

data = {
    "contents": [
        {
            "parts": [
                {
                    "text": """Please transcribe the audio/video file.

Requirements:
1. Split the transcript into segments.
2. For each segment, provide:
   - start_time (in seconds)
   - end_time (in seconds)
   - text (spoken content)
3. Output strictly in JSON format with the following structure:

{
  "segments": [
    {
      "start_time": "0",
      "end_time": "2",
      "text": "Hello"
    },
    {
      "start_time": "2",
      "end_time": "5",
      "text": "How are you today"
    }
  ]
}
"""
                },
                {
                    "inline_data": {
                        "mime_type": "audio/wav",
                        "data": audio_base64
                    }
                }
            ]
        }
    ],
    "generation_config": {
        "response_mime_type": "application/json",
        "response_schema": {
            "type": "OBJECT",
            "properties": {
                "segments": {
                    "type": "ARRAY",
                    "items": {
                        "type": "OBJECT",
                        "properties": {
                            "start_time": {"type": "STRING"},
                            "end_time": {"type": "STRING"},
                            "text": {"type": "STRING"}
                        },
                        "required": ["start_time", "end_time", "text"]
                    }
                }
            },
            "required": ["segments"]
        }
    }
}

# Gọi Gemini API
response = requests.post(url, headers=headers, data=json.dumps(data))
result = response.json()

# Lấy ra phần segments (JSON string)
segments_json = result["candidates"][0]["content"]["parts"][0]["text"]
segments = json.loads(segments_json)["segments"]

# --- Lưu vào SQLite ---
conn = sqlite3.connect("transcript.db")
cursor = conn.cursor()

# Tạo bảng nếu chưa có
cursor.execute("""
CREATE TABLE IF NOT EXISTS transcript (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_time TEXT,
    end_time TEXT,
    text TEXT
)
""")

# Insert từng segment
for seg in segments:
    cursor.execute(
        "INSERT INTO transcript (start_time, end_time, text) VALUES (?, ?, ?)",
        (seg["start_time"], seg["end_time"], seg["text"])
    )

conn.commit()
conn.close()

print("Đã lưu transcript vào SQLite thành công!")
