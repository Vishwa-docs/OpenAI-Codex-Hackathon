from __future__ import annotations

import httpx

from services.api.app.core.settings import Settings
from services.api.app.domain.repository import SeedRepository
from services.api.app.services.chat import EvidenceGroundedChatService


def test_chat_service_requires_openai_configuration() -> None:
    repository = SeedRepository()
    project = repository.get_project("legacycart")
    service = EvidenceGroundedChatService(Settings(openai_api_key=None))

    reply = service.build_reply(project, "Should we move the database first?")

    assert "OPENAI_API_KEY" in reply


def test_chat_service_uses_openai_response_when_configured(monkeypatch) -> None:
    repository = SeedRepository()
    project = repository.get_project("legacycart")
    service = EvidenceGroundedChatService(Settings(openai_api_key="test-key"))

    def fake_post(self, url: str, *, headers: dict[str, str], json: dict[str, object]):  # noqa: ARG001
        assert url.endswith("/chat/completions")
        assert headers["Authorization"] == "Bearer test-key"
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": (
                                "Defer the database-first wave until secrets and logging blockers are remediated.\n"
                                "Sources: demo-systems/legacycart/backend/src/main/resources/application-prod.yml"
                            )
                        }
                    }
                ]
            },
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(httpx.Client, "post", fake_post)

    reply = service.build_reply(project, "Should we move the database first?")

    assert "database-first" in reply
    assert "Sources:" in reply
