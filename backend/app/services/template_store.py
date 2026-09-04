"""SQLite-backed persistence for user-owned post templates."""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from uuid import uuid4

from ..category_settings import Category
from ..schemas import SavedTemplate, TemplateUpsertRequest


DEFAULT_DB_PATH = Path(
    os.getenv("PAWPOST_TEMPLATE_DB_PATH", str(Path(__file__).resolve().parents[2] / "data" / "pawpost.db"))
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class TemplateStore:
    """Small single-file store; SQLite handles restart persistence and file locking."""

    def __init__(self, db_path: Path | str = DEFAULT_DB_PATH) -> None:
        self.db_path = Path(db_path)
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.db_path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout = 5000")
        return connection

    def _ensure_schema(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS post_templates (
                    template_id TEXT PRIMARY KEY,
                    category TEXT NOT NULL,
                    name TEXT NOT NULL,
                    template_body TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_post_templates_category_updated "
                "ON post_templates(category, updated_at DESC)"
            )

    @staticmethod
    def _to_model(row: sqlite3.Row) -> SavedTemplate:
        return SavedTemplate(
            template_id=str(row["template_id"]),
            category=row["category"],
            name=str(row["name"]),
            template_body=str(row["template_body"]),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )

    def list(self, category: Category | None = None) -> list[SavedTemplate]:
        with self._connect() as connection:
            if category:
                rows = connection.execute(
                    "SELECT * FROM post_templates WHERE category = ? "
                    "ORDER BY updated_at DESC, name COLLATE NOCASE ASC",
                    (category,),
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT * FROM post_templates "
                    "ORDER BY category ASC, updated_at DESC, name COLLATE NOCASE ASC"
                ).fetchall()
        return [self._to_model(row) for row in rows]

    def get(self, template_id: str) -> SavedTemplate | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM post_templates WHERE template_id = ?",
                (template_id,),
            ).fetchone()
        return self._to_model(row) if row else None

    def upsert(self, request: TemplateUpsertRequest) -> SavedTemplate:
        name = request.name.strip()
        body = request.template_body.strip()
        template_id = request.template_id or f"saved_{uuid4().hex[:16]}"
        now = _now()
        with self._connect() as connection:
            existing = connection.execute(
                "SELECT created_at, category FROM post_templates WHERE template_id = ?",
                (template_id,),
            ).fetchone()
            if existing and existing["category"] != request.category:
                raise ValueError("テンプレートのカテゴリは変更できません。")
            created_at = str(existing["created_at"]) if existing else now
            connection.execute(
                """
                INSERT INTO post_templates(
                    template_id, category, name, template_body, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(template_id) DO UPDATE SET
                    name = excluded.name,
                    template_body = excluded.template_body,
                    updated_at = excluded.updated_at
                """,
                (template_id, request.category, name, body, created_at, now),
            )
        saved = self.get(template_id)
        if saved is None:  # pragma: no cover - defensive guard for an interrupted write
            raise RuntimeError("テンプレートを保存できませんでした。")
        return saved

    def delete(self, template_id: str) -> bool:
        with self._connect() as connection:
            cursor = connection.execute(
                "DELETE FROM post_templates WHERE template_id = ?",
                (template_id,),
            )
        return cursor.rowcount > 0


class InMemoryTemplateStore:
    """Disposable store for the public Vercel Mock deployment.

    Vercel Functions do not provide a durable local filesystem. Keeping this
    small store in memory lets the portfolio demo expose the template flow
    without pretending that user edits are permanently saved.
    """

    def __init__(self) -> None:
        self._templates: dict[str, SavedTemplate] = {}
        self._lock = RLock()

    def list(self, category: Category | None = None) -> list[SavedTemplate]:
        with self._lock:
            templates = [
                template
                for template in self._templates.values()
                if category is None or template.category == category
            ]
            templates.sort(key=lambda template: template.name.casefold())
            templates.sort(key=lambda template: template.updated_at, reverse=True)
            if category is None:
                templates.sort(key=lambda template: str(template.category))
            return templates

    def get(self, template_id: str) -> SavedTemplate | None:
        with self._lock:
            return self._templates.get(template_id)

    def upsert(self, request: TemplateUpsertRequest) -> SavedTemplate:
        name = request.name.strip()
        body = request.template_body.strip()
        template_id = request.template_id or f"saved_{uuid4().hex[:16]}"
        now = _now()
        with self._lock:
            existing = self._templates.get(template_id)
            if existing and existing.category != request.category:
                raise ValueError("テンプレートのカテゴリは変更できません。")
            saved = SavedTemplate(
                template_id=template_id,
                category=request.category,
                name=name,
                template_body=body,
                created_at=existing.created_at if existing else now,
                updated_at=now,
            )
            self._templates[template_id] = saved
            return saved

    def delete(self, template_id: str) -> bool:
        with self._lock:
            return self._templates.pop(template_id, None) is not None


def _build_template_store() -> TemplateStore | InMemoryTemplateStore:
    if os.getenv("PAWPOST_TEMPLATE_STORE_MODE", "").lower() == "memory":
        return InMemoryTemplateStore()
    return TemplateStore()


persistent_template_store = _build_template_store()
