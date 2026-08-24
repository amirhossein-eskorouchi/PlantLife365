"""
PlantLife365 local AI-assistant service.

The maintained implementation keeps model communication separate from
the Django view and restricts the default Ollama connection to local
loopback hosts.
"""

import json
import os
import urllib.error
import urllib.parse
import urllib.request

from .data_services import get_latest_reading
from .models import (
    HardwareDevice,
    SystemLog,
    UserSubscription,
)


DEFAULT_OLLAMA_URL = (
    "http://127.0.0.1:11434/api/generate"
)

DEFAULT_OLLAMA_MODEL = "phi3"
DEFAULT_TIMEOUT_SECONDS = 20
MAX_MESSAGE_LENGTH = 2000

LOCAL_HOSTS = {
    "localhost",
    "127.0.0.1",
    "::1",
}


class AssistantServiceError(RuntimeError):
    """Raised when the local assistant cannot satisfy a request."""


def _env_truthy(
    name,
    default=False,
):
    raw = os.environ.get(
        name
    )

    if raw is None:
        return default

    return raw.strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _assistant_timeout():
    try:
        timeout = int(
            os.environ.get(
                "OLLAMA_TIMEOUT_SECONDS",
                str(DEFAULT_TIMEOUT_SECONDS),
            )
        )
    except ValueError:
        timeout = DEFAULT_TIMEOUT_SECONDS

    timeout = max(
        1,
        timeout,
    )

    timeout = min(
        60,
        timeout,
    )

    return timeout


def _ollama_url():
    url = os.environ.get(
        "OLLAMA_URL",
        DEFAULT_OLLAMA_URL,
    ).strip()

    parsed = urllib.parse.urlparse(
        url
    )

    if parsed.scheme not in {
        "http",
        "https",
    }:
        raise AssistantServiceError(
            "OLLAMA_URL must use HTTP or HTTPS."
        )

    host = (
        parsed.hostname
        or ""
    ).lower()

    allow_remote = _env_truthy(
        "PLANTLIFE365_ALLOW_REMOTE_OLLAMA",
        default=False,
    )

    if not allow_remote:
        if host not in LOCAL_HOSTS:
            raise AssistantServiceError(
                "Remote Ollama endpoints are disabled by default."
            )

    return url


def _project_knowledge():
    return (
        "PlantLife365 is an IoT-enabled agricultural monitoring "
        "and decision-support research platform. The maintained "
        "system includes ESP32 sensing and imaging, authenticated "
        "telemetry ingestion, a Django dashboard, historical data "
        "visualization, CSV export, alerts, and exploratory "
        "regression analytics. Custom server-side Python execution "
        "is intentionally disabled. Subscription tiers are prototype "
        "application logic and are not a production payment system."
    )


def _latest_sensor_context(user):
    latest = get_latest_reading(
        user
    )

    if latest is None:
        return (
            "Current telemetry: no active device reading is available."
        )

    return (
        "Current telemetry:\n"
        f"- Device: {latest.device_id}\n"
        f"- Temperature: {latest.temperature} C\n"
        f"- Humidity: {latest.humidity}%\n"
        f"- Water level: {latest.water_level}%\n"
        f"- Light: {latest.light}%\n"
        f"- Gas measurement: {latest.gas}%\n"
        f"- Timestamp: {latest.timestamp.isoformat()}"
    )


def _recent_log_context(user):
    logs = (
        SystemLog.objects
        .filter(
            owner=user
        )
        .order_by(
            "-timestamp"
        )[:5]
    )

    if not logs:
        return (
            "Recent alerts: none."
        )

    lines = [
        "Recent alerts:"
    ]

    for log in logs:
        lines.append(
            (
                f"- [{log.level}] "
                f"{log.timestamp.isoformat()}: "
                f"{log.message}"
            )
        )

    return "\n".join(
        lines
    )


def _account_context(user):
    active_devices = HardwareDevice.objects.filter(
        owner=user,
        is_active=True,
    ).count()

    subscription, _ = UserSubscription.objects.get_or_create(
        user=user
    )

    return (
        "Application context:\n"
        f"- Active devices: {active_devices}\n"
        f"- Prototype tier: {subscription.get_tier_display()}\n"
        f"- Maximum configured devices: {subscription.max_devices}"
    )


def build_user_context(user):
    return "\n\n".join(
        [
            _project_knowledge(),
            _account_context(user),
            _latest_sensor_context(user),
            _recent_log_context(user),
        ]
    )


def generate_assistant_reply(
    user,
    message,
):
    message = str(
        message
        or ""
    ).strip()

    if not message:
        raise AssistantServiceError(
            "Message is required."
        )

    if len(message) > MAX_MESSAGE_LENGTH:
        raise AssistantServiceError(
            f"Message exceeds {MAX_MESSAGE_LENGTH} characters."
        )

    context = build_user_context(
        user
    )

    prompt = (
        "You are the PlantLife365 monitoring assistant.\n\n"
        "Use only the supplied application and telemetry context when "
        "making claims about the user's system. If the context does "
        "not contain the information needed, say that the information "
        "is unavailable. Do not claim that exploratory regression "
        "outputs are agronomic recommendations.\n\n"
        f"{context}\n\n"
        f"User question:\n{message}\n\n"
        "Assistant response:"
    )

    url = _ollama_url()

    model_name = os.environ.get(
        "OLLAMA_MODEL",
        DEFAULT_OLLAMA_MODEL,
    ).strip()

    if not model_name:
        model_name = DEFAULT_OLLAMA_MODEL

    request_payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False,
    }

    encoded_payload = json.dumps(
        request_payload
    ).encode(
        "utf-8"
    )

    request = urllib.request.Request(
        url,
        data=encoded_payload,
        headers={
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=_assistant_timeout(),
        ) as response:
            raw_response = response.read().decode(
                "utf-8"
            )

    except urllib.error.URLError as exc:
        raise AssistantServiceError(
            "Could not connect to the configured local AI service."
        ) from exc

    except TimeoutError as exc:
        raise AssistantServiceError(
            "The local AI service timed out."
        ) from exc

    try:
        parsed_response = json.loads(
            raw_response
        )
    except json.JSONDecodeError as exc:
        raise AssistantServiceError(
            "The local AI service returned invalid JSON."
        ) from exc

    reply = str(
        parsed_response.get(
            "response",
            "",
        )
    ).strip()

    if not reply:
        raise AssistantServiceError(
            "The local AI service returned an empty response."
        )

    return reply
