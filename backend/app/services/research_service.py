from typing import Dict, Optional, List
from app.schemas.chat import IntentCategory
from app.schemas.research import OfficialServiceResearch, OfficialLinkItem

OFFICIAL_RESEARCH_DATABASE: Dict[str, OfficialServiceResearch] = {
    IntentCategory.WB_DOMICILE_CERTIFICATE.value: OfficialServiceResearch(
        service_id="wb_domicile_certificate",
        title="West Bengal Domicile Certificate",
        issuing_authority="Kolkata Collectorate (Kolkata district) / District Magistrates & SDOs (all other WB districts)",
        jurisdiction="Government of West Bengal",
        official_portal_url="https://kolkatacollectorate.wb.gov.in/domicile-certificate/",
        alternate_portal_url="https://edistrict.wb.gov.in/PACE/",
        official_form_download_url="https://cdn.s3waas.gov.in/s35487315b1286f907165907aa8fc96619/uploads/2025/09/17587126387607.pdf",
        overview=(
            "The Domicile / Residential Certificate certifies that the applicant is a bona fide permanent resident "
            "of West Bengal. It is mandatory for claiming the 85% state quota in college admissions (WBJEE, NEET, etc.), "
            "state merit scholarships, and state government appointments."
        ),
        required_documents=[
            "Proof of continuous residence in West Bengal for at least 10–15 years (Certificate from local Councillor / Gram Panchayat Pradhan / MLA / MP)",
            "Proof of Date of Birth (Madhyamik Admit Card / Birth Certificate from KMC or registered municipal authority)",
            "Proof of Present Residential Address (Voter ID / Electricity Bill / Telephone Bill in applicant's or parents' name)",
            "Educational verification / Proof of Higher Studies (School Leaving Certificate / College Admission Proof)",
            "Proof of parents' residence or immovable property tax receipt (Khajana / KMC Tax Receipt) if applicable",
            "Two recent passport-sized color photographs",
        ],
        official_links=[
            OfficialLinkItem(
                title="Kolkata Collectorate Domicile Portal",
                url="https://kolkatacollectorate.wb.gov.in/domicile-certificate/",
                description="Official Kolkata Collectorate page for higher studies domicile certificate applications and guidelines",
                link_type="official_portal",
            ),
            OfficialLinkItem(
                title="West Bengal e-District 2.0 Citizen Portal",
                url="https://edistrict.wb.gov.in/PACE/",
                description="Unified citizen service portal for West Bengal district administrative services",
                link_type="state_portal",
            ),
            OfficialLinkItem(
                title="Official Domicile Application Form (Higher Studies)",
                url="https://cdn.s3waas.gov.in/s35487315b1286f907165907aa8fc96619/uploads/2025/09/17587126387607.pdf",
                description="Direct official PDF application form issued by the Kolkata Collectorate",
                link_type="downloadable_form",
            ),
        ],
    ),
    IntentCategory.WB_INCOME_CERTIFICATE.value: OfficialServiceResearch(
        service_id="wb_income_certificate",
        title="West Bengal Income Certificate",
        issuing_authority="Sub-Divisional Officer (SDO) / District Magistrate / BDO",
        jurisdiction="Government of West Bengal",
        official_portal_url="https://edistrict.wb.gov.in/PACE/",
        alternate_portal_url="https://wb.gov.in/",
        official_form_download_url="https://edistrict.wb.gov.in/",
        overview=(
            "An official certificate issued by the SDO or competent revenue authority certifying the annual gross family "
            "income of the applicant from all sources. Essential for availing educational fee concessions, welfare subsidies, "
            "and government scholarships like SVMCM (Swami Vivekananda Merit-cum-Means) and Aikyashree."
        ),
        required_documents=[
            "Salary Slip / Certificate from employer (for salaried persons) OR Income Tax Return (ITR) acknowledgement",
            "Income report / certificate from local Councillor (KMC/Municipality) or Gram Panchayat Pradhan",
            "Proof of Identity (Aadhaar Card / Voter ID Card / PAN Card)",
            "Proof of Residence (Voter Card / Electricity Bill / Ration Card)",
            "Recent passport-sized photograph of the applicant",
        ],
        official_links=[
            OfficialLinkItem(
                title="West Bengal e-District 2.0 Portal",
                url="https://edistrict.wb.gov.in/PACE/",
                description="Official e-District portal for online application and certificate tracking",
                link_type="official_portal",
            ),
            OfficialLinkItem(
                title="Swami Vivekananda Scholarship (SVMCM) Portal",
                url="https://svmcm.wbhed.gov.in/",
                description="Official portal for West Bengal higher education merit-cum-means scholarships",
                link_type="guidance",
            ),
        ],
    ),
    IntentCategory.TRADE_LICENCE.value: OfficialServiceResearch(
        service_id="trade_licence",
        title="Municipal Certificate of Enlistment (Trade Licence)",
        issuing_authority="Kolkata Municipal Corporation (KMC) / Respective Municipal Corporation or Gram Panchayat",
        jurisdiction="West Bengal Municipal & Local Government",
        official_portal_url="https://www.kmcgov.in/",
        alternate_portal_url="https://silpasathi.wb.gov.in/",
        official_form_download_url="https://www.kmcgov.in/KMCPortal/jsp/KMCTradeLicenseHome.jsp",
        overview=(
            "Certificate of Enlistment (CE / Trade Licence) is a mandatory municipal authorization required for any commercial "
            "shop, office, or manufacturing trade establishment operating within urban or rural municipal areas in West Bengal."
        ),
        required_documents=[
            "Proof of occupancy of business premises (Rent Agreement / Rent Bill / Property Tax Receipt / KMC Mutation Certificate)",
            "Consent letter / NOC from the premises owner if the place of business is rented",
            "Identity Proof of proprietor / partners / directors (Aadhaar / Voter ID / PAN)",
            "Fire NOC and Pollution Control Board (WBPCB) clearance for applicable trade categories",
            "Trade name and nature of business activities declaration",
        ],
        official_links=[
            OfficialLinkItem(
                title="Kolkata Municipal Corporation (KMC) Trade Portal",
                url="https://www.kmcgov.in/KMCPortal/jsp/KMCTradeLicenseHome.jsp",
                description="Official portal for new Certificate of Enlistment and online renewal",
                link_type="official_portal",
            ),
            OfficialLinkItem(
                title="Silpa Sathi - West Bengal Single Window Portal",
                url="https://silpasathi.wb.gov.in/",
                description="State-wide single window platform for industrial and commercial municipal clearances",
                link_type="state_portal",
            ),
        ],
    ),
    IntentCategory.FSSAI_REGISTRATION.value: OfficialServiceResearch(
        service_id="fssai_registration",
        title="FSSAI Food Business Registration & Licensing",
        issuing_authority="Food Safety and Standards Authority of India (FSSAI) & State Food Safety Department",
        jurisdiction="Government of India / Government of West Bengal",
        official_portal_url="https://foscos.fssai.gov.in/",
        alternate_portal_url="https://www.fssai.gov.in/",
        official_form_download_url="https://foscos.fssai.gov.in/assets/kbase/User_Manual_for_FoSCoS.pdf",
        overview=(
            "Mandatory 14-digit food safety registration or license issued under the Food Safety and Standards Act, 2006. "
            "Petty food business operators (turnover up to ₹12 Lakhs/year) require Basic Registration (Form A, ₹100/year). "
            "Establishments with turnover between ₹12 Lakhs and ₹20 Crores require a State Licence (Form B)."
        ),
        required_documents=[
            "Photograph of the Food Business Operator (Proprietor / Partner)",
            "Government Photo ID Proof (Aadhaar / Voter ID / PAN / Passport)",
            "Proof of possession of premises (Electricity Bill / Rent Agreement / Property Tax receipt)",
            "List of food categories and products manufactured, stored, or sold",
            "Partnership Deed / Certificate of Incorporation if applicable",
            "Water testing report (for manufacturing / catering units)",
        ],
        official_links=[
            OfficialLinkItem(
                title="FSSAI FoSCoS Official Portal",
                url="https://foscos.fssai.gov.in/",
                description="Official Food Safety Compliance System for applying, tracking, and renewing FSSAI licenses",
                link_type="official_portal",
            ),
            OfficialLinkItem(
                title="FoSCoS Official User Manual & Eligibility Guidelines",
                url="https://foscos.fssai.gov.in/assets/kbase/User_Manual_for_FoSCoS.pdf",
                description="Official statutory handbook outlining fee structures, categories, and step-by-step procedures",
                link_type="downloadable_form",
            ),
        ],
    ),
    IntentCategory.FOOD_BUSINESS_SETUP.value: OfficialServiceResearch(
        service_id="food_business_setup",
        title="Food Business Setup Approvals (Trade Licence + FSSAI)",
        issuing_authority="Local Municipal Corporation / Panchayat & FSSAI",
        jurisdiction="West Bengal & National Compliance",
        official_portal_url="https://silpasathi.wb.gov.in/",
        alternate_portal_url="https://foscos.fssai.gov.in/",
        official_form_download_url="https://www.kmcgov.in/",
        overview=(
            "Opening a commercial food business (bakery, restaurant, cloud kitchen, cafe) in West Bengal requires two primary "
            "statutory approvals: 1) Municipal Certificate of Enlistment (Trade Licence) from KMC/Municipality, and 2) FSSAI Food "
            "Safety Registration/Licence from FoSCoS."
        ),
        required_documents=[
            "Premises occupancy document (Rental Agreement / Property Tax Receipt)",
            "Municipal Trade Licence (Certificate of Enlistment)",
            "FSSAI Registration (for turnover < ₹12L) or State Licence (for turnover > ₹12L)",
            "Fire Safety NOC (for dine-in restaurants or commercial kitchens)",
            "Pollution clearance (WBPCB) for industrial bakeries or commercial kitchens if applicable",
            "Photo ID and address proof of owner",
        ],
        official_links=[
            OfficialLinkItem(
                title="Silpa Sathi Single Window System",
                url="https://silpasathi.wb.gov.in/",
                description="Integrated portal for commercial municipal and business clearances in West Bengal",
                link_type="state_portal",
            ),
            OfficialLinkItem(
                title="FSSAI FoSCoS Portal",
                url="https://foscos.fssai.gov.in/",
                description="Apply for mandatory Food Safety Registration or State Licence",
                link_type="official_portal",
            ),
            OfficialLinkItem(
                title="KMC Trade Licence Portal",
                url="https://www.kmcgov.in/KMCPortal/jsp/KMCTradeLicenseHome.jsp",
                description="Apply for local municipal Certificate of Enlistment in Kolkata",
                link_type="official_portal",
            ),
        ],
    ),
}


