# Finanzas-IA — Agente financiero con memoria (LangChain + Gemini + LangSmith)

Agente IA para **Finanzas Inteligentes SAC** que analiza reportes financieros
mensuales de sucursales (Lima, Arequipa, Cusco) y genera resúmenes ejecutivos
automáticamente, recordando los meses anteriores para hacer comparaciones.

## Estructura

```
├── docs/arquitectura.md      # Diseño de la arquitectura (actividad 1)
├── src/
│   ├── config.py             # .env + construcción del LLM Gemini
│   ├── memoria.py            # Memoria de corto y largo plazo (actividad 2)
│   ├── prompts.py            # Prompts especializados (actividad 3)
│   ├── agente.py             # Agente: extracción + resumen
│   └── evaluacion.py         # Evaluación: checks exactos + LLM-juez (actividad 6)
├── data/reportes/            # 3 reportes mensuales (actividad 4)
├── resumenes/                # Salida: resúmenes ejecutivos + evaluación (actividad 5)
├── memoria/                  # Memoria persistente del agente (JSON, se autogenera)
└── main.py                   # Orquestador
```

## Configuración

1. Activar el entorno virtual (ya creado):
   ```fish
   source .venv/bin/activate.fish
   ```
   (si usas bash: `source .venv/bin/activate`)

2. Editar `.env` y pegar tus claves:
   - `GOOGLE_API_KEY` — gratis en https://aistudio.google.com/apikey
   - `LANGSMITH_API_KEY` — en https://smith.langchain.com → Settings → API Keys

## Ejecución

```fish
.venv/bin/python main.py
```

Procesa los 3 reportes en orden cronológico. Por cada uno:
1. Extrae métricas clave (JSON) y las guarda en la memoria de largo plazo
2. Genera el resumen ejecutivo usando la memoria de los meses previos
3. Lo evalúa (¿cifras fieles? + rúbrica 1-5 con LLM-como-juez)

Salidas en `resumenes/`: `resumen_2026-01_enero.md`, `..._febrero.md`,
`..._marzo.md` y `evaluacion.md`.

## Observabilidad (LangSmith)

Con `LANGSMITH_TRACING=true`, cada cadena (`extraccion_metricas`,
`resumen_ejecutivo`, `juez_evaluador`) queda trazada en
https://smith.langchain.com bajo el proyecto **finanzas-ia**: prompts
completos, tokens, latencia y errores.

## Cómo funciona la memoria

- **Corto plazo:** `RunnableWithMessageHistory` inyecta el historial de la
  conversación en cada resumen, así el agente "recuerda" lo que redactó antes.
- **Largo plazo:** tras cada análisis, las métricas del mes se persisten en
  `memoria/memoria_financiera.json` y se inyectan en el prompt de los meses
  siguientes → el agente compara "marzo vs febrero" con cifras reales aunque
  se reinicie el proceso.
