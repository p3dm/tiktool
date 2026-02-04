import requests, base64, json

API_KEY = "AIzaSyDZKjNnRKeZ3Qh0jPAByvzUt28BtQzaMNE"
url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

headers = {
    "x-goog-api-key": API_KEY,
    "Content-Type": "application/json"
}

# Encode audio file thành base64
with open("a.wav", "rb") as f:
    audio_b64 = base64.b64encode(f.read()).decode("utf-8")

payload = {
    "contents": [
        {
            "parts": [
                {
                    "inlineData": {
                        "mimeType": "audio/wav",
                        "data": audio_b64
                    }
                },
                {
                    "text": "Transcribe the audio in its original language with and also provide an English translation."
                }
            ]
        }
    ],
    "generation_config": {
        "response_mime_type": "application/json",
        "response_schema": {
            "type": "OBJECT",
            "properties": {
                "original_text": {
                    "type": "STRING",
                    "description": "Transcript in the original language of the audio"
                },
                "english_translation": {
                    "type": "STRING",
                    "description": "Translation of the transcript into English"
                }
            },
            "required": ["original_text", "english_translation"]
        }
    }
}

resp = requests.post(url, headers=headers, json=payload).json()

text_json = resp['candidates'][0]['content']['parts'][0]['text'] # Parse chuỗi JSON thành dict
data = json.loads(text_json)
original = data['original_text']
translation = data['english_translation']
print("Original:", original)
print("English:", translation)