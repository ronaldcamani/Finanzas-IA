"""Orquestador: analiza los 3 reportes mensuales, genera resúmenes ejecutivos
y los evalúa. Cada llamada al LLM queda trazada en LangSmith (proyecto
'finanzas-ia') si LANGSMITH_TRACING=true en .env.
"""
import time

from src.agente import AgenteFinanciero
from src.config import DIR_REPORTES, DIR_RESUMENES
from src.evaluacion import Evaluador, verificar_cifras
from src.memoria import MemoriaFinanciera


def main() -> None:
    DIR_RESUMENES.mkdir(exist_ok=True)

    # Memoria limpia para que la corrida sea reproducible de inicio a fin.
    MemoriaFinanciera().limpiar()

    agente = AgenteFinanciero()
    evaluador = Evaluador()
    reportes = sorted(DIR_REPORTES.glob("*.txt"))  # orden cronológico por nombre
    resultados = []

    for ruta in reportes:
        print(f"\n{'=' * 60}\nProcesando: {ruta.name}")
        texto = ruta.read_text(encoding="utf-8")

        # Contexto de meses previos ANTES de memorizar el mes actual (el juez
        # evaluará la comparación contra esto).
        memoria_previa = agente.memoria.contexto()

        metricas, resumen = agente.procesar(texto)
        print(f"  Métricas extraídas: ingresos S/ {metricas['ingresos_totales']:,}, "
              f"utilidad S/ {metricas['utilidad_operativa']:,}")

        salida = DIR_RESUMENES / f"resumen_{ruta.stem}.md"
        salida.write_text(resumen, encoding="utf-8")
        print(f"  Resumen guardado en: {salida.relative_to(salida.parent.parent)}")

        print("  Evaluando...")
        cifras = verificar_cifras(resumen, metricas)
        rubrica = evaluador.calificar(texto, memoria_previa, resumen)
        resultados.append((ruta.stem, metricas, cifras, rubrica))
        print(f"  Cifras correctas: {cifras['puntaje']}% | Rúbrica LLM: {rubrica}")
        time.sleep(15)  # respeta el límite por minuto del nivel gratuito de Gemini

    # ── Informe de evaluación consolidado ────────────────────────────────────
    lineas = ["# Evaluación de resúmenes ejecutivos\n"]
    lineas.append("| Mes | Cifras presentes | Fidelidad | Completitud | Uso de memoria | Accionabilidad |")
    lineas.append("|---|---|---|---|---|---|")
    for nombre, _, cifras, rub in resultados:
        lineas.append(
            f"| {nombre} | {cifras['puntaje']}% | {rub.get('fidelidad', '-')}/5 "
            f"| {rub.get('completitud', '-')}/5 | {rub.get('uso_de_memoria', '-')}/5 "
            f"| {rub.get('accionabilidad', '-')}/5 |"
        )
    lineas.append("\n## Comentarios del juez\n")
    for nombre, _, _, rub in resultados:
        lineas.append(f"- **{nombre}**: {rub.get('comentario', rub)}")
    informe = DIR_RESUMENES / "evaluacion.md"
    informe.write_text("\n".join(lineas), encoding="utf-8")
    print(f"\n{'=' * 60}\nInforme de evaluación: {informe}")
    print("Revisa las trazas en https://smith.langchain.com (proyecto 'finanzas-ia')")


if __name__ == "__main__":
    main()
