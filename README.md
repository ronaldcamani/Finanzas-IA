# Finanzas-IA — Agente financiero con memoria (LangChain + Gemini + LangSmith)

Agente IA para **Finanzas Inteligentes SAC** que analiza reportes financieros
mensuales de sucursales (Lima, Arequipa, Cusco) y genera resúmenes ejecutivos
automáticamente, recordando los meses anteriores para hacer comparaciones.

## Estructura

```
├── docs/arquitectura.md      # Diseño de la arquitectura
├── src/
│   ├── config.py             # .env + construcción del LLM Gemini
│   ├── memoria.py            # Memoria de corto y largo plazo
│   ├── prompts.py            # Prompts especializados
│   ├── agente.py             # Agente: extracción + resumen
│   └── evaluacion.py         # Evaluación: checks exactos + LLM-juez
├── data/reportes/            # 3 reportes mensuales
├── resumenes/                # Salida: resúmenes ejecutivos + evaluación
├── memoria/                  # Memoria persistente del agente (JSON, se autogenera)
└── main.py                   # Orquestador
```

## Configuración

1. Crear el entorno virtual e instalar dependencias:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Copiar la plantilla de variables de entorno y completar tus claves:

   ```bash
   cp .env.example .env
   ```

   - `GOOGLE_API_KEY` — gratis en <https://aistudio.google.com/apikey>
   - `LANGSMITH_API_KEY` — en <https://smith.langchain.com> → Settings → API Keys

## Ejecución

```bash
python main.py
```

Procesa los 3 reportes en orden cronológico. Por cada uno:

1. Extrae métricas clave (JSON) y las guarda en la memoria de largo plazo
2. Genera el resumen ejecutivo usando la memoria de los meses previos
3. Lo evalúa (¿cifras fieles? + rúbrica 1-5 con LLM-como-juez)

Salidas en `resumenes/`: `resumen_2026-01_enero.md`, `..._febrero.md`,
`..._marzo.md` y `evaluacion.md`.

## Ejemplo de resultado

Fragmento de [`resumenes/resumen_2026-03_marzo.md`](resumenes/resumen_2026-03_marzo.md).
La sección de comparación sale de la memoria de largo plazo (las cifras de
febrero no aparecen en el reporte de marzo):

> ### Resultados del mes
>
> En marzo de 2026, Finanzas Inteligentes SAC alcanzó **ingresos totales de S/ 958,000** y **gastos operativos de S/ 554,000**, resultando en una **utilidad operativa de S/ 404,000**. El margen operativo mejoró significativamente a **42.2%**.
>
> ### Comparación con meses anteriores
>
> Los ingresos totales aumentaron un **3.91%** respecto a febrero (S/ 921,000). Los gastos operativos disminuyeron un **2.64%** (S/ 569,000), destacando la reducción en provisiones por incobrables. La utilidad operativa se disparó un **14.77%**. La mora > 30 días se redujo notablemente en 0.7 pp, situándose en 3.9%, gracias al nuevo modelo de scoring. El número de clientes nuevos se incrementó en un **14.91%**.
>
> ### Recomendaciones
>
> 1. **Lanzar y monitorear la campaña "Crédito Escolar" en Lima**: Asegurar una ejecución efectiva para compensar la caída de ingresos y mantener el dinamismo.
> 2. **Consolidar la mejora en Arequipa y Cusco**: Implementar estrategias para mantener la tendencia positiva en colocación y captación de clientes en ambas sucursales.
> 3. **Analizar la reducción de provisiones**: Evaluar si la disminución en provisiones por incobrables se debe a una mejora estructural en la calidad de la cartera o a factores temporales.

Evaluación automática ([`resumenes/evaluacion.md`](resumenes/evaluacion.md)):

| Mes | Cifras presentes | Fidelidad | Completitud | Uso de memoria | Accionabilidad |
|---|---|---|---|---|---|
| 2026-01_enero | 100% | 5/5 | 5/5 | 5/5 | 5/5 |
| 2026-02_febrero | 100% | 5/5 | 5/5 | 5/5 | 5/5 |
| 2026-03_marzo | 100% | 5/5 | 5/5 | 5/5 | 5/5 |

## Observabilidad (LangSmith)

Con `LANGSMITH_TRACING=true`, cada cadena (`extraccion_metricas`,
`resumen_ejecutivo`, `juez_evaluador`) queda trazada en
<https://smith.langchain.com> bajo el proyecto **finanzas-ia**: prompts
completos, tokens, latencia y errores.

## Cómo funciona la memoria

- **Corto plazo:** `RunnableWithMessageHistory` inyecta el historial de la
  conversación en cada resumen, así el agente "recuerda" lo que redactó antes.
- **Largo plazo:** tras cada análisis, las métricas del mes se persisten en
  `memoria/memoria_financiera.json` y se inyectan en el prompt de los meses
  siguientes → el agente compara "marzo vs febrero" con cifras reales aunque
  se reinicie el proceso.
