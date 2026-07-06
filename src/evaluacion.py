"""Evaluación de los resúmenes generados.

Dos métodos complementarios:
1. Check exacto: ¿las cifras clave del mes aparecen en el resumen?
2. LLM-como-juez: rúbrica de 4 criterios (1-5) calificada por Gemini.
"""
import json
import re

from langchain_core.output_parsers import StrOutputParser

from .config import crear_llm
from .prompts import PROMPT_JUEZ


def _formatos(numero: float) -> list[str]:
    """Variantes con las que una cifra puede aparecer escrita en el resumen."""
    entero = int(numero)
    variantes = [f"{entero:,}", str(entero)]
    if entero >= 1000:
        variantes.append(f"{entero / 1000:g} mil")
    if numero != entero:
        variantes.append(f"{numero:g}")
    return variantes


def verificar_cifras(resumen: str, metricas: dict) -> dict:
    """Comprueba presencia de las cifras clave del mes en el texto del resumen."""
    claves = {
        "ingresos_totales": metricas["ingresos_totales"],
        "utilidad_operativa": metricas["utilidad_operativa"],
        "margen_pct": metricas["margen_pct"],
        "mora_pct": metricas["mora_pct"],
    }
    resultado = {}
    for nombre, valor in claves.items():
        resultado[nombre] = any(v in resumen for v in _formatos(valor))
    resultado["puntaje"] = round(
        100 * sum(v for k, v in resultado.items() if k != "puntaje") / len(claves)
    )
    return resultado


class Evaluador:
    def __init__(self):
        # Temperatura 0: el juez debe ser determinista.
        llm = crear_llm(temperatura=0.0)
        self.cadena_juez = (PROMPT_JUEZ | llm | StrOutputParser()).with_config(
            run_name="juez_evaluador"
        )

    def calificar(self, reporte: str, memoria: str, resumen: str) -> dict:
        salida = self.cadena_juez.invoke(
            {"reporte": reporte, "memoria": memoria, "resumen": resumen}
        )
        match = re.search(r"\{.*\}", salida, re.DOTALL)
        return json.loads(match.group(0)) if match else {"error": salida[:200]}
