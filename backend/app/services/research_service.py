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

PROBABLE_RESEARCH_DATABASE: Dict[str, OfficialServiceResearch] = {
    "passport_services": OfficialServiceResearch(
        service_id="passport_services",
        title="Indian Passport Services (Tatkaal / Normal / Renewal)",
        issuing_authority="Consular, Passport & Visa Division, Ministry of External Affairs",
        jurisdiction="Government of India",
        official_portal_url="https://www.passportindia.gov.in/",
        alternate_portal_url="https://services.india.gov.in/",
        overview=(
            "Official passport issuance and renewal services under the Passports Act, 1967. "
            "Applications, payments, and appointments are scheduled online via Passport Seva Kendras (PSK / POPSK)."
        ),
        is_verified=False,
        verification_badge="Probable Official Guidance",
        disclaimer="Probable official portal link. Please check appointment availability and document guidelines on passportindia.gov.in.",
        required_documents=[
            "Proof of Date of Birth (Birth Certificate, Madhyamik/10th Admit Card, or Transfer Certificate)",
            "Proof of Present Address (Aadhaar Card, Electricity Bill, Bank Passbook, or Voter ID)",
            "Standard Government Photo ID (Aadhaar, Voter ID, PAN)",
            "Previous Passport booklet (for re-issue / renewal applications)",
        ],
        official_links=[
            OfficialLinkItem(
                title="Passport Seva Portal",
                url="https://www.passportindia.gov.in/",
                description="Official Ministry of External Affairs portal for passport application, fee payment, and appointment booking",
                link_type="official_portal",
            ),
        ],
    ),
    "driving_licence": OfficialServiceResearch(
        service_id="driving_licence",
        title="Driving Licence & Learner Licence (Sarathi Parivahan)",
        issuing_authority="Regional Transport Office (RTO) / Ministry of Road Transport and Highways (MoRTH)",
        jurisdiction="Government of India & State Transport Departments",
        official_portal_url="https://parivahan.gov.in/",
        alternate_portal_url="https://sarathi.parivahan.gov.in/",
        overview=(
            "Motor vehicle driving licences (Learner, Permanent, Commercial, Renewal) are administered "
            "under the Motor Vehicles Act, 1988 via the unified Parivahan Sarathi platform."
        ),
        is_verified=False,
        verification_badge="Probable Official Guidance",
        disclaimer="Probable official portal link. Slot booking, test procedures, and fee payments vary by state RTO.",
        required_documents=[
            "Proof of Age (Madhyamik Certificate, Birth Certificate, or Passport)",
            "Proof of Residential Address (Voter ID, Electricity Bill, Aadhaar Card, or Rent Agreement)",
            "Form 1 Physical Fitness Declaration (and Form 1A Medical Certificate for applicants above 40 years)",
            "Valid Learner's Licence (for permanent driving licence tests)",
        ],
        official_links=[
            OfficialLinkItem(
                title="Parivahan Sewa Official Portal",
                url="https://parivahan.gov.in/",
                description="Unified national portal for driving licence services, vehicle registration (Vahan), and slot booking",
                link_type="official_portal",
            ),
        ],
    ),
    "pan_card": OfficialServiceResearch(
        service_id="pan_card",
        title="Permanent Account Number (PAN Card)",
        issuing_authority="Income Tax Department, Ministry of Finance (via Protean NSDL / UTIITSL)",
        jurisdiction="Government of India",
        official_portal_url="https://www.incometax.gov.in/",
        alternate_portal_url="https://www.onlineservices.nsdl.com/paam/endUserRegisterContact.html",
        overview=(
            "Ten-digit alphanumeric identifier issued by the Income Tax Department under the Income Tax Act, 1961 "
            "for financial identification and tax compliance."
        ),
        is_verified=False,
        verification_badge="Probable Official Guidance",
        disclaimer="Probable official portal link. Use authorized e-Filing or Protean NSDL portals to avoid unauthorized third-party fees.",
        required_documents=[
            "Proof of Identity (Aadhaar Card, Voter ID, Passport, or Driving Licence)",
            "Proof of Address (Aadhaar Card, Utility Bill, or Bank Account Statement)",
            "Proof of Date of Birth (Birth Certificate, Matriculation Certificate, or Passport)",
        ],
        official_links=[
            OfficialLinkItem(
                title="Income Tax e-Filing Portal (Instant e-PAN)",
                url="https://www.incometax.gov.in/",
                description="Apply for instant paperless e-PAN using Aadhaar e-KYC",
                link_type="official_portal",
            ),
            OfficialLinkItem(
                title="Protean NSDL PAN Application Portal",
                url="https://www.onlineservices.nsdl.com/paam/endUserRegisterContact.html",
                description="Authorized official portal for new PAN (Form 49A) and corrections",
                link_type="official_portal",
            ),
        ],
    ),
    "voter_id": OfficialServiceResearch(
        service_id="voter_id",
        title="Voter ID Card (Election Photo Identity Card - EPIC)",
        issuing_authority="Election Commission of India (ECI) / Chief Electoral Officers",
        jurisdiction="Government of India",
        official_portal_url="https://voters.eci.gov.in/",
        overview=(
            "Electoral registration and voter identity card issuance under the Representation of the People Act, 1950. "
            "Eligible Indian citizens aged 18+ can apply via Form 6."
        ),
        is_verified=False,
        verification_badge="Probable Official Guidance",
        disclaimer="Probable official portal link. Electoral rolls are finalized by the local Electoral Registration Officer (ERO).",
        required_documents=[
            "Proof of Age (Birth Certificate, Aadhaar, PAN, or Passport)",
            "Proof of Ordinary Residence (Electricity Bill, Water Bill, Aadhaar, or Bank Passbook)",
            "One recent color passport photograph (4.5 cm x 3.5 cm)",
        ],
        official_links=[
            OfficialLinkItem(
                title="Election Commission Voters Portal",
                url="https://voters.eci.gov.in/",
                description="Official ECI portal for new voter registration (Form 6), address shifting (Form 8), and EPIC download",
                link_type="official_portal",
            ),
        ],
    ),
    "aadhaar_services": OfficialServiceResearch(
        service_id="aadhaar_services",
        title="Aadhaar Services (Enrollment, Update & PVC Card)",
        issuing_authority="Unique Identification Authority of India (UIDAI)",
        jurisdiction="Government of India",
        official_portal_url="https://myaadhaar.uidai.gov.in/",
        overview=(
            "12-digit unique identity number issued by UIDAI under the Aadhaar Act, 2016 based on biometric and demographic information."
        ),
        is_verified=False,
        verification_badge="Probable Official Guidance",
        disclaimer="Probable official portal link. Biometric updates require visiting an authorized Aadhaar Seva Kendra (ASK).",
        required_documents=[
            "Valid Proof of Identity (POI) from UIDAI approved list (Voter ID, Passport, PAN)",
            "Valid Proof of Address (POA) from UIDAI approved list (Utility bill, Rent agreement, Bank statement)",
            "Date of Birth proof (for initial enrollment or DOB correction)",
        ],
        official_links=[
            OfficialLinkItem(
                title="myAadhaar Citizen Portal",
                url="https://myaadhaar.uidai.gov.in/",
                description="Official UIDAI portal to check status, order Aadhaar PVC, and update demographic details",
                link_type="official_portal",
            ),
        ],
    ),
    "caste_certificate": OfficialServiceResearch(
        service_id="caste_certificate",
        title="Caste Certificate (SC / ST / OBC Certificate)",
        issuing_authority="Sub-Divisional Officer (SDO) / District Magistrate / Backward Classes Welfare Department",
        jurisdiction="State Government & Central Welfare Directory",
        official_portal_url="https://castcertificatewb.gov.in/",
        alternate_portal_url="https://services.india.gov.in/",
        overview=(
            "Official certificate verifying membership in a recognized Scheduled Caste, Scheduled Tribe, or Other Backward Class."
        ),
        is_verified=False,
        verification_badge="Probable Official Guidance",
        disclaimer="Probable official portal link. State rules and documentary proof of lineage are verified by local revenue authorities.",
        required_documents=[
            "Proof of paternal lineage (blood relation certificate of father/uncle or genealogy tree)",
            "Proof of residence in the state (Ration card, Land deed / Porcha, or Voter ID)",
            "Proof of citizenship (Voter ID of applicant/parents, Aadhaar card)",
            "Two passport-sized photographs",
        ],
        official_links=[
            OfficialLinkItem(
                title="West Bengal Caste Certificate Portal",
                url="https://castcertificatewb.gov.in/",
                description="Official portal for SC/ST/OBC certificate online application and status tracking",
                link_type="official_portal",
            ),
            OfficialLinkItem(
                title="National Government Services Portal",
                url="https://services.india.gov.in/",
                description="Central services directory for other Indian states",
                link_type="state_portal",
            ),
        ],
    ),
    "birth_death_certificate": OfficialServiceResearch(
        service_id="birth_death_certificate",
        title="Birth & Death Registration (Civil Registration System)",
        issuing_authority="Registrar of Births & Deaths / Local Municipal Authority",
        jurisdiction="Government of India & State Municipal Authorities",
        official_portal_url="https://crsorgi.gov.in/",
        alternate_portal_url="https://janma-mrityutathya.wb.gov.in/",
        overview=(
            "Mandatory civil registration of vital events under the Registration of Births and Deaths Act, 1969."
        ),
        is_verified=False,
        verification_badge="Probable Official Guidance",
        disclaimer="Probable official portal link. Vital events must be registered within 21 days with the local registrar.",
        required_documents=[
            "Institutional Birth/Death Discharge slip or report from hospital",
            "Identity and address proof of parents or informant (Aadhaar / Voter ID)",
            "Marriage certificate of parents (for birth registration) if requested",
        ],
        official_links=[
            OfficialLinkItem(
                title="Civil Registration System (CRS) India",
                url="https://crsorgi.gov.in/",
                description="Central CRS portal for online birth and death registration across Indian states",
                link_type="official_portal",
            ),
        ],
    ),
}


