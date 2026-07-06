"""Agente financiero: extrae métricas, alimenta la memoria y genera resúmenes."""
import json
import re

from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables.history import RunnableWithMessageHistory

from .config import crear_llm
from .memoria import MemoriaFinanciera, obtener_historial
from .prompts import PROMPT_EXTRACCION, PROMPT_RESUMEN


def _extraer_json(texto: str) -> dict:
    """El LLM a veces envuelve el JSON en ```json ...```; lo limpia y parsea."""
    match = re.search(r"\{.*\}", texto, re.DOTALL)
    if not match:
        raise ValueError(f"El modelo no devolvió JSON: {texto[:200]}")
    return json.loads(match.group(0))


class AgenteFinanciero:
    def __init__(self, session_id: str = "finanzas-inteligentes"):
        self.llm = crear_llm()
        self.memoria = MemoriaFinanciera()
        self.session_id = session_id

        self.cadena_extraccion = (
            PROMPT_EXTRACCION | self.llm | StrOutputParser()
        ).with_config(run_name="extraccion_metricas")

        # El resumen usa memoria de corto plazo: el historial de la sesión se
        # inyecta automáticamente en el MessagesPlaceholder("historial").
        self.cadena_resumen = RunnableWithMessageHistory(
            (PROMPT_RESUMEN | self.llm | StrOutputParser()).with_config(
                run_name="resumen_ejecutivo"
            ),
            obtener_historial,
            input_messages_key="reporte",
            history_messages_key="historial",
        )

    def analizar_reporte(self, texto_reporte: str) -> dict:
        """Extrae métricas del reporte y las guarda en la memoria de largo plazo."""
        salida = self.cadena_extraccion.invoke({"reporte": texto_reporte})
        metricas = _extraer_json(salida)
        self.memoria.recordar(metricas)
        return metricas

    def generar_resumen(self, texto_reporte: str, metricas_mes: dict) -> str:
        """Genera el resumen ejecutivo usando ambos niveles de memoria.

        La memoria de largo plazo excluye el mes actual para que la sección de
        comparación se base solo en meses anteriores.
        """
        memoria_previa = MemoriaFinanciera()
        memoria_previa.meses = [
            m for m in self.memoria.meses if m.get("mes") != metricas_mes.get("mes")
        ]
        return self.cadena_resumen.invoke(
            {"reporte": texto_reporte, "memoria": memoria_previa.contexto()},
            config={"configurable": {"session_id": self.session_id}},
        )

    def procesar(self, texto_reporte: str) -> tuple[dict, str]:
        """Flujo completo para un reporte: analizar → memorizar → resumir."""
        metricas = self.analizar_reporte(texto_reporte)
        resumen = self.generar_resumen(texto_reporte, metricas)
        return metricas, resumen
