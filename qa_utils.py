# qa_utils.py

import json
import streamlit as st
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA, LLMChain
try:
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings
except ImportError:
    from langchain.chat_models import ChatOpenAI
    from langchain.embeddings import OpenAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain.text_splitter import CharacterTextSplitter

from config import DOCS_DIR
from language_config import ENG, ESP, ITA

# Common stopwords to skip when matching answer words to timestamps (reduces noise)
_STOPWORDS = frozenset({
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "must", "shall", "can", "need", "dare",
    "to", "of", "in", "for", "on", "with", "at", "by", "from", "as",
    "into", "through", "during", "before", "after", "above", "below",
})

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
        return DummyChain(language), []

    try:
        transcription_path = DOCS_DIR / "transcription.txt"
        loader = TextLoader(str(transcription_path))
        documents = loader.load()

        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
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

        with open(DOCS_DIR / "word_timestamps.json", "r", encoding="utf-8") as f:
            word_timestamps = json.load(f)

        return qa_chain, word_timestamps

    except Exception as e:
        st.error(f"Error setting up QA chain: {str(e)}")
        return None, None


# Function to find relevant timestamps (skips stopwords to reduce noise)
def find_relevant_timestamps(answer, word_timestamps):
    if not word_timestamps:
        return []
    answer_words = {w.strip(".,;:?!").lower() for w in answer.split()}
    answer_words -= _STOPWORDS
    if not answer_words:
        return []
    relevant_timestamps = []
    for word_info in word_timestamps:
        word = word_info.get("text", "").strip(".,;:?!").lower()
        if word and word in answer_words:
            relevant_timestamps.append(word_info["start"])
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

