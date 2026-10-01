# Audio2Text y transcripción incremental: aprendizaje de v0.15.11

> **Baseline:** Git `v0.15.11` / `c5e8864`
> **Propósito:** explicar qué problema se resolvió, qué mecanismo quedó implementado y qué falta para un producto de transcripción realmente vivo.
> **Alcance:** documentación de aprendizaje. No modifica código, tags ni historial.

## Lectura ejecutiva

Audio2Text tenía una experiencia paradójica: podía grabar una reunión larga, pero la persona debía esperar a que terminara toda la transcripción. El cuello de botella no era únicamente “Groq lento”; era una combinación de trabajo acumulado, procesamiento posterior y fragilidad ante errores de red. Slices A, B y C atacan capas distintas:

| Estado | Qué significa en este baseline |
|---|---|
| **HECHO** | Slice A endurece la llamada a Groq: timeout, manejo de `413/429`, circuit breaker, progreso/ETA, checkpoint y logging. |
| **HECHO** | Slice B paraleliza el procesamiento posterior con un pool de 3 workers y conserva el orden al unir resultados. |
| **HECHO** | Slice C toma snapshots cada 25 s, usa un pool separado de 2 workers, persiste `.partial_stream.txt`, reordena por índice y deja solo los chunks restantes para el merge post-stop. |
| **HECHO** | En la prueba sintética registrada, un audio de 720 s deja aproximadamente 1–2 chunks para el cierre y el merge queda por debajo de 6 s. Es una prueba mock, no una garantía de red real. |
| **INFERENCIA** | La arquitectura desacopla gran parte de la latencia final de la duración total: mientras se graba, el trabajo ya avanza. |
| **PENDIENTE** | Slice C no es todavía subtitulado visible estable tipo YouTube ni un endpoint de speech streaming nativo. Es un backend incremental con evento de UI y resultado final ordenado. |

## 1. Historia del problema: los 20 minutos

El síntoma observado era el bloqueo exponencial aparente en una reunión de unos 20 minutos: al detener la grabación, Audio2Text recién comenzaba a partir, enviar y resolver todos los chunks. Si cada llamada sufría latencia, reintentos o un límite de tamaño, el tiempo de espera crecía con la cantidad de chunks. La interfaz quedaba sin una señal útil de avance durante la espera.

La lección importante es conceptual: **procesar después de grabar no es streaming**. Aunque se use paralelismo, si todo el audio espera al evento “stop”, el usuario sigue percibiendo la suma del trabajo pendiente.

### Causas raíz

| Causa | Efecto | Evidencia/estado |
|---|---|---|
| Procesamiento diferido | Toda la duración se convierte en trabajo post-stop. | **HECHO**, motivación de Slices B/C. |
| Chunks enviados secuencialmente o con capacidad limitada | La latencia de cada llamada se acumula. | **HECHO**, Slice B introduce pool de 3. |
| Respuesta desordenada de workers | Paralelizar sin índice puede alterar el texto. | **HECHO**, A/B/C preservan orden por índice. |
| Archivos grandes o límites del proveedor | `413` puede interrumpir una transcripción completa. | **HECHO**, Slice A clasifica y tolera `413`. |
| Rate limits y fallos transitorios | `429`/timeout no deben detener la captura. | **HECHO**, se registran como `STREAM` o error y el cierre puede reintentar. |
| Falta de checkpoint | Una caída obliga a repetir demasiado trabajo. | **HECHO**, existen checkpoints parciales; la estrategia de horas continuas aún requiere rotación/resume. |
| Confusión entre parcial y final | Un texto que cambia puede presentarse como definitivo. | **PENDIENTE**, falta contrato explícito de hipótesis/committed text. |

## 2. Qué hicieron A, B y C

### Slice A: resiliencia antes que velocidad

**HECHO.** El commit `17e8c20` agregó la base de hardening: timeout de 30 s por operación, manejo de `413/429`, circuit breaker, progreso/ETA, checkpoint y logger dedicado. Su función es que el sistema falle de manera acotada y observable.

**Aprendizaje:** el manejo de errores no es un detalle posterior. En una transcripción larga, disponibilidad, reintento y conservación del parcial forman parte del producto.