class ResearchService:
    """Service providing verified official government portals, resources, and checklists."""

    @staticmethod
    def get_service_research(intent: Optional[IntentCategory | str]) -> Optional[OfficialServiceResearch]:
        if not intent:
            return None
        val = intent.value if isinstance(intent, IntentCategory) else str(intent).lower()
        return OFFICIAL_RESEARCH_DATABASE.get(val)

    @staticmethod
    def format_research_context_for_prompt(intent: Optional[IntentCategory | str]) -> str:
        """Formats verified official research data for injection into Gemini context."""
        research = ResearchService.get_service_research(intent)
        if not research:
            return ""

        docs_list = "\n".join(f"  - {d}" for d in research.required_documents)
        links_list = "\n".join(f"  - [{link.title}]({link.url}): {link.description}" for link in research.official_links)

        return (
            f"\nVERIFIED OFFICIAL GOVERNMENT RESEARCH FOR {research.title.upper()}:\n"
            f"- Issuing Authority: {research.issuing_authority}\n"
            f"- Jurisdiction: {research.jurisdiction}\n"
            f"- Primary Official Portal: {research.official_portal_url}\n"
            f"- Legal Overview: {research.overview}\n"
            f"- Verified Required Documents Checklist:\n{docs_list}\n"
            f"- Official Portal & Resource Links:\n{links_list}\n"
            f"IMPORTANT: Cite these exact official URLs and checklist items when guiding the citizen."
        )


research_service = ResearchService()
