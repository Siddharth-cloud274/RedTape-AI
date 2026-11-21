import os
from typing import Dict, List, Optional
from pydantic import BaseModel


class OfficialTemplateMetadata(BaseModel):
    template_id: str
    service_id: str
    title: str
    issuing_authority: str
    jurisdiction: str
    purpose: str
    source_portal_url: str
    download_url: str
    sha256_hash: str
    page_count: int
    template_type: str  # "static" or "fillable"
    file_path: str
    version: str


TEMPLATE_REGISTRY: Dict[str, OfficialTemplateMetadata] = {
    "kolkata_domicile_higher_studies": OfficialTemplateMetadata(
        template_id="kolkata_domicile_higher_studies",
        service_id="wb_domicile_certificate",
        title="Application for Domicile Certificate (For Higher Studies Purpose)",
        issuing_authority="Kolkata Collectorate, Government of West Bengal",
        jurisdiction="Kolkata Collectorate",
        purpose="Higher Studies",
        source_portal_url="https://kolkatacollectorate.wb.gov.in/domicile-certificate/",
        download_url="https://cdn.s3waas.gov.in/s35487315b1286f907165907aa8fc96619/uploads/2025/09/17587126387607.pdf",
        sha256_hash="ba897eb9bd41b81700cf94dc6489a8d329b6838ef547570b35a6b69843e2317d",
        page_count=3,
        template_type="static",
        file_path=os.path.abspath(
            os.path.join(os.path.dirname(__file__), "official", "kolkata_domicile_higher_studies.pdf")
        ),
        version="2025-09",
    )
}


def get_template(template_id: str) -> Optional[OfficialTemplateMetadata]:
    """Retrieves verified official template metadata by ID."""
    return TEMPLATE_REGISTRY.get(template_id)


def list_templates() -> List[OfficialTemplateMetadata]:
    """Lists all verified official templates."""
    return list(TEMPLATE_REGISTRY.values())