### Slice B: paralelismo post-stop

**HECHO.** El commit `f6f46ef` usa 3 workers para procesar chunks en paralelo y luego reconstruye el texto en orden. Reduce el tiempo de cierre cuando ya existe el audio completo, pero no elimina la espera previa al stop.

### Slice C: trabajo incremental durante la captura

**HECHO.** El commit `c5e8864` implementa:

- snapshot del buffer cada `25.0 s` bajo un lock breve;
- división compatible con el chunker post-stop, con objetivo de 25 s y máximo de 29 s;
- `ThreadPoolExecutor` separado con `2` workers;
- `streaming_pending` para no duplicar trabajo en vuelo;
- `streaming_ordered` para guardar texto por índice;
- checkpoint atómico en un archivo temporal terminado en `.partial_stream.txt`;
- evento de UI `En vivo Chunk cur/total` mediante la cola existente;
- espera de tareas en vuelo al detener y merge que intenta solo lo que falta;
- tolerancia a `429`, `413` y timeout sin propagar el error al loop de captura.

El diseño evita que la captura dependa de la API: la copia del audio es breve, el envío ocurre en background y las excepciones quedan registradas. El texto que llega antes puede estar disponible como estado parcial, mientras el resultado final se une después.

## 3. Snapshot de 25 s, pools y orden

### Flujo implementado

```text
Captura PCM
    |
    | cada 25 s: copia breve bajo audio_lock
    v
Snapshot -> chunker target 25 s / max 29 s
    |
    +--> pool streaming: 2 workers -> Groq -> streaming_ordered[idx]
    |                                      |
    |                                      +--> .partial_stream.txt
    |                                      +--> evento UI Chunk cur/total
    |
stop -> cierra nuevos submits -> espera in-flight -> snapshot ordenado
    |
    +--> merge solo de índices faltantes -> join sorted(idx) -> resultado final
```

### Por qué hay dos pools

El pool de streaming tiene 2 workers y el procesamiento post-stop de Slice B tiene su propia capacidad. La separación reduce la probabilidad de que el cierre o una ráfaga de trabajo posterior compita con la captura. **HECHO:** la separación está expresada en `backend/transcriber.py`. **RECOMENDACIÓN:** una futura versión debería medir límites efectivos del proveedor y hacer backpressure explícito; más workers no implica automáticamente más throughput.

### Por qué el orden no depende de la finalización

Los futures pueden terminar en cualquier orden. Cada chunk conserva `idx`; el resultado se guarda como `streaming_ordered[idx]` y el join recorre `sorted(keys)`. Así, el orden temporal del audio se conserva aunque el chunk 8 termine antes que el 7.

### Qué significa “25 s”

No significa que cada 25 s aparezca una frase perfecta. Es un intervalo de snapshot y un objetivo de chunking. El último tramo se retiene mientras la grabación sigue activa para evitar enviar un borde incompleto; el cierre procesa el tail restante.

## 4. Qué está realmente hecho y qué se infiere

| Afirmación | Clasificación | Lectura correcta |
|---|---|---|
| Hay snapshot periódico de 25 s. | **HECHO** | Está implementado y cubierto por tests de Slice C. |
| Hay pool streaming separado de 2 workers. | **HECHO** | Es una constante y un executor distinto del post-stop. |
| El merge conserva el orden. | **HECHO** | Se ordena por índice antes del `join`. |
| El post-stop de un caso mock de 720 s queda bajo 6 s. | **HECHO** | Resultado de test sintético con Groq mock y dos chunks restantes. |
| La aplicación entrega subtítulos vivos estables. | **INFERENCIA INCORRECTA** | Hoy hay backend parcial y un evento `En vivo Chunk cur/total`; no hay estabilización de texto visible. |
| La latencia real es constante en producción. | **INFERENCIA NO DEMOSTRADA** | Depende de red, rate limits, modelo, cuenta, audio y carga. |
| Más workers siempre aceleran. | **INFERENCIA FALSA** | Puede aumentar presión de rate limit y contention. |

## 5. Límite central: no es todavía YouTube live captions

