"""Strict AI output and operator-supplied source contracts. Unknown is not zero."""
import re
from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

PRODUCT_ID_PATTERN = r'^(?:coupang-[0-9]+(?:-[0-9]+){0,2}|manual-[a-z0-9]+(?:-[a-z0-9]+)*)$'


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)


def public_url(value):
    parsed = urlsplit(value)
    if (parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password
            or parsed.port not in (None, 443)):
        raise ValueError('출처/구매 URL은 인증 정보 없는 HTTPS 주소여야 합니다.')
    return value


class Source(StrictModel):
    id: str = Field(pattern=r'^[a-zA-Z0-9_-]{1,80}$')
    kind: Literal['manufacturer', 'label', 'regulator']
    url: str
    title: str = Field(min_length=1, max_length=200)
    text: str = Field(min_length=1, max_length=60000)
    retrievedAt: str = Field(min_length=1, max_length=80)

    _url = field_validator('url')(public_url)


class Evidence(StrictModel):
    sourceId: str
    quote: str = Field(min_length=1, max_length=2000)


class TextFact(StrictModel):
    value: str = Field(min_length=1, max_length=1000)
    evidence: Evidence


class NumberFact(StrictModel):
    value: float = Field(gt=0, le=1e15)
    evidence: Evidence


class Ingredient(StrictModel):
    key: str = Field(pattern=r'^[a-z][a-z0-9_]{0,79}$',
                     description='Unique substance identifier, not a category ID. Never repeat a key within ingredients.')
    name: str = Field(min_length=1, max_length=150)
    amount: float | None = Field(ge=0, le=1e15)
    unit: Literal['mg', 'mcg', 'g', 'IU', 'CFU', 'mL', 'mcg RAE', 'mg α-TE', 'mcg DFE', 'mg NE'] | None
    basis: Literal['per_serving', 'per_unit', 'per_daily', 'unknown']
    form: str | None
    # Parents and children must not be summed: e.g. fish oil contains EPA/DHA.
    partOf: str | None
    evidence: Evidence

    @model_validator(mode='after')
    def consistent_amount(self):
        if (self.amount is None) != (self.unit is None):
            raise ValueError('함량과 단위는 함께 제공하거나 함께 null이어야 합니다.')
        return self


class Claim(StrictModel):
    text: str = Field(min_length=1, max_length=500)
    effectId: Literal['immunity', 'energy-vitality', 'eye-health', 'digestive-health',
                      'sleep-stress', 'skin-health', 'weight', 'bone-joint'] | None
    ingredientKeys: list[str]
    evidence: Evidence


class AgeGroup(StrictModel):
    id: Literal['kids', 'teens', '20s', '30s-40s', '50s-60s', '70-plus']
    evidence: Evidence


class Analysis(StrictModel):
    productIdentity: TextFact
    brand: TextFact | None
    serving: TextFact | None
    unitsPerServing: NumberFact | None
    dailyServings: NumberFact | None
    # Full formula mass PER SERVING, never fish oil subtotal, bottle or %DV.
    totalContentMg: NumberFact | None
    pillSizeMm: NumberFact | None
    formulation: TextFact | None
    ingredients: list[Ingredient] = Field(max_length=80)
    claims: list[Claim] = Field(max_length=15)
    warnings: list[TextFact] = Field(max_length=20)
    audience: list[TextFact] = Field(max_length=10)
    ageGroups: list[AgeGroup] = Field(max_length=5)
    summary: str = Field(max_length=1500)
    unknowns: list[str] = Field(max_length=20)

    @model_validator(mode='after')
    def consistent_ingredients(self):
        keys = [i.key for i in self.ingredients]
        if len(keys) != len(set(keys)):
            raise ValueError('중복 성분 키: 같은 성분의 함량 기준을 먼저 통일하세요.')
        for ingredient in self.ingredients:
            visited, parent = {ingredient.key}, ingredient.partOf
            while parent is not None:
                if parent not in keys or parent in visited:
                    raise ValueError('성분 포함 관계가 유효하지 않습니다.')
                visited.add(parent)
                parent = next(i.partOf for i in self.ingredients if i.key == parent)
        if any(set(c.ingredientKeys) - set(keys) for c in self.claims):
            raise ValueError('기능성의 성분 연결이 유효하지 않습니다.')
        if (self.unitsPerServing or self.dailyServings or self.totalContentMg) and not self.serving:
            raise ValueError('섭취 개수/횟수/전체 중량에는 1회 섭취 기준이 필요합니다.')
        if any(i.basis == 'per_serving' and i.amount is not None for i in self.ingredients) and not self.serving:
            raise ValueError('1회 섭취량 기준의 함량에는 섭취량 원문이 필요합니다.')
        return self


def normalized_text(text):
    return re.sub(r'\s+', ' ', text).strip()


def validate_evidence(analysis, sources):
    """Reject invented citations; semantic/product/dose checks still need review."""
    by_id = {source.id: normalized_text(source.text) for source in sources}
    if len(by_id) != len(sources):
        raise ValueError('출처 ID가 중복됩니다.')

    def visit(value):
        if isinstance(value, dict):
            if set(value) == {'sourceId', 'quote'}:
                quote = normalized_text(value['quote'])
                if not quote or quote not in by_id.get(value['sourceId'], ''):
                    raise ValueError('AI 근거 문장이 원문에 없습니다.')
            else:
                for nested in value.values():
                    visit(nested)
        elif isinstance(value, list):
            for nested in value:
                visit(nested)
    visit(analysis.model_dump())


class SourceSpec(StrictModel):
    id: str = Field(pattern=r'^[a-zA-Z0-9_-]{1,80}$')
    kind: Literal['manufacturer', 'label', 'regulator']
    url: str
    title: str = Field(min_length=1, max_length=200)
    # Null requests a permitted manufacturer HTML fetch. Text can be a label transcription.
    text: str | None = Field(min_length=1, max_length=60000)

    _url = field_validator('url')(public_url)


class SourceBundle(StrictModel):
    productId: str = Field(pattern=PRODUCT_ID_PATTERN, max_length=160)
    expectedProductName: str = Field(min_length=1, max_length=500)
    # Exact variant/market must be checked by the operator who supplies the mapping.
    variantNote: str = Field(min_length=1, max_length=1000)
    sources: list[SourceSpec] = Field(min_length=1, max_length=8)

    @field_validator('sources')
    @classmethod
    def unique_sources(cls, sources):
        if len({s.id for s in sources}) != len(sources):
            raise ValueError('제품 내 출처 ID가 중복됩니다.')
        return sources


class ManualProduct(StrictModel):
    """A real product and its sources supplied locally, independent of a shopping API."""
    id: str = Field(pattern=r'^manual-[a-z0-9]+(?:-[a-z0-9]+)*$', max_length=160)
    product: str = Field(min_length=1, max_length=500)
    productUrl: str
    buyLink: str | None = None
    variantNote: str = Field(min_length=1, max_length=1000)
    sources: list[SourceSpec] = Field(min_length=1, max_length=8)

    @field_validator('productUrl', 'buyLink')
    @classmethod
    def safe_url(cls, value):
        return public_url(value) if value is not None else None

    @field_validator('product', 'variantNote')
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError('제품명과 버전 설명은 비어 있을 수 없습니다.')
        return value.strip()

    def source_bundle(self):
        return SourceBundle(productId=self.id, expectedProductName=self.product,
                            variantNote=self.variantNote, sources=self.sources)

    @model_validator(mode='after')
    def valid_bundle(self):
        self.source_bundle()
        return self
