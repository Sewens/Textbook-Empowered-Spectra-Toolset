from pydantic import BaseModel, Field


class TermSource(BaseModel):
    source_id: str
    source_title: str
    page_index: int | None = None
    matched_keyword: str | None = None
    evidence_text: str | None = None
    evidence_quality: str | None = None


class TermItem(BaseModel):
    term_id: str
    category: str
    term_en: str
    term_zh: str
    aliases: list[str] = Field(default_factory=list)
    definition_zh: str | None = None


class TermDetail(TermItem):
    source: TermSource | None = None
    related_groups: list["RelatedGroupRef"] = Field(default_factory=list)


class RelatedGroupRef(BaseModel):
    group_id: str
    name_zh: str
    name_en: str
    match_reason: str | None = None


class TermsListResponse(BaseModel):
    total: int
    items: list[TermItem]