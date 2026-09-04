from pathlib import Path

from fastapi.testclient import TestClient

from app.api import templates
from app.main import app
from app.schemas import TemplateUpsertRequest
from app.services.template_store import TemplateStore
from app.services import template_renderer


def test_template_store_survives_a_new_store_instance(tmp_path: Path) -> None:
    database = tmp_path / "pawpost.db"
    first = TemplateStore(database)
    created = first.upsert(
        TemplateUpsertRequest(
            category="pet",
            name="海のお出かけ",
            template_body="{caption}\n\n{hashtags}",
        )
    )

    restarted = TemplateStore(database)
    restored = restarted.get(created.template_id)

    assert restored is not None
    assert restored.category == "pet"
    assert restored.name == "海のお出かけ"
    assert restored.template_body == "{caption}\n\n{hashtags}"


def test_saved_template_is_resolved_by_post_renderer(tmp_path: Path, monkeypatch) -> None:
    store = TemplateStore(tmp_path / "renderer.db")
    saved = store.upsert(
        TemplateUpsertRequest(
            category="travel",
            name="旅の記録",
            template_body="📍 {title}\n\n{caption}\n\n{hashtags}",
        )
    )
    monkeypatch.setattr(template_renderer, "persistent_template_store", store)

    template_id, body = template_renderer.resolve_template("travel", saved.template_id)

    assert template_id == saved.template_id
    assert body.startswith("📍 {title}")


def test_template_api_is_category_scoped_and_supports_update_delete(tmp_path: Path, monkeypatch) -> None:
    store = TemplateStore(tmp_path / "api.db")
    monkeypatch.setattr(templates, "template_store", store)
    client = TestClient(app)

    created_response = client.post(
        "/api/templates",
        json={
            "category": "restaurant",
            "name": "店舗の短文",
            "template_body": "{title}\n\n{caption}\n\n{hashtags}",
        },
    )
    assert created_response.status_code == 201
    created = created_response.json()
    assert created["category"] == "restaurant"
    assert created["is_builtin"] is False

    assert client.get("/api/templates?category=restaurant").json()[0]["template_id"] == created["template_id"]
    assert client.get("/api/templates?category=pet").json() == []

    updated_response = client.put(
        f"/api/templates/{created['template_id']}",
        json={
            "template_id": created["template_id"],
            "category": "restaurant",
            "name": "店舗の紹介文",
            "template_body": "{caption}\n\n{hashtags}",
        },
    )
    assert updated_response.status_code == 200
    assert updated_response.json()["name"] == "店舗の紹介文"

    assert client.delete(f"/api/templates/{created['template_id']}").status_code == 204
    assert client.get("/api/templates?category=restaurant").json() == []


def test_template_api_rejects_unknown_variables(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(templates, "template_store", TemplateStore(tmp_path / "api.db"))
    response = TestClient(app).post(
        "/api/templates",
        json={
            "category": "pet",
            "name": "無効なテンプレート",
            "template_body": "{caption}\n{not_allowed}",
        },
    )

    assert response.status_code == 422
    assert "not_allowed" in response.json()["detail"]
