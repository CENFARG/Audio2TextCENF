# Audio2Text: Roadmap Maestro

Índice único de evolución de Audio2Text para **reuniones largas**, **subtitulado vivo**, **traducción simultánea**, **interlocutores**, **diarización** y **speech-to-speech**. Esta referencia consolida el estado estable, los aprendizajes y las decisiones de priorización sin convertir hipótesis en compromisos.

## Cómo convocarlo

Buscar o pedir: **Audio2Text roadmap maestro**, **reuniones largas**, **subtitulado vivo**, **traducción simultánea**, **interlocutores**, **diarización**, **speech-to-speech**.

La convocatoria debe recuperar este archivo antes de consultar informes secundarios. Las memorias Engram detalladas quedan como trazabilidad, no como roadmaps alternativos.

## Estado estable actual

| Elemento | Estado verificable |
|---|---|
| Baseline | Git `v.0.15.11`, commit `c5e8864`; proyecto `D:\CENF\gentle-ai\audio2text-v0150-groq-fix`. |
| Slice A | Hecho: timeout de 30 s, manejo de `413/429`, circuit breaker, progreso/ETA, checkpoint y logging. |
| Slice B | Hecho: pool de 3 workers para procesamiento post-stop y reconstrucción ordenada por índice. |
| Slice C | Hecho: snapshots cada 25 s, pool separado de 2 workers, `streaming_pending`, `streaming_ordered`, checkpoint `.partial_stream.txt`, evento de UI `En vivo Chunk cur/total`, espera y merge final de faltantes. |
| Resultado medido | En un test sintético con mock y audio de 720 s quedaron aproximadamente 1-2 chunks para el cierre; merge menor a 6 s. No es garantía de red, cuenta, cuota ni producción. |
| Límite explícito | Slice C es backend incremental de chunks y resultado final ordenado. **Todavía no es subtitulado vivo estable tipo YouTube ni un endpoint nativo de speech streaming.** |

## Problema original y aprendizaje

El síntoma original apareció en una grabación continua de unos 20 minutos: al presionar stop, Audio2Text recién comenzaba a partir, enviar y resolver todos los chunks. La espera crecía por acumulación de llamadas, latencias, reintentos y límites de tamaño; la interfaz no daba una señal útil durante ese trabajo.

La causa no era simplemente “Groq lento”. El problema era procesar después de grabar, sin timeout/retry suficientemente acotados, con llamadas secuenciales o limitadas, riesgo de `413/429`, poca observabilidad y sin un contrato que separara texto provisional de texto final. **Procesar después de grabar no es streaming**: el paralelismo post-stop reduce el cierre, pero no elimina la espera percibida.

Aprendizajes consolidados:

- La captura debe permanecer desacoplada de la API; el envío y las excepciones deben ejecutarse en background.
- Paralelizar exige conservar `idx` y unir por orden, nunca por orden de finalización.
- Un snapshot de 25 s es intervalo de trabajo, no una frase perfecta ni un subtítulo confirmado.
- Más workers no implica más throughput: puede aumentar presión de rate limit, contention y duplicación en bordes.
- Un parcial persistido no equivale a una sesión durable: para 5 h faltan rotación, journal de estados, resume tras caída y política de cuota.
- El vivo real necesita hipótesis reescribibles, prefijo committed, endpointing acústico/semántico, overlap, contrato de UI y métricas.

## Qué está hecho, qué se supone y qué falta

### Hecho

- Git `v.0.15.11` es el baseline estable documentado; el término correcto es **Git**, no “GIP”.
- Slices A, B y C están implementados según la tabla anterior.
- Slice C procesa snapshots durante la captura, conserva orden y reduce el trabajo post-stop en los casos cubiertos por tests.
- Groq es el proveedor actual de los Slices A/B/C mediante STT batch compatible con OpenAI; la documentación consultada no demuestra streaming STT nativo con interim events.
- La investigación SOTA, las fuentes oficiales y sus vacíos están registrados en Engram #2758.

### Hipótesis o recomendaciones

