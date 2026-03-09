import os
import requests
import time
import json
from pathlib import Path
import yt_dlp
import logging
import streamlit as st

from config import TEMP_DIR, DOCS_DIR
from language_config import get_language_display_name

logger = logging.getLogger(__name__)
base_url = "https://api.assemblyai.com/v2"
headers = {
    "authorization": os.getenv("ASSEMBLY_AI_KEY"),
    "content-type": "application/json"
}


# yt-dlp function for YouTube video
def save_audio(url):
    try:
        # Create temp directory if it doesn't exist
        TEMP_DIR.mkdir(parents=True, exist_ok=True)
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',  # bitrate 192 kbps
            }],
            'outtmpl': str(TEMP_DIR / '%(id)s.%(ext)s'),
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            audio_filename = ydl.prepare_filename(info).replace('.webm', '.mp3')

        logger.info(f"Successfully downloaded audio: {audio_filename}")
        return Path(audio_filename).name
    except Exception as e:
        logger.error(f"Error downloading audio: {str(e)}")
        st.error(f"Error downloading audio: {str(e)}")
        return None



# Mock transcription and word timestamps for DEBUG_MODE (no API calls)
MOCK_TRANSCRIPTION = """This is a sample transcription for testing the app without API costs. 
The audio-enhanced chatbot allows users to ask questions about video and audio content. 
When you ask a question, the system provides a dummy answer. This demonstrates the full flow 
including transcription display, summary generation, and relevant timestamps."""

MOCK_WORD_TIMESTAMPS = [
    {"text": "This", "start": 0, "end": 300},
    {"text": "is", "start": 300, "end": 500},
    {"text": "a", "start": 500, "end": 600},
    {"text": "sample", "start": 600, "end": 1100},
    {"text": "transcription", "start": 1100, "end": 2100},
    {"text": "for", "start": 2100, "end": 2300},
    {"text": "testing", "start": 2300, "end": 3000},
    {"text": "the", "start": 3000, "end": 3200},
    {"text": "app", "start": 3200, "end": 3500},
    {"text": "without", "start": 3500, "end": 4100},
    {"text": "API", "start": 4100, "end": 4400},
    {"text": "costs.", "start": 4400, "end": 5000},
    {"text": "The", "start": 5000, "end": 5200},
    {"text": "audio-enhanced", "start": 5200, "end": 6500},
    {"text": "chatbot", "start": 6500, "end": 7200},
    {"text": "allows", "start": 7200, "end": 7800},
    {"text": "users", "start": 7800, "end": 8300},
    {"text": "to", "start": 8300, "end": 8500},
    {"text": "ask", "start": 8500, "end": 8900},
    {"text": "questions", "start": 8900, "end": 10100},
    {"text": "about", "start": 10100, "end": 10500},
    {"text": "video", "start": 10500, "end": 11200},
    {"text": "and", "start": 11200, "end": 11600},
    {"text": "audio", "start": 11600, "end": 12200},
    {"text": "content.", "start": 12200, "end": 13000},
    {"text": "When", "start": 13000, "end": 13500},
    {"text": "you", "start": 13500, "end": 13800},
    {"text": "ask", "start": 13800, "end": 14200},
    {"text": "a", "start": 14200, "end": 14300},
    {"text": "question,", "start": 14300, "end": 15300},
    {"text": "the", "start": 15300, "end": 15600},
    {"text": "system", "start": 15600, "end": 16300},
    {"text": "provides", "start": 16300, "end": 17200},
    {"text": "a", "start": 17200, "end": 17300},
    {"text": "dummy", "start": 17300, "end": 18100},
    {"text": "answer.", "start": 18100, "end": 18900},
]


# Modify the assemblyai_stt function to return both text and word-level timestamps
def assemblyai_stt(audio_filename, DEBUG_MODE=False):
    if DEBUG_MODE:
        st.sidebar.info("Using mock transcription (no API call)")
        cleanup_temp_files()
        return MOCK_TRANSCRIPTION, MOCK_WORD_TIMESTAMPS

    try:
        audio_path = TEMP_DIR / audio_filename
        if not audio_path.is_file():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        with open(audio_path, "rb") as f:
            response = requests.post(base_url + "/upload",
                                     headers=headers,
                                     data=f)
        response.raise_for_status()  # Raise an exception for bad status codes

        upload_url = response.json()["upload_url"]
        data = {
            "audio_url": upload_url,
        }
        url = base_url + "/transcript"
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()

        transcript_id = response.json()['id']
        polling_endpoint = f"https://api.assemblyai.com/v2/transcript/{transcript_id}"

        while True:
            transcription_result = requests.get(polling_endpoint, headers=headers).json()

            if transcription_result['status'] == 'completed':
                break
            elif transcription_result['status'] == 'error':
                raise RuntimeError(f"Transcription failed: {transcription_result['error']}")
            else:
                time.sleep(3)

        transcription_text = transcription_result['text']
        word_timestamps = transcription_result['words']

        # show the available language if possible (AssemblyAI may return en_us, en_uk, etc.)
        detected_lang = transcription_result.get('language_code', 'und')
        detected_name = get_language_display_name(detected_lang)
        st.sidebar.info(f"Language detected: `{detected_name}`")

        DOCS_DIR.mkdir(parents=True, exist_ok=True)
        (DOCS_DIR / "transcription.txt").write_text(transcription_text, encoding="utf-8")
        with open(DOCS_DIR / "word_timestamps.json", "w", encoding="utf-8") as f:
            json.dump(word_timestamps, f)

        logger.info("Successfully transcribed audio with word-level timestamps")
        cleanup_temp_files()
        return transcription_text, word_timestamps
    except Exception as e:
        logger.error(f"Error in speech-to-text conversion: {str(e)}")
        st.error(f"Error in speech-to-text conversion: {str(e)}")
        return None, None

# Cleanup temporary files (safe if temp/ does not exist)
def cleanup_temp_files():
    if not TEMP_DIR.is_dir():
        return
    for file in TEMP_DIR.iterdir():
        try:
            if file.is_file():
                file.unlink()
        except OSError as e:
            logger.warning(f"Could not remove {file}: {e}")