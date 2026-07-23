# Transcription Agents Specification

## Purpose

Define the Adapter+Provider architecture for Audio2Text v2's transcription,
metadata, block, and post-processing agents. Business modules MUST depend
on Protocols (ports); concrete adapters are injected at runtime by
`DependencyManager`. Event flow and the recording lifecycle are coordinated
by `BusEventManager` and `StateMachineManager`.

## Requirements

### Requirement: TranscriptionProvider Protocol

The system SHALL define a `TranscriptionProvider` Protocol in
`audio2text/providers/base.py` exposing `transcribe_file`,
`transcribe_stream`, `validate_config`, and the `is_available`,
`provider_name`, `model_name` properties. No service MAY import a concrete
provider class.

#### Scenario: Service depends on Protocol only

- GIVEN `TranscriptionService` accepts a `TranscriptionProvider`
- WHEN a test injects a `MockProvider`
- THEN the service calls `transcribe_file` without importing `groq_provider`

#### Scenario: Unavailable provider is skipped

- GIVEN `GroqProvider.is_available` returns `False`
- WHEN the service resolves the provider
- THEN `transcribe` returns `None` without raising

### Requirement: Three Concrete Provider Adapters

The system MUST ship exactly three production adapters:
`GroqProvider`, `FasterWhisperProvider`, `NvidiaRivaProvider`. Each SHALL
implement `TranscriptionProvider` and register with `DependencyManager`
under its type key (`groq`, `faster_whisper`, `nvidia`).

#### Scenario: DependencyManager resolves Groq

- GIVEN `DependencyManager` has `groq` registered
- WHEN a caller requests the provider for type `"groq"`
- THEN a `GroqProvider` instance is returned
- AND its `provider_name` equals `"groq"`

#### Scenario: Unknown provider type rejected

- GIVEN the registered types are `groq`, `faster_whisper`, `nvidia`
- WHEN a caller requests type `"azure"`
- THEN `ValueError` listing valid types is raised

### Requirement: Injectable Block Adapters

`TaskExtractor`, `Summary`, `KeywordExtractor` MUST be adapters of a
`PostProcessingBlock` Protocol with `process(text) -> BlockResult`. They
SHALL be injected into `TranscriptionService` as a list, not hard-wired as
pipeline stages.

#### Scenario: Caller composes block list

- GIVEN a caller injects `[TaskExtractor, Summary]` into the service
- WHEN transcription completes
- THEN only those two blocks run, in injection order
- AND the pipeline does not reference blocks by name

### Requirement: MetadataProvider as Injectable Adapter

The system SHALL define a `MetadataProvider` Protocol for persisting
transcription metadata. The default JSONL adapter MUST be replaceable
without changing `TranscriptionService`.

#### Scenario: Custom MetadataProvider injected

- GIVEN a test injects an in-memory `MetadataProvider`
- WHEN transcription completes
- THEN metadata is written to the injected provider only
- AND no file is created on disk

### Requirement: Post-Processing via ExternalAPIManager

All LLM calls (AI enhancement, block LLM work) SHALL go through core-cenf
`ExternalAPIManager`, which provides retry, circuit breaker, and timeout.
Direct client construction in services MUST NOT exist.

#### Scenario: Circuit breaker trips on Groq LLM failure

- GIVEN the LLM endpoint has failed 5 consecutive times
- WHEN a block attempts an LLM call
- THEN `ExternalAPIManager` short-circuits with `CircuitOpenError`
- AND the block returns fallback text without retrying

### Requirement: BusEventManager for Transcription Events

The system SHALL publish lifecycle events on `BusEventManager`:
`transcription.started`, `transcription.completed`,
`transcription.failed`. Subscribers MUST subscribe to the bus and MUST NOT
be called directly by the service.

#### Scenario: Completion event reaches subscriber

- GIVEN a component subscribes to `transcription.completed`
- WHEN a job finishes successfully
- THEN it receives a `TranscriptionResult` payload
- AND the service has no direct reference to the subscriber

### Requirement: StateMachineManager for Recording FSM

The recording lifecycle SHALL be driven by a `StateMachineManager` FSM with
states `idle → recording → transcribing → done` and an `error` terminal.
Only valid transitions are permitted; invalid transitions raise
`InvalidTransition`.

#### Scenario: Happy-path transitions

- GIVEN the FSM is in state `idle`
- WHEN events `start`, `stop`, `transcribed` fire in order
- THEN the FSM reaches `done` without raising `InvalidTransition`

#### Scenario: Double-start rejected

- GIVEN the FSM is in state `recording`
- WHEN a second `start` event fires
- THEN `InvalidTransition` is raised and state stays `recording`

### Requirement: DependencyManager for Runtime Resolution

The system SHALL use `DependencyManager` to resolve providers, blocks, and
metadata adapters at runtime based on configuration. Hard-coded provider
ladders MUST NOT exist outside `DependencyManager`.

#### Scenario: Fallback chain exercised

- GIVEN config `providers.fallback_chain = ["faster_whisper", "groq"]`
- WHEN the primary provider `"nvidia"` returns `is_available=False`
- THEN `DependencyManager` resolves the next available provider
- AND the chosen `provider_name` is `"faster_whisper"`