- Ventanas de 5-10 s pueden mejorar la percepción de vivo, pero deben medirse; no son garantía.
- Un pipeline `PCM -> jitter buffer -> VAD/hangover -> decoder/API -> endpointing -> estabilizador -> UI provisional/committed` es una dirección técnica plausible.
- LocalAgreement-2 o una regla equivalente puede estabilizar un prefijo a cambio de latencia; requiere benchmark propio.
- Metadata estructural de una plataforma puede atribuir interlocutores mejor que inferir speakers desde texto, cuando la API, permisos y consentimiento lo permiten.
- xAI puede evaluarse como alternativa para streaming STT, interim results y Smart Turn; no es el proveedor actual ni implica automáticamente subtitulado estable, traducción multilingüe o diarización.

### Pendiente

- Definir y medir el contrato provisional/committed/final/error.
- Medir latencia end-to-end P50/P95, frecuencia de actualización, revision/erasure rate, WER final y latencia de segmento.
- Verificar por cuenta los precios, rate limits, concurrencia, facturación mínima, región, permisos y disponibilidad.
- Validar captura de micrófono, WASAPI loopback, múltiples endpoints y sincronización en Windows.
- Diseñar persistencia durable de hasta 5 h con rotación, hash/índice, estados `pending/complete/failed`, checkpoint atómico, resume e idempotencia.
- Definir traducción español↔inglés contextual y sus límites de latencia, coherencia y costo.
- Obtener integración autorizada con Meet/Teams/Zoom y decidir qué metadata puede usarse.
- Evaluar diarización audio-only o audiovisual; los timestamps no son speaker labels.
- Mantener speech-to-speech/doblaje para el final, después de contar con transcripción, contexto, permisos y métricas estables.

## Roadmap único 1-10

Orden vigente: valor práctico de reuniones primero; complejidad y dependencias después. La dificultad es relativa y no representa horas ni presupuesto.

