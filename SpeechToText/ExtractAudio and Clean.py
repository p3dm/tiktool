import subprocess
import os

def preprocess_audio_for_asr(
    input_video: str,
    output_wav: str
):
    """
    Pipeline:
    Video
     → Extract audio
     → Mono
     → 16kHz
     → High-pass filter
     → Light denoise
     → Light compression
     → Loudness normalize
     → WAV PCM16 (ASR-ready)
    """

    if not os.path.exists(input_video):
        raise FileNotFoundError(f"Không tìm thấy file: {input_video}")

    cmd = [
        "ffmpeg",
        "-y",
        "-i", input_video,
        "-vn",
        "-ac", "1",                  # mono
        "-ar", "16000",               # 16kHz
        "-acodec", "pcm_s16le",       # PCM 16-bit
        "-af",
        (
            "highpass=f=80,"
            "afftdn=nf=-25,"
            "acompressor=threshold=-18dB:ratio=2:attack=5:release=50,"
            "loudnorm=I=-16:TP=-1:LRA=11"
        ),
        output_wav
    ]

    subprocess.run(cmd, check=True)
    print(f"✅ Xuất audio ASR-ready: {output_wav}")

input_video = "Video-02.mp4"
output_audio = "output_asr.wav"

preprocess_audio_for_asr(input_video, output_audio)
