from typing import List, Optional
from pydantic import BaseModel, Field


class OfficialLinkItem(BaseModel):
    title: str = Field(..., description="Display title for the official link")
    url: str = Field(..., description="Absolute URL to the official government portal or document")
    description: Optional[str] = Field(None, description="Short context on what can be done at this link")
    link_type: str = Field("official_portal", description="Type: official_portal, downloadable_form, guidance")


class OfficialServiceResearch(BaseModel):
    service_id: str = Field(..., description="Standardized service identifier")
    title: str = Field(..., description="Official title of the administrative service")
    issuing_authority: str = Field(..., description="Designated issuing authority")
    jurisdiction: str = Field(..., description="Applicable administrative jurisdiction")
    official_portal_url: str = Field(..., description="Primary official government portal")
    alternate_portal_url: Optional[str] = Field(None, description="State-wide or fallback portal")
    official_form_download_url: Optional[str] = Field(None, description="Direct download URL for official form PDF")
    overview: str = Field(..., description="Overview and purpose of the certificate or permit")
    required_documents: List[str] = Field(default_factory=list, description="Checklist of supporting documents")
    official_links: List[OfficialLinkItem] = Field(default_factory=list, description="Official resources and portal links")
    is_verified: bool = Field(default=True, description="True for verified official templates, False for probable guidance")
    verification_badge: str = Field(default="Verified Official", description="Badge text: 'Verified Official' or 'Probable Official Guidance'")
    disclaimer: Optional[str] = Field(default=None, description="Disclaimer or warning note for probable/unverified links")