| # | Iniciativa y valor | Dificultad | Recursos requeridos | Dependencias | Criterio de entrada | Criterio de salida |
|---:|---|---|---|---|---|---|
| 1 | **Reuniones durables hasta 1 h.** Evita pérdida de trabajo y hace confiable la sesión continua. | Media | Persistencia local, rotación/checkpoint, tests de recuperación, métricas de sesión y control de errores del proveedor. | Slice A/B/C; contrato de índices y parciales. | El baseline conserva parciales, pero todavía no hay sesión durable con resume probado. | Una sesión de 1 h puede detenerse o recuperarse sin repetir chunks confirmados ni perder el orden; fallos y límites quedan observables. |
| 2 | **Reducir delay exploratorio a 5-10 s.** Acerca el producto a feedback útil durante la conversación. | Alta | VAD, hangover, endpointing, overlap, estabilizador, benchmark E2E y control de concurrencia. | Slice C; definición provisional/committed; elección o prueba de STT incremental. | Existe medición base y un proveedor/API con interim documentado, o se acepta un prototipo acotado. | P50/P95, revisión de texto y error final cumplen umbrales definidos en una prueba reproducible; no se declara garantía universal. |
| 3 | **Traducción español↔inglés contextual.** Agrega valor inmediato a reuniones bilingües sin saltar todavía a voz sintética. | Alta | ASR, traductor/LLM, memoria de contexto, glosario, nombres propios, identificador idempotente y métricas de latencia/calidad. | Texto committed de #2; estrategia de proveedor y presupuesto verificados. | Hay segmentos suficientemente estables y se conocen idioma, permisos, cuota y costo vigente de cada llamada. | Traducción incremental coherente en un piloto, con contexto acotado, reintentos idempotentes y latencia medida. |
| 4 | **Subtitulado visible vivo estable.** Convierte el backend incremental en una experiencia legible tipo captions, sin afirmar equivalencia con YouTube. | Alta | UI para provisional/committed/corregido/error, endpointing, deduplicación, overlap, accesibilidad y métricas de revisión. | #2; opcionalmente #3 para segunda línea traducida. | Existe un estabilizador probado y un contrato de estados; el evento `En vivo Chunk cur/total` ya no se trata como subtítulo. | El usuario ve hipótesis que pueden cambiar y un prefijo committed que no se reescribe; se reportan latencias y revision rate. |
| 5 | **Reuniones continuas hasta 5 h.** Escala duración sin depender de RAM ni de un único archivo. | Alta | Rotación de WAV, journal de sesión, checkpoints atómicos, resume, hash, backpressure, cuotas y presupuesto máximo por cuenta. | #1; idealmente #2 para utilidad en vivo; pruebas de crash y recuperación. | Una sesión de 1 h es durable y existen límites verificados del proveedor y del dispositivo. | Una prueba piloto de 5 h recupera desde el primer índice faltante, conserva orden, limita concurrencia y separa captura/STT/traducción/TTS/plataforma en sus métricas de costo. |
| 6 | **Captura de micrófono + audio del sistema.** Permite escuchar al usuario y al entorno de la reunión. | Media-Alta | Enumeración de endpoints, WASAPI input/loopback, buffers separados, selección de dispositivo, sincronización y controles de privacidad. | #1; validación Windows y consentimiento; no asumir Stereo Mix. | Se conoce el hardware objetivo y existe una política explícita para mic, loopback y cambios de dispositivo. | El sistema captura cada fuente elegida de forma reproducible, informa limitaciones de sincronización y no confunde loopback con cada aplicación individual. |
| 7 | **Meet/Teams con interlocutores.** Integra reuniones reales y metadata de participantes cuando esté permitido. | Alta | OAuth, permisos/scopes, consentimiento, controles tenant/proyecto, SDK/API de plataforma y almacenamiento seguro de metadata. | #4/#5/#6; captura y texto estable; aprobación de acceso por plataforma. | Se confirma elegibilidad: Meet Media API puede estar en Developer Preview, Teams Graph es principalmente post-meeting y Zoom RTMS requiere app/scopes/créditos. | Un piloto autorizado entrega audio/transcript y metadata de participantes con trazabilidad; no se presenta un artefacto post-meeting como streaming. Zoom queda como plus, no como dependencia del orden base. |
| 8 | **Agente apuntador/interventor: texto primero, voz después.** Sugiere preguntas, alertas o resúmenes durante la reunión. | Alta | Contexto committed, reglas de intervención, guardrails, UI de sugerencias, cancelación, logs y evaluación humana. | #2, #3/#4 y política de intervención; #7 si usa participantes. | La transcripción viva es suficientemente estable y se define cuándo el agente puede sugerir, nunca asumir que puede intervenir. | El agente produce sugerencias textuales trazables, no interrumpe sin autorización y demuestra utilidad/error en un piloto controlado. |
| 9 | **Diarización audio-only.** Atribuye turnos cuando no existe metadata confiable. | Muy alta | Segmentación, embeddings, detección de solapamiento, muestras de referencia, modelo/servicio especializado y evaluación DER. | #5/#6; audio separado o suficientemente limpio; política de identidad y privacidad. | Se define el número de speakers, corpus de prueba y métrica; no se confunden timestamps con speakers. | La atribución se reporta con confianza y DER/errores medidos; se explicita cuándo no puede identificar a una persona. |
| 10 | **Speech-to-speech/doblaje.** Experiencia de conversación o voz traducida de extremo a extremo. | Muy alta | API realtime de audio, STT/TTS o proveedor speech-to-speech, control de interrupción, latencia, seguridad, consentimiento y presupuesto. | Todos los fundamentos anteriores, especialmente #2/#3/#4 y medición E2E. | Hay caso de uso aprobado, costos y límites de cuenta verificados, y texto/contexto estable como fallback auditable. | Una demo/piloto mantiene turnos, cancelación y consentimiento, reporta latencia/costo/calidad y conserva una salida textual verificable. |

## Proveedores, costos y límites

**Groq y xAI son proveedores distintos.** Groq es la dependencia actual de los Slices A/B/C: STT batch Whisper, endpoints `/openai/v1/audio/transcriptions` y `/translations`, timestamps y límites de archivo. xAI ofrece una superficie separada de modelos, STT streaming/interim, TTS, Voice API y speech-to-speech realtime. No se deben mezclar nombres, credenciales, métricas, límites ni precios.

No asumir costos. El valor previo `$0.004/min` queda fuera de cualquier presupuesto porque no fue confirmado por una fuente oficial vigente. Tampoco “free tier” significa costo cero en producción. Para cada cuenta y modelo se debe verificar:

