"""Sistema de memoria del agente: dos niveles.

1. Corto plazo  → historial de conversación en RAM (InMemoryChatMessageHistory),
                  inyectado en cada llamada vía RunnableWithMessageHistory.
2. Largo plazo  → métricas estructuradas por mes, persistidas en JSON, que
                  sobreviven reinicios y permiten comparaciones mes a mes.
"""
import json
from pathlib import Path

from langchain_core.chat_history import InMemoryChatMessageHistory

from .config import DIR_MEMORIA

# ── Memoria de corto plazo (conversacional) ──────────────────────────────────
_sesiones: dict[str, InMemoryChatMessageHistory] = {}


def obtener_historial(session_id: str) -> InMemoryChatMessageHistory:
    """Devuelve (o crea) el historial de chat de una sesión."""
    if session_id not in _sesiones:
        _sesiones[session_id] = InMemoryChatMessageHistory()
    return _sesiones[session_id]


# ── Memoria de largo plazo (estructurada y persistente) ──────────────────────
class MemoriaFinanciera:
    """Guarda las métricas clave de cada mes analizado en un JSON persistente."""

    def __init__(self, ruta: Path | None = None):
        self.ruta = ruta or (DIR_MEMORIA / "memoria_financiera.json")
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        self.meses: list[dict] = []
        if self.ruta.exists():
            self.meses = json.loads(self.ruta.read_text(encoding="utf-8"))

    def recordar(self, metricas: dict) -> None:
        """Añade (o reemplaza) las métricas de un mes y persiste a disco."""
        self.meses = [m for m in self.meses if m.get("mes") != metricas.get("mes")]
        self.meses.append(metricas)
        self.ruta.write_text(
            json.dumps(self.meses, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def contexto(self) -> str:
        """Texto con la memoria acumulada, listo para inyectar en un prompt."""
        if not self.meses:
            return "(sin meses anteriores: este es el primer reporte analizado)"
        lineas = []
        for m in self.meses:
            por_sucursal = ", ".join(
                f"{s} S/ {v:,}" for s, v in m.get("ingresos_por_sucursal", {}).items()
            )
            lineas.append(
                f"- {m['mes']}: ingresos S/ {m['ingresos_totales']:,} "
                f"({por_sucursal}), "
                f"gastos S/ {m['gastos_totales']:,}, "
                f"utilidad S/ {m['utilidad_operativa']:,} "
                f"(margen {m['margen_pct']}%), mora {m['mora_pct']}%, "
                f"{m['clientes_nuevos']} clientes nuevos. "
                f"Mejor sucursal: {m['mejor_sucursal']}. "
                f"Alertas: {'; '.join(m['alertas'])}"
            )
        return "\n".join(lineas)

    def limpiar(self) -> None:
        self.meses = []
        if self.ruta.exists():
            self.ruta.unlink()
