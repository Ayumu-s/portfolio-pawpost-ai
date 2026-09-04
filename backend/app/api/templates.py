from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from ..category_settings import Category
from ..schemas import SavedTemplate, TemplateUpsertRequest
from ..services.template_renderer import TemplateValidationError, validate_template_body
from ..services.template_store import persistent_template_store

router = APIRouter(prefix="/api/templates", tags=["templates"])
template_store = persistent_template_store


@router.get("", response_model=list[SavedTemplate])
async def list_templates(
    category: Annotated[Category | None, Query()] = None,
) -> list[SavedTemplate]:
    return template_store.list(category)


def _validate_request(request: TemplateUpsertRequest) -> None:
    if not request.name.strip():
        raise HTTPException(status_code=422, detail="テンプレート名を入力してください。")
    if not request.template_body.strip():
        raise HTTPException(status_code=422, detail="テンプレート本文を入力してください。")
    try:
        validate_template_body(request.template_body)
    except TemplateValidationError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.post("", response_model=SavedTemplate, status_code=status.HTTP_201_CREATED)
async def save_template(request: TemplateUpsertRequest) -> SavedTemplate:
    _validate_request(request)
    try:
        return template_store.upsert(request)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.put("/{template_id}", response_model=SavedTemplate)
async def update_template(template_id: str, request: TemplateUpsertRequest) -> SavedTemplate:
    if request.template_id and request.template_id != template_id:
        raise HTTPException(status_code=422, detail="テンプレートIDが一致しません。")
    normalized = request.model_copy(update={"template_id": template_id})
    _validate_request(normalized)
    if template_store.get(template_id) is None:
        raise HTTPException(status_code=404, detail="テンプレートが見つかりません。")
    try:
        return template_store.upsert(normalized)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(template_id: str) -> None:
    if not template_store.delete(template_id):
        raise HTTPException(status_code=404, detail="テンプレートが見つかりません。")
