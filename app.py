import streamlit as st
import json
import os
import time
from dotenv import load_dotenv
import requests
import yt_dlp # yt downloader
from pathlib import Path

from langchain.document_loaders import TextLoader
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA, LLMChain
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.prompts import PromptTemplate
import logging

from language_config import ENG, ESP, ITA, UI_TEXTS, LANGUAGE_NAME_MAP
from stt_utils import save_audio, assemblyai_stt, cleanup_temp_files
from qa_utils import DummyChain, setup_qa_chain, generate_summary, find_relevant_timestamps

QUERY_KEY = "query"
RESULT_KEY = "result"

# debug
DEBUG_MODE = True


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
api_token = os.getenv('ASSEMBLY_AI_KEY')
os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')


base_url = "https://api.assemblyai.com/v2"

headers = {
    "authorization": api_token,
    "content-type": "application/json"
}


# Modify the main Streamlit app

st.set_page_config(layout="wide", page_title="ChatAudio", page_icon="🔊")
if DEBUG_MODE:
    st.sidebar.warning("Debug Mode Active - No API costs")


language = st.sidebar.selectbox("Language", [ENG, ESP, ITA])
ui_texts = UI_TEXTS[language]
input_label = ui_texts["input_label"]
question_label = ui_texts["question_label"]
summary_button = ui_texts["summary_button"]
title = ui_texts["title"]



st.title(title)

input_source = st.text_input(input_label)

if input_source:
    col1, col2 = st.columns(2)

    with col1:
        st.info(ui_texts["uploaded_video"])
        st.video(input_source)
        audio_filename = save_audio(input_source)
        if audio_filename:
            transcription, word_timestamps = assemblyai_stt(audio_filename, DEBUG_MODE)
            if transcription:
                st.info(ui_texts["transcription_done"])
                st.text_area(ui_texts["transcription"], transcription, height=300)

                # Set up the QA chain
                if not DEBUG_MODE:
                    qa_chain, word_timestamps = DummyChain(language), word_timestamps
                else:
                    qa_chain = DummyChain(language)

                # Add summary generation option
                if st.button(summary_button):
                    with st.spinner("Generating summary..."):
                        summary = generate_summary(transcription, language)
                        st.subheader(ui_texts["summary"])
                        st.write(summary)

            else:
                if DEBUG_MODE:
                    st.warning("⚠️ DEBUG MODE ")
                else:
                    st.error("ERROR")

    with col2:
        st.info(ui_texts["chat_below"])
        query = st.text_input(question_label)
        if query:
            if qa_chain:
                with st.spinner("Generating answer..."):
                    result = qa_chain({QUERY_KEY: query})
                    answer = result[RESULT_KEY]
                    st.success(answer)
                    
                    # Find and display relevant timestamps
                    relevant_timestamps = find_relevant_timestamps(answer, word_timestamps)
                    if relevant_timestamps:
                        st.subheader(ui_texts["timestamps"])
                        for timestamp in relevant_timestamps[:5]:  # Limit to top 5 timestamps
                            st.write(f"{timestamp // 60}:{timestamp % 60:02d}")
            else:
                st.error("QA system is not ready. Please make sure the transcription is completed.")