Slice C **no** implementa un subtitulado visible estable tipo YouTube. El evento de UI informa progreso de chunks; no expone un texto provisional que se reescribe de manera controlada. Tampoco existe un endpoint público de YouTube que permita asumir su lógica interna de captions live.

Para vivo real hacen falta, como mínimo:

1. **Hypotheses:** texto provisional asociado a una ventana de audio.
2. **Committed text:** prefijo que ya no se reescribe.
3. **Endpointing:** decisión de cuándo terminó una frase, acústica y/o semánticamente.
4. **Overlap:** contexto de audio entre ventanas para no cortar palabras.
5. **Contrato de UI:** distinguir provisional, confirmado, corregido y error.
6. **Métricas:** latencia del primer texto, frecuencia de revisión, tasa de borrado/revisión, WER final y latencia de segmento.

**RECOMENDACIÓN.** No convertir `streaming_ordered` directamente en un textbox final. Primero definir el modelo de estado de hipótesis y committed text.

## 6. Roadmap técnico: 5–10 s sin prometer

El objetivo semántico razonable es explorar ventanas de 5–10 s, no declarar una garantía. Un pipeline futuro podría ser:

```text
PCM -> jitter buffer -> VAD + hangover -> decoder/API incremental
                                  |
                    endpointing acústico/semántico
                                  |
                  estabilizador de hipótesis
                    |                         |
              provisional UI             committed text
```

| Etapa | Propuesta | Estado |
|---|---|---|
| VAD | Detectar voz/silencio con hangover para no cortar consonantes o pausas breves. | **RECOMENDACIÓN** |
| Solapamiento | Mantener contexto de audio entre ventanas y deduplicar texto repetido. | **RECOMENDACIÓN** |
| Endpointing | Combinar silencio acústico con una señal semántica para frases incompletas. | **PENDIENTE** |
| Estabilidad | Aceptar un prefijo tras coincidencia de hipótesis consecutivas, con latencia configurable. | **RECOMENDACIÓN** |
| Proveedor | Evaluar un STT con interim events documentados; Groq batch no demuestra streaming nativo en la documentación consultada. | **PENDIENTE** |
| Medición | Benchmark E2E captura→red→API→UI con P50/P95 y revisión de texto. | **PENDIENTE** |

Reducir el intervalo de 25 s a 5 s aumenta llamadas, coste potencial, presión de rate limit y riesgo de duplicación en los bordes. La mejora debe validarse, no suponerse.

## 7. Traducción con contexto

Una cascada `ASR -> traducción -> TTS` es integrable, pero propaga errores y suma latencia. Para conservar coherencia entre chunks, la capa de traducción debería recibir:

- texto committed reciente;
- resumen de contexto acotado;
- glosario y nombres propios;
- idioma origen y destino;
- señal de inicio/cierre de turno cuando exista;
- identificador de segmento para reintentos idempotentes.

**HECHO de investigación:** el endpoint Groq de translations documentado traduce a inglés y el modelo `whisper-large-v3-turbo` no figura con traducción soportada en esa documentación. **PENDIENTE:** definir una estrategia multilingüe real. xAI ofrece capacidades de voz distintas, pero no debe inferirse que speech-to-speech equivale a subtitulado estable ni a traducción multilingüe con committed text.

## 8. Fuentes de audio en Windows

| Fuente | Qué captura | Límite |
|---|---|---|
| Micrófono por endpoint | Señal del dispositivo de entrada seleccionado. | Requiere elegir dispositivo y manejar cambios. |
| WASAPI loopback | Mezcla del endpoint de render del sistema. | Shared mode; no es una captura universal de cada aplicación. |
| Stereo Mix / What You Hear | Mezcla expuesta por ciertos drivers. | Opcional, no estandarizada y puede estar deshabilitada. |
| Varias fuentes | Buffers separados por endpoint. | No se debe asumir sincronización perfecta entre clocks. |

**HECHO de investigación:** Microsoft documenta loopback WASAPI por endpoint. **PENDIENTE:** validar una combinación concreta de bindings Python y la política de selección/sincronización para este repo.

## 9. Meet, Teams y Zoom: metadata y APIs

