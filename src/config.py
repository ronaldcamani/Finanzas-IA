"""Configuración central: carga .env y construye el LLM."""
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

RAIZ = Path(__file__).resolve().parent.parent
DIR_REPORTES = RAIZ / "data" / "reportes"
DIR_RESUMENES = RAIZ / "resumenes"
DIR_MEMORIA = RAIZ / "memoria"

load_dotenv(RAIZ / ".env")

MODELO = os.getenv("MODELO_GEMINI", "gemini-2.5-flash")


def crear_llm(temperatura: float = 0.2) -> ChatGoogleGenerativeAI:
    """LLM Gemini. Temperatura baja: el análisis financiero debe ser fiel a las cifras."""
    if not os.getenv("GOOGLE_API_KEY"):
        raise RuntimeError(
            "Falta GOOGLE_API_KEY en el archivo .env "
            "(obtenla gratis en https://aistudio.google.com/apikey)"
        )
    return ChatGoogleGenerativeAI(model=MODELO, temperature=temperatura)