```text
costo estimado = minutos enviados x precio vigente del modelo/cuenta
                 + traducción/TTS si aplica
                 + créditos o servicios de plataforma
                 + margen por reintentos y solapamiento
```

La investigación encontró que Groq documenta STT batch y que su endpoint de traducción está orientado a inglés; `whisper-large-v3-turbo` no figura con traducción soportada en la documentación consultada. xAI no debe presumirse como solución multilingüe estable solo por ofrecer speech-to-speech.

## Windows, reuniones e interlocutores

- WASAPI loopback captura la mezcla del endpoint de render en shared mode; no es una captura universal de cada aplicación.
- Stereo Mix/What You Hear depende del driver y puede estar deshabilitado.
- Múltiples endpoints requieren buffers separados y no garantizan sincronización perfecta entre clocks.
- Meet Media API tiene requisitos de proyecto, OAuth, inscripción y estado Developer Preview; Meet REST transcripts no prueban parciales vivos.
- Teams Graph documenta principalmente transcript/recording post-meeting con permisos y controles del tenant.
- Zoom RTMS documenta audio, video, screen share y transcript en vivo con atribución por participante, pero requiere app, scopes y créditos; no es equivalente al Zoom Web/Meeting SDK.
- Metadata de participantes, cuando está autorizada, es preferible a inferir identidad vocal. Diarización audio-only y audiovisual son capacidades separadas.

## Relación con Planificador, Scheme y SEE

| Actor | Uso de este índice |
|---|---|
| **Planificador** | Toma el orden 1-10 como backlog estratégico, compara impacto/esfuerzo y decide qué iniciativa entra en el próximo ciclo. No convierte una hipótesis técnica en compromiso de implementación. |
| **Scheme** | Diseña el proceso y la arquitectura de la iniciativa elegida: contratos de estado, dependencias, límites humanos/IA, proveedores, seguridad, observabilidad y criterios de entrada/salida. |
| **SEE** | Evalúa viabilidad técnico-económica-tiempo y recursos disponibles antes de autorizar el salto de una etapa; reaudita con evidencia de piloto, métricas, costos y riesgos. |

Flujo recomendado: **Planificador prioriza -> Scheme diseña -> SEE evalúa -> implementación/piloto -> SEE reaudita -> Planificador actualiza este índice**. Este archivo es la referencia de coordinación, no reemplaza una especificación, diseño técnico ni evaluación SEE.

## Fuentes y trazabilidad

### Documentos del repositorio

