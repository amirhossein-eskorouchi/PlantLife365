# Local AI Assistant

## Purpose

PlantLife365 includes an optional conversational interface that can
summarize the authenticated user's monitoring context through a
configured Ollama-compatible language model.

The maintained implementation separates model communication into:

dashboard/assistant_service.py

## Context

The assistant receives a compact user-scoped context containing:

- active-device count
- prototype subscription tier
- latest telemetry
- up to five recent user-owned logs
- a concise description of maintained PlantLife365 capabilities

It does not intentionally query another user's devices or logs.

## Local-by-default policy

The default endpoint is:

http://127.0.0.1:11434/api/generate

By default the application permits only loopback hosts:

- localhost
- 127.0.0.1
- ::1

Remote endpoints require explicit configuration through:

PLANTLIFE365_ALLOW_REMOTE_OLLAMA=true

## Configuration

Environment variables:

- OLLAMA_URL
- OLLAMA_MODEL
- OLLAMA_TIMEOUT_SECONDS
- PLANTLIFE365_ALLOW_REMOTE_OLLAMA

## Authentication and CSRF

The maintained chatbot endpoint requires:

- an authenticated Django user
- POST
- Django CSRF protection

The historical CSRF-exempt chatbot behavior is not retained.

## Prompt boundary

The assistant is instructed to use supplied monitoring context when
making claims about the user's PlantLife365 system.

If required information is unavailable, the assistant should say so.

Exploratory regression outputs should not be presented as agronomic
recommendations.

## Limitation

Generated language-model responses may be incorrect.

PlantLife365 does not represent those responses as verified operational
or agronomic advice.
