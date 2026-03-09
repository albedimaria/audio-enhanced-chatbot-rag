import os
import logging
import streamlit as st
from dotenv import load_dotenv

from language_config import ENG, ESP, ITA, UI_TEXTS
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
api_token = os.getenv("ASSEMBLY_AI_KEY")
openai_key = os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_API_KEY"] = openai_key or ""

# Modify the main Streamlit app
st.set_page_config(layout="wide", page_title="ChatAudio", page_icon="🔊")
if DEBUG_MODE:
    st.sidebar.warning("Debug Mode Active - No API costs")
elif not api_token or not openai_key:
    st.sidebar.error(
        "Missing API keys. Set ASSEMBLY_AI_KEY and OPENAI_API_KEY in .env for transcription and QA."
    )


language = st.sidebar.selectbox("Language", [ENG, ESP, ITA])
ui_texts = UI_TEXTS[language]
input_label = ui_texts["input_label"]
question_label = ui_texts["question_label"]
summary_button = ui_texts["summary_button"]
title = ui_texts["title"]



st.title(title)

input_source = st.text_input(input_label)

if input_source:
    qa_chain = None
    word_timestamps = None

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

                # Set up the QA chain (real RAG when not debug, dummy otherwise)
                if DEBUG_MODE:
                    qa_chain = DummyChain(language)
                else:
                    qa_chain, word_timestamps = setup_qa_chain(language, DEBUG_MODE)
                    if qa_chain is None:
                        st.error("Failed to set up QA system. Check docs/ and API keys.")

                # Add summary generation option
                if st.button(summary_button):
                    with st.spinner("Generating summary..."):
                        summary = generate_summary(transcription, language, DEBUG_MODE)
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
                    
                    # Find and display relevant timestamps (AssemblyAI returns milliseconds)
                    if word_timestamps:
                        relevant_timestamps = find_relevant_timestamps(answer, word_timestamps)
                    else:
                        relevant_timestamps = []
                    if relevant_timestamps:
                        st.subheader(ui_texts["timestamps"])
                        for timestamp_ms in relevant_timestamps[:5]:  # Limit to top 5 timestamps
                            seconds = timestamp_ms // 1000
                            st.write(f"{seconds // 60}:{seconds % 60:02d}")
            else:
                st.error("QA system is not ready. Please make sure the transcription is completed.")


