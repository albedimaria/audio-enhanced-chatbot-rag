import os
import requests
import time
import json
from pathlib import Path
import yt_dlp
import logging
import streamlit as st
from language_config import LANGUAGE_NAME_MAP

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
        os.makedirs('temp', exist_ok=True)

        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',  # bitrate 192 kbps
            }],
            'outtmpl': 'temp/%(id)s.%(ext)s',
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



# Modify the assemblyai_stt function to return both text and word-level timestamps
def assemblyai_stt(audio_filename, DEBUG_MODE=False):
    if DEBUG_MODE:
        return None, None

    try:
        audio_path = os.path.join('temp', audio_filename)
        if not os.path.exists(audio_path):
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

        # show the available language if possible
        detected_lang = transcription_result.get('language_code', 'und')
        detected_name = LANGUAGE_NAME_MAP.get(detected_lang, detected_lang)
        st.sidebar.info(f"Language detected: `{detected_name}`")

        os.makedirs('docs', exist_ok=True)
        with open('docs/transcription.txt', 'w') as file:
            file.write(transcription_text)
        with open('docs/word_timestamps.json', 'w') as file:
            json.dump(word_timestamps, file)

        logger.info("Successfully transcribed audio with word-level timestamps")
        return transcription_text, word_timestamps
    except Exception as e:
        logger.error(f"Error in speech-to-text conversion: {str(e)}")
        st.error(f"Error in speech-to-text conversion: {str(e)}")
        return None, None

# Cleanup temporary files
def cleanup_temp_files():
    for file in os.listdir('temp'):
        os.remove(os.path.join('temp', file))