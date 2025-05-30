# qa_utils.py

import json
from langchain.document_loaders import TextLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA, LLMChain
from langchain.prompts import PromptTemplate
import streamlit as st

from language_config import ENG, ESP, ITA

class DummyChain:
    def __init__(self, language):
        self.language = language

    def __call__(self, input_dict):
        return {"result": {
            ENG: "This is a dummy answer.",
            ESP: "Esta es una respuesta simulada.",
            ITA: "Questa è una risposta simulata."
        }[self.language]}


# Modify the setup_qa_chain function to include word timestamps
@st.cache_resource
def setup_qa_chain(language, DEBUG_MODE=False):
    if DEBUG_MODE:
        # mock function empty dictionary
        return DummyChain(language), []

    try:
        loader = TextLoader('docs/transcription.txt')
        documents = loader.load()

        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        texts = text_splitter.split_documents(documents)

        embeddings = OpenAIEmbeddings()
        vectorstore = FAISS.from_documents(texts, embeddings)

        retriever = vectorstore.as_retriever()

        chat = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)

        qa_chain = RetrievalQA.from_chain_type(
            llm=chat,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True
        )

        with open('docs/word_timestamps.json', 'r') as file:
            word_timestamps = json.load(file)

        return qa_chain, word_timestamps

    except Exception as e:
        st.error(f"Error setting up QA chain: {str(e)}")
        return None, None


# Function to find relevant timestamps
def find_relevant_timestamps(answer, word_timestamps):
    relevant_timestamps = []
    answer_words = answer.lower().split()
    for word_info in word_timestamps:
        if word_info['text'].lower() in answer_words:
            relevant_timestamps.append(word_info['start'])
    return relevant_timestamps


# Function to generate summary
def generate_summary(transcription, language, DEBUG_MODE=False):
    if DEBUG_MODE:
        return {
            ENG: "This is a simulated summary.",
            ESP: "Este es un resumen simulado.",
            ITA: "Questo è un riassunto simulato."
        }[language]

    chat = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.7)
    template = (
        "Resume la siguiente transcripción en 3-5 frases:\n\n{transcription}"
        if language == ESP else
        "Riassumi la seguente trascrizione in 3-5 frasi:\n\n{transcription}"
        if language == ITA else
        "Summarize the following transcription in 3-5 sentences:\n\n{transcription}"
    )
    summary_prompt = PromptTemplate(
        input_variables=["transcription"],
        template=template
    )
    summary_chain = LLMChain(llm=chat, prompt=summary_prompt)
    return summary_chain.run(transcription)

