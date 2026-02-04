import sqlite3
import os
import re

def load_audio_segments(segment_dir):
    files = os.listdir(segment_dir)
    files.sort(key=lambda x: int(re.search(r"seg_(\d+)", x).group(1)))
    return files

def load_start_timestamps(db_path, table):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(f"""
        SELECT timestamp
        FROM {table}
        ORDER BY id
    """)

    timestamps = [row[0] for row in cursor.fetchall()]
    conn.close()
    return timestamps

def parse_mm_ss(ts):
    mm, ss = ts.split(":")
    return (int(mm) * 60 + int(ss)) * 1000
from pydub import AudioSegment

def build_audio_timeline(audio_files, timestamps, segment_dir):
    timeline = AudioSegment.silent(duration=0)

    for i in range(len(audio_files)):
        start_ms = parse_mm_ss(timestamps[i])
        seg_audio = AudioSegment.from_wav(
            os.path.join(segment_dir, audio_files[i])
        )

        # Nếu timeline hiện tại chưa tới start → chèn silence
        if len(timeline) < start_ms:
            silence = AudioSegment.silent(duration=start_ms - len(timeline))
            timeline += silence

        timeline += seg_audio

    return timeline
timestamps = load_start_timestamps(
    db_path="videos.db",
    table="video4"
)

audio_files = load_audio_segments("segments")

final_audio = build_audio_timeline(
    audio_files,
    timestamps,
    segment_dir="segments"
)

final_audio.export("final_audio.wav", format="wav")
print("✅ Đã tạo final_audio.wav")
