import torch
import soundfile as sf
import numpy as np
import os

# Load Silero VAD
model, utils = torch.hub.load(
    repo_or_dir="snakers4/silero-vad",
    model="silero_vad",
    trust_repo=True
)

(get_speech_timestamps, _, _, _, _) = utils

def load_wav_16k_mono(path):
    wav, sr = sf.read(path)

    if wav.ndim > 1:
        wav = wav.mean(axis=1)

    if sr != 16000:
        import librosa
        wav = librosa.resample(wav, orig_sr=sr, target_sr=16000)

    return torch.from_numpy(wav.astype(np.float32)), 16000

def run_vad_and_save_segments(wav_path, out_dir="segments"):
    os.makedirs(out_dir, exist_ok=True)

    wav, sr = load_wav_16k_mono(wav_path)

    speech_timestamps = get_speech_timestamps(
        wav,
        model,
        sampling_rate=sr,
        threshold=0.75,
        min_speech_duration_ms=300,
        min_silence_duration_ms=300
    )

    print("Speech segments:")
    for i, seg in enumerate(speech_timestamps):
        start_sample = seg['start']
        end_sample = seg['end']
        print(f"{i+1:02d}: {start_sample/sr:.2f}s → {end_sample/sr:.2f}s")

        # Lấy audio segment
        segment_audio = wav[start_sample:end_sample].numpy()
        out_path = os.path.join(out_dir, f"seg_{i+1:02d}_{start_sample/sr:.2f}_{end_sample/sr:.2f}.wav")
        sf.write(out_path, segment_audio, sr)
        print(f"Saved segment audio: {out_path}")

if __name__ == "__main__":
    run_vad_and_save_segments("out.wav")
