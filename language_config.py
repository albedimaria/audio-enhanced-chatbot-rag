# language_config.py

ENG = "English"
ESP = "Español"
ITA = "Italiano"

# AssemblyAI returns codes like "en", "en_us", "en_uk"; map base codes to display names
LANGUAGE_NAME_MAP = {
    "en": ENG,
    "es": ESP,
    "it": ITA,
}


def get_language_display_name(language_code: str) -> str:
    """Resolve AssemblyAI language_code to display name (e.g. en_us -> English)."""
    if not language_code or language_code == "und":
        return language_code or "und"
    # Exact match first
    if language_code in LANGUAGE_NAME_MAP:
        return LANGUAGE_NAME_MAP[language_code]
    # Fallback: base code (en_us -> en)
    base = language_code.split("_")[0].lower()
    return LANGUAGE_NAME_MAP.get(base, language_code)

UI_TEXTS = {
    ENG: {
        "input_label": "Enter the YouTube video URL",
        "question_label": "Ask your question here...",
        "summary_button": "Generate Summary",
        "title": "Chat with Your Audio using LLM",
        "uploaded_video": "Your uploaded video",
        "transcription_done": "Transcription completed. You can now ask questions.",
        "transcription": "Transcription",
        "chat_below": "Chat Below",
        "summary": "Summary",
        "timestamps": "Relevant Timestamps"
    },
    ESP: {
        "input_label": "Introduce la URL del video de YouTube",
        "question_label": "Haz tu pregunta aquí...",
        "summary_button": "Generar Resumen",
        "title": "Chatea con tu audio usando LLM",
        "uploaded_video": "Tu video cargado",
        "transcription_done": "Transcripción completada. Ahora puedes hacer preguntas.",
        "transcription": "Transcripción",
        "chat_below": "Chat aquí abajo",
        "summary": "Resumen",
        "timestamps": "Tiempos relevantes"
    },
    ITA: {
        "input_label": "Inserisci l'URL del video YouTube",
        "question_label": "Fai la tua domanda qui...",
        "summary_button": "Genera Riassunto",
        "title": "Chatta con il tuo audio usando LLM",
        "uploaded_video": "Il tuo video caricato",
        "transcription_done": "Trascrizione completata. Ora puoi fare domande.",
        "transcription": "Trascrizione",
        "chat_below": "Chat qui sotto",
        "summary": "Riassunto",
        "timestamps": "Timestamp rilevanti"
    }
}
