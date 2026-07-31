---
name: voice
description: Harmony's local voice capability — speech-to-text (whisper) and text-to-speech (Kokoro) served as OpenAI-compatible /audio/* routes through LiteLLM. Unlike search/imagegen/browser, voice is NOT an agent-invoked MCP tool — it's channel-level config an OpenClaw gateway consumes automatically. Load when wiring voice on a gateway or reasoning about how voice notes/replies flow.
tier: subject
requires: [cluster]
audience: [crew]
---

## What this capability is

Harmony self-hosts voice as **OpenAI-compatible audio endpoints behind LiteLLM** — no cloud dependency:

- **STT (speech → text):** model id `whisper-1` (GPU whisper-large-v3-turbo, with a CPU faster-whisper fallback), on LiteLLM's `/audio/transcriptions` (`mode: audio_transcription`). Callers always send `model=whisper-1`; LiteLLM's fallback machinery covers a GPU miss.
- **TTS (text → speech):** model id `kokoro` (Kokoro-FastAPI, native `/audio/speech`, `mode: audio_speech`), with selectable voices (e.g. `af_heart`, `af_bella`).

Any client can call these directly like any OpenAI `/audio/*` endpoint. The distinction that matters: **voice is not a tool an agent decides to call** — it's wired into the *channel*, so it happens around the conversation, not inside the agent's tool loop.

## How OpenClaw consumes it (the wiring)

Voice on an OpenClaw gateway is three separate config blocks, each independent:

- **`tools.media.audio`** — inbound STT. A Telegram/mobile **voice note** is auto-transcribed to text before the agent sees it. Config lists an STT model (`whisper-1`) with a `baseUrl` and a **`provider`**.
- **`messages.tts`** — outbound TTS. Replies are spoken back. `auto` controls when: `off` / `always` / `inbound` (speak only when the user sent voice) / `tagged`. Points at `kokoro` + a `speakerVoice`.
- **`talk.realtime`** — voice *conversation* mode. Set `mode: stt-tts` to compose the local whisper+Kokoro pair (turn-based). `realtime` mode is a cloud-only, different path — the local pair does not serve the browser Control-UI mic or a realtime Talk client, only Telegram/mobile turn-based voice.

Config is read at **startup** — every voice change needs a gateway restart to take effect.

## The auth landmine (STT)

`media.audio` STT auth resolves from **`models.providers.<provider>.apiKey`**, NOT from an inline `headers` block, and `<provider>` must be a **provider key that is actually defined** in the gateway config. Pointing it at an undefined provider (e.g. a bare `openai` that was never defined) throws a client-side `ProviderAuthError` — and the visible symptom is the agent replying to an **empty transcript** (it looks like the model ignored you, not like an auth failure). Use the same defined LiteLLM VK provider the chat path uses. TTS auth follows the same `providers.<provider>.apiKey` shape.

## Per-harness

- **OpenClaw:** the primary consumer — voice is channel config as above (operator wires it; the agent just talks).
- **Claude Code / pi.dev:** can call `/audio/transcriptions` and `/audio/speech` directly through the LiteLLM base URL when a task needs transcription or narration, but there's no dedicated tool — it's a plain OpenAI-compatible request.

## Notes

- Best-quality open TTS models are non-commercial (XTTS/Fish/F5); Kokoro is the CPU-friendly, commercially-usable default. GPU TTS with voice cloning (Chatterbox, MIT) is a separate, heavier option.
- Realtime *web/browser* voice is cloud-only today — the local pair is turn-based STT-TTS for chat channels, not a realtime websocket.