- [Aprendizaje Audio2Text Streaming v0.15.11 (Markdown)](APRENDIZAJE_AUDIO2TEXT_STREAMING_v0.15.11_20260828.md)
- [Aprendizaje Audio2Text Streaming v0.15.11 (HTML)](APRENDIZAJE_AUDIO2TEXT_STREAMING_v0.15.11_20260828.html)
- [Auditoría v0.15.9: bloqueo exponencial de 20 min (Markdown)](AUDITORIA_v0.15.9_20min_bloqueo_exponencial_20260827.md) *(nombre y contenido preservados en Engram #2703; el archivo no está presente en este checkout)*
- [Auditoría v0.15.9: bloqueo exponencial de 20 min (HTML)](AUDITORIA_v0.15.9_20min_bloqueo_exponencial_20260827.html) *(referencia histórica; el archivo no está presente en este checkout)*

### Engram

- **#2771, maestro de evolución:** decisión de consolidar este índice y su orden vigente.
- **#2758, investigación SOTA:** streaming STT, VAD/endpointing, hipótesis, traducción, Windows, Meet/Teams/Zoom, diarización, Groq/xAI, costos y vacíos de evidencia.
- **#2760, aprendizaje:** documento dual sobre el problema de 20 min, Slices A/B/C, límites y próximos pasos.
- **#2763, iniciativa live/reuniones:** prioridad de subtitulado vivo 5-10 s y reuniones de hasta 5 h.
- **#2764, priorización:** valoración por impacto/dificultad y necesidad de medir antes de prometer.
- **#2770, orden revisado:** orden 1-10 de reuniones, traducción, subtitulado, fuentes, plataformas, agente, diarización y speech-to-speech.
- **#2703, auditoría v0.15.9:** raíz del incidente original: bloqueo post-stop, degradación, límites de 25 MB y falta de resiliencia.
- **#2754/#2755/#2756:** trazabilidad del release Git `v.0.15.11`, Slice C, orden preservado y mediciones sintéticas.

### Fuentes técnicas externas consolidadas

- [Groq Speech-to-Text](https://console.groq.com/docs/speech-to-text) y [Groq Text-to-Speech](https://console.groq.com/docs/text-to-speech)
- [xAI Models](https://docs.x.ai/developers/models), [Speech-to-Text](https://docs.x.ai/developers/models/speech-to-text), [Speech-to-Speech](https://docs.x.ai/developers/models/speech-to-speech) y [Pricing](https://docs.x.ai/developers/pricing)
- [Microsoft WASAPI loopback](https://learn.microsoft.com/en-us/windows/win32/coreaudio/loopback-recording)
- [Google Meet Media API](https://developers.google.com/workspace/meet/media-api/guides/overview) y [Meet transcripts REST](https://developers.google.com/workspace/meet/api/reference/rest/v2/conferenceRecords.transcripts)
- [Microsoft Teams transcripts](https://learn.microsoft.com/en-us/microsoftteams/platform/graph-api/meeting-transcripts/overview-transcripts)
- [Zoom RTMS](https://developers.zoom.us/docs/rtms/), [media](https://developers.zoom.us/docs/rtms/meetings/media/) y [getting started](https://developers.zoom.us/docs/rtms/meetings/getting-started/)
- [YouTube captions](https://support.google.com/youtube/answer/6373554?hl=en) y [Captions API](https://developers.google.com/youtube/v3/docs/captions)
- [Yamamoto et al., VAD y streaming ASR](https://aclanthology.org/2025.iwsds-1.26/), [Phoenix-VAD](https://arxiv.org/abs/2509.20410), [SimulStreaming/LocalAgreement-2](https://arxiv.org/html/2506.17077), [pyannote-audio](https://github.com/pyannote/pyannote-audio) y [benchmark](https://www.pyannote.ai/benchmark)

Las fuentes externas respaldan capacidades documentadas, no garantizan disponibilidad por región/cuenta ni sustituyen benchmarks del proyecto.

## Correcciones obligatorias

| No usar | Usar | Motivo |
|---|---|---|
| “GIP” | **Git** | El versionado real y el baseline son Git local: `v.0.15.11` sobre `c5e8864`. |
| “Grok” para referirse a Groq | **Groq** para los Slices actuales; **xAI** para la alternativa | Son proveedores diferentes, con APIs y costos diferentes. |
| `$0.004/min` como dato | **Costo pendiente de verificar por cuenta/modelo** | No existe confirmación oficial vigente en las fuentes consolidadas. |
| “5 s garantizados” | **Objetivo exploratorio de 5-10 s** | La latencia depende de captura, red, proveedor, cuota, audio y carga. |
| “Slice C = subtitulado vivo” | **Slice C = streaming incremental de snapshots y merge ordenado** | Falta hipótesis estable, committed text, endpointing y UI de captions. |

## Convocatoria futura exacta

Usar cualquiera de estas frases para recuperar la referencia correcta:

```text
Abrí el Audio2Text roadmap maestro y decime el estado de reuniones largas.
Recuperá el roadmap maestro de Audio2Text para subtitulado vivo.
Consultá Audio2Text roadmap maestro: traducción simultánea español-inglés.
Revisá en el roadmap maestro la parte de interlocutores y diarización.
¿Qué dependencias faltan antes de speech-to-speech según Audio2Text roadmap maestro?
Compará el estado Git v.0.15.11 y los Slices A/B/C con el roadmap maestro.
Usá el roadmap maestro de Audio2Text para preparar la evaluación de Planificador, Scheme y SEE.
No crees otro informe: actualizá o referenciá ROADMAP_AUDIO2TEXT_MASTER.md.
```

## Alcance de este documento

Este es el **índice único y liviano** del roadmap. No crea otro HTML, no duplica informes y no modifica código, tags ni builds. Los documentos detallados conservan la evidencia; este archivo conserva el mapa de decisión y la convocatoria.
