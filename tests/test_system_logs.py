import json

from django.test import RequestFactory

from dashboard.models import SystemLog
from dashboard.views import logs_api


def decode_json_response(response):
    return json.loads(
        response.content.decode(
            "utf-8"
        )
    )


def test_logs_api_only_returns_current_user_logs(
    user,
    second_user,
):
    own_log = SystemLog.objects.create(
        owner=user,
        level="INFO",
        message="Own alert",
    )

    SystemLog.objects.create(
        owner=second_user,
        level="CRITICAL",
        message="Other user alert",
    )

    factory = RequestFactory()

    request = factory.get(
        "/api/logs/"
    )

    request.user = user

    response = logs_api(
        request
    )

    assert response.status_code == 200

    payload = decode_json_response(
        response
    )

    assert len(
        payload["logs"]
    ) == 1

    assert payload["logs"][0]["id"] == own_log.id

    assert payload["logs"][0]["message"] == "Own alert"
