import requests
import sqlite3
import requests, base64, json
import requests
import base64
import subprocess
import json
import sqlite3
def load_video_data(db_path, table_name):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()


    # Load meta (1 row)
    cursor.execute(f"""
        SELECT purpose, tone, audience
        FROM {table_name}
        WHERE id = 1
    """)
    meta_row = cursor.fetchone()

    if not meta_row:
        conn.close()
        raise ValueError("Meta data not found")

    meta = {
        "purpose": meta_row[0],
        "tone": meta_row[1],
        "audience": meta_row[2]
    }

    # Load segments
    cursor.execute(f"""
        SELECT timestamp, translated_text
        FROM {table_name}
        ORDER BY id
    """)

    segments = [
        {
            "timestamp": ts,
            "translated_text": en
        }
        for ts, en in cursor.fetchall()
    ]

    conn.close()

    return {
        "meta": meta,
        "segments": segments
    }

video_data = load_video_data(
    db_path="videos.db",
    table_name="video4"
)

meta = video_data["meta"]
segments = video_data["segments"]

voice_prompt = (
    f"You are speaking to the viewer in a natural, conversational way.\n"
    f"Purpose: {meta['purpose']}.\n"
    f"Target audience: {meta['audience']}.\n"
    f"Overall tone: {meta['tone']}.\n"
    f"Speak as a real person, not a formal narrator.\n"
    f"Speak slightly faster than normal everyday conversation.\n"
    f"Maintain a clear, energetic pace without sounding rushed.\n"
    f"Use brief, efficient pauses only when necessary.\n"
    f"Change pitch and emphasis naturally to keep it engaging.\n"
    f"Avoid long pauses or drawn-out delivery.\n"
    f"Sound friendly, lively, and confident.\n"
    f"When you see [PAUSE_1S], stop speaking completely for about 1.5 seconds before continuing."
)


API_KEY = "AIzaSyByXB_xd0ZVRPgRM6h6fSYbsRKumYsCYy8"

url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-tts:generateContent"

headers = {
    "x-goog-api-key": API_KEY,
    "Content-Type": "application/json"
}

# Giả sử bạn đã có dữ liệu segments từ Gemini STT
# data['segments'] = [
#   {"timestamp":"00:00:01", "original_text":"...", "english_translation":"Top best AIs to help you build a channel in 2026, from free to paid."},
#   {"timestamp":"00:00:05", "original_text":"...", "english_translation":"Tora 2"}
# ]

# Chuẩn bị text cho TTS: mỗi câu 1 đoạn, nghỉ 1s
text_for_tts = ""
for seg in segments:
    # Lấy từng sentence trong english_translation (có thể tách bằng dấu chấm)
    sentences = [seg["translated_text"].strip()] if seg["translated_text"].strip() else []
    for sentence in sentences:
        text_for_tts += sentence + " [PAUSE_1S] "

# Tạo payload TTS" [PAUSE_5S] "
payload = {
    "contents": [{
        "parts": [{
            "text":voice_prompt + "\n\n---\n\n" + text_for_tts
        }]
    }],
    "generationConfig": {
        "responseModalities": ["AUDIO"],
        "speechConfig": {
            "voiceConfig": {
                "prebuiltVoiceConfig": {
                    "voiceName": "Algieba"
                }
            }
        }
    },
    "model": "gemini-2.5-flash-preview-tts"
}

# Gửi request TTS
response = requests.post(url, headers=headers, json=payload)
response.raise_for_status()
data_tts = response.json()

# Lấy audio base64
audio_b64 = data_tts["candidates"][0]["content"]["parts"][0]["inlineData"]["data"]

# Giải mã PCM
pcm_bytes = base64.b64decode(audio_b64)

# Lưu PCM ra file
with open("out.pcm", "wb") as f:
    f.write(pcm_bytes)

print("Đã tạo file out.pcm")

# Chuyển PCM -> WAV
subprocess.run([
    "ffmpeg",
    "-y",
    "-f", "s16le",
    "-ar", "24000",
    "-ac", "1",
    "-i", "out.pcm",
    "out.wav"
])

print("Đã tạo file out.wav")