| Plataforma | Relevante para vivo | Qué no asumir |
|---|---|---|
| Google Meet | Media API en Developer Preview con audio, video y metadata de participantes bajo requisitos de proyecto/OAuth/inscripción. | No asumir disponibilidad general ni que REST transcripts entregue parciales vivos. |
| Microsoft Teams | Microsoft Graph expone transcript/recording post-meeting bajo permisos y controles del tenant. | No confundir artefacto VTT posterior con streaming propio. |
| Zoom | RTMS documenta audio/video/screen share y transcript en vivo por WebSocket, con atribución por participante y opciones de audio por participante o merged. | Requiere scopes, aplicación y créditos del Developer Pack; SDK Web/Meeting no es equivalente a RTMS. |

**RECOMENDACIÓN.** Si el objetivo es atribución confiable, usar metadata estructural de la plataforma cuando esté permitido, en lugar de inferir hablantes únicamente desde texto.

## 10. Diarización

La diarización audio-only requiere segmentación, embeddings y manejo de solapamiento de voces. El video agrega asociación con active speaker, rostro, labios y sincronización audiovisual. Timestamps no significan speaker labels.

| Fuente de identidad | Calidad esperable | Estado |
|---|---|---|
| Metadata Meet/Zoom | Atribución estructural si la API la entrega. | **RECOMENDACIÓN** |
| Diarización audio-only | Requiere modelo/servicio adicional, por ejemplo una familia especializada como pyannote. | **PENDIENTE** |
| xAI/Groq STT | No hay evidencia consultada de speaker labels nativos. | **HECHO de investigación** |
| Video + audio | Mejor señal potencial, mayor complejidad y sincronización. | **PENDIENTE** |

## 11. Groq no es xAI/Grok

| Proveedor | Capacidades documentadas relevantes | Lectura para Audio2Text |
|---|---|---|
| **Groq** | Endpoints OpenAI-compatible de STT batch (`/openai/v1/audio/transcriptions` y `/translations`), modelos Whisper, timestamps y límites de archivo. | Es la dependencia de los Slices A/B/C actuales. La documentación consultada no demuestra STT streaming nativo con interim events. |
| **xAI** | Voice API, STT y TTS; documentación de streaming STT e interim results, además de speech-to-speech realtime. | Es una alternativa futura a evaluar, con límites, precios, región y disponibilidad por cuenta. No es el proveedor actual de Slice C. |

El parecido de “Grok” con “Groq” es una fuente de errores de arquitectura y costos. Deben mantenerse separados en documentación, configuración, métricas y decisiones.

## 12. Costos: no asumidos

No se adopta como hecho el valor `$0.004/min`. Se registra como afirmación previa no confirmada y se corrige abajo. Tampoco se transforma un free tier en “costo cero de producción”.

La cuenta correcta para planificar es:

```text
costo estimado = minutos enviados x precio vigente del modelo/cuenta
                 + traducción/TTS si aplica
                 + créditos o servicios de plataforma
                 + margen por reintentos y solapamiento
```

| Plan por cuenta | Decisión operativa | Estado |
|---|---|---|
| Free/development | Usar solo para pruebas controladas; registrar límites y respuestas `429`. | **RECOMENDACIÓN** |
| Paid individual | Verificar precio, rate limit, concurrencia y facturación mínima antes de 5 h. | **PENDIENTE** |
| Team/enterprise | Confirmar límites del workspace, retención, consentimiento y presupuesto. | **PENDIENTE** |
| xAI separado | Presupuestar como proveedor distinto; no reutilizar tarifas de Groq. | **RECOMENDACIÓN** |

## 13. Cinco horas: rotación, checkpoints y plan por cuenta

Cinco horas son `18.000 s`. Con snapshots nominales de 25 s, el orden de magnitud es `720` intervalos si todos fueran exactos; el chunker real puede producir variaciones por silencios y límites. Esto no promete 720 llamadas ni una duración fija de cada chunk.

**RECOMENDACIÓN de diseño, aún no implementada:**

1. Rotar archivos de audio por una ventana acotada, por ejemplo por tiempo configurable, sin conservar cinco horas completas en RAM.
2. Persistir metadata de sesión, índice de chunk, hash, estado `pending/complete/failed` y ruta del checkpoint.
3. Escribir checkpoint después de cada chunk completado y hacerlo atómico.
4. Reanudar desde el primer índice faltante, sin duplicar chunks ya confirmados.
5. Mantener un límite de concurrencia por cuenta y backoff con jitter para `429`.
6. Separar costo de captura local, STT, traducción, TTS y plataforma de reunión.
7. Ejecutar una prueba piloto por cuenta con presupuesto máximo y métricas E2E.

**PENDIENTE:** Slice C persiste un parcial de texto, pero no implementa todavía una sesión durable de cinco horas con rotación de WAV, journal de estados y resume tras caída. La cifra de memoria o tamaño de audio depende de sample rate, canales, formato y política de buffer; no debe generalizarse sin medir la configuración real.

## 14. Correcciones a afirmaciones previas

| Afirmación anterior | Corrección |
|---|---|
| “GIP” para versionado. | **Git** es el término correcto. El baseline es Git tag `v.0.15.11` sobre `c5e8864`. |
| `$0.004/min` como costo. | No confirmado por fuente oficial vigente; queda fuera de cualquier presupuesto. Verificar pricing/rate limits por modelo y cuenta. |
| xAI/Grok y Groq como si fueran lo mismo. | Son proveedores distintos, con APIs, límites y precios distintos. |
| “5 s garantizados”. | No hay garantía. El sistema actual usa snapshots de 25 s; 5–10 s es una recomendación a medir. |
| Slice C como subtitulado vivo estable. | Es backend incremental/evento de chunks y merge final; falta hipótesis, committed text y endpointing. |

## 15. Fuentes de investigación

Fuentes consultadas el 2026-08-28; se conservan como referencias de investigación, no como garantía contractual:

- xAI modelos: <https://docs.x.ai/developers/models>
- xAI speech-to-text: <https://docs.x.ai/developers/models/speech-to-text>
- xAI speech-to-speech: <https://docs.x.ai/developers/models/speech-to-speech>
- xAI pricing: <https://docs.x.ai/developers/pricing>
- Groq speech-to-text: <https://console.groq.com/docs/speech-to-text>
- Groq text-to-speech: <https://console.groq.com/docs/text-to-speech>
- Microsoft WASAPI loopback: <https://learn.microsoft.com/en-us/windows/win32/coreaudio/loopback-recording>
- Google Meet Media API: <https://developers.google.com/workspace/meet/media-api/guides/overview>
- Google Meet transcripts REST: <https://developers.google.com/workspace/meet/api/reference/rest/v2/conferenceRecords.transcripts>
- Microsoft Teams transcripts: <https://learn.microsoft.com/en-us/microsoftteams/platform/graph-api/meeting-transcripts/overview-transcripts>
- Zoom RTMS: <https://developers.zoom.us/docs/rtms/>
- Zoom RTMS meetings media: <https://developers.zoom.us/docs/rtms/meetings/media/>
- Zoom RTMS getting started: <https://developers.zoom.us/docs/rtms/meetings/getting-started/>
- YouTube captions help: <https://support.google.com/youtube/answer/6373554?hl=en>
- YouTube Data API captions: <https://developers.google.com/youtube/v3/docs/captions>
- Yamamoto et al., VAD y streaming ASR: <https://aclanthology.org/2025.iwsds-1.26/>
- Phoenix-VAD: <https://arxiv.org/abs/2509.20410>
- SimulStreaming / LocalAgreement-2: <https://arxiv.org/html/2506.17077>
- pyannote audio: <https://github.com/pyannote/pyannote-audio>
- pyannote benchmark: <https://www.pyannote.ai/benchmark>

## 16. Validación documental

| Control | Resultado |
|---|---|
| Baseline citado | **HECHO:** `v.0.15.11`, `c5e8864`. |
| Código/tags modificados | **HECHO:** no se modificaron. |
| Hechos separados de inferencias | **HECHO:** tags explícitos en tablas y texto. |
| Costos no inventados | **HECHO:** `$0.004/min` queda marcado como no confirmado. |
| HTML offline | **PENDIENTE durante generación:** se validará que no haya CDN, placeholders ni referencias externas de recursos. |