class ResearchService:
    """Service providing verified official government portals, resources, and checklists."""

    @staticmethod
    def get_service_research(
        intent: Optional[IntentCategory | str],
        query: Optional[str] = None,
    ) -> Optional[OfficialServiceResearch]:
        if intent:
            val = intent.value if isinstance(intent, IntentCategory) else str(intent).lower()
            # 1. Check verified database
            if val in OFFICIAL_RESEARCH_DATABASE:
                return OFFICIAL_RESEARCH_DATABASE[val]
            # 2. Check probable database
            if val in PROBABLE_RESEARCH_DATABASE:
                return PROBABLE_RESEARCH_DATABASE[val]

        # 3. Keyword check on query if available
        if query:
            q_lower = query.lower()
            if "passport" in q_lower:
                return PROBABLE_RESEARCH_DATABASE["passport_services"]
            elif "driving" in q_lower or "licence" in q_lower and "trade" not in q_lower:
                return PROBABLE_RESEARCH_DATABASE["driving_licence"]
            elif "pan" in q_lower or "pan card" in q_lower:
                return PROBABLE_RESEARCH_DATABASE["pan_card"]
            elif "voter" in q_lower or "epic" in q_lower:
                return PROBABLE_RESEARCH_DATABASE["voter_id"]
            elif "aadhaar" in q_lower or "aadhar" in q_lower:
                return PROBABLE_RESEARCH_DATABASE["aadhaar_services"]
            elif "caste" in q_lower or "sc certificate" in q_lower or "obc" in q_lower:
                return PROBABLE_RESEARCH_DATABASE["caste_certificate"]
            elif "birth certificate" in q_lower or "death certificate" in q_lower:
                return PROBABLE_RESEARCH_DATABASE["birth_death_certificate"]

            # 4. Open-to-all universal civic fallback
            words = [w for w in ["certificate", "licence", "license", "registration", "scheme", "apply", "card", "yojana", "portal"] if w in q_lower]
            if words:
                return OfficialServiceResearch(
                    service_id="general_service",
                    title="National Government Citizen Services",
                    issuing_authority="Competent Central / State Ministry or Department",
                    jurisdiction="Government of India / State Government",
                    official_portal_url="https://services.india.gov.in/",
                    overview=(
                        "Unified citizen services directory facilitating online access to government services, "
                        "welfare schemes, and civic applications across all Indian states and Union Territories."
                    ),
                    is_verified=False,
                    verification_badge="Probable Official Guidance",
                    disclaimer="Probable official portal link from the National Services Directory. Please confirm state-specific requirements.",
                    required_documents=[
                        "Standard Government Photo ID (Aadhaar, Voter ID, or PAN)",
                        "Proof of Residential Address (Utility Bill, Voter ID, or Ration Card)",
                        "Prescribed Application Form or Online Registration Acknowledgement",
                        "Passport-sized photograph and fee payment receipt (if applicable)",
                    ],
                    official_links=[
                        OfficialLinkItem(
                            title="National Government Services Portal of India",
                            url="https://services.india.gov.in/",
                            description="Official Government of India portal connecting citizens to 14,000+ state and central services",
                            link_type="official_portal",
                        ),
                        OfficialLinkItem(
                            title="Digital India Citizen Services",
                            url="https://www.digitalindia.gov.in/",
                            description="National digital public infrastructure portal for citizen services",
                            link_type="state_portal",
                        ),
                    ],
                )

        return None

    @staticmethod
    def format_research_context_for_prompt(intent: Optional[IntentCategory | str], query: Optional[str] = None) -> str:
        """Formats verified official research data for injection into Gemini context."""
        research = ResearchService.get_service_research(intent, query)
        if not research:
            return ""

        docs_list = "\n".join(f"  - {d}" for d in research.required_documents)
        links_list = "\n".join(f"  - [{link.title}]({link.url}): {link.description}" for link in research.official_links)
        verified_status = "VERIFIED OFFICIAL" if research.is_verified else "PROBABLE / GENERAL GUIDANCE"

        checklist_label = "Verified Required Documents Checklist" if research.is_verified else "Typical Supporting Documents Checklist"

        return (
            f"\nGOVERNMENT RESEARCH FOR {research.title.upper()} ({verified_status}):\n"
            f"- Issuing Authority: {research.issuing_authority}\n"
            f"- Jurisdiction: {research.jurisdiction}\n"
            f"- Primary Portal: {research.official_portal_url}\n"
            f"- Legal Overview: {research.overview}\n"
            f"- {checklist_label}:\n{docs_list}\n"
            f"- Portal & Resource Links:\n{links_list}\n"
            f"NOTE: If this service is PROBABLE, clarify that it is probable official guidance."
        )


research_service = ResearchService()
