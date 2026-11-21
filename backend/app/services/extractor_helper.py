import re
from typing import Dict, List, Optional
from app.schemas.facts import ExtractedFactItem


def extract_heuristic_applicant_facts(
    text: str,
    target_field: Optional[str] = None,
    confirmed_facts: Optional[Dict[str, str]] = None,
) -> List[ExtractedFactItem]:
    """
    Extracts explicit applicant particulars (name, father, DOB, address, duration, location, purpose)
    from natural language citizen messages, taking into account the currently targeted question.
    """
    facts: List[ExtractedFactItem] = []
    text_clean = text.strip()
    if not text_clean:
        return facts

    # 1. Applicant Name
    name_match = re.search(
        r"(?:my name is|i am|name[:\s]+)\s*([A-Za-z]+(?:\s+[A-Za-z]+){1,3})",
        text_clean,
        re.IGNORECASE,
    )
    if name_match:
        val = name_match.group(1).strip()
        if val.lower() not in ["applying", "looking", "interested", "a student", "an applicant"]:
            facts.append(
                ExtractedFactItem(
                    field_name="applicant_name",
                    field_value=val,
                    evidence=name_match.group(0),
                    is_correction=False,
                )
            )

    # 2. Father's Name
    father_match = re.search(
        r"(?:father(?:'s)?(?:\s+name)?(?:\s+is|:))\s*([A-Za-z]+(?:\s+[A-Za-z]+){1,3})",
        text_clean,
        re.IGNORECASE,
    )
    if father_match:
        val = father_match.group(1).strip()
        facts.append(
            ExtractedFactItem(
                field_name="father_name",
                field_value=val,
                evidence=father_match.group(0),
                is_correction=False,
            )
        )

    # 3. Date of Birth
    dob_match = re.search(
        r"(?:date of birth|dob|birth\s*date)(?:\s+is|:)?\s*([0-9]{1,4}[\/\-\.][0-9]{1,2}[\/\-\.][0-9]{1,4})",
        text_clean,
        re.IGNORECASE,
    )
    if dob_match:
        val = dob_match.group(1).strip()
        facts.append(
            ExtractedFactItem(
                field_name="date_of_birth",
                field_value=val,
                evidence=dob_match.group(0),
                is_correction=False,
            )
        )

    # 4. Present Address
    addr_match = re.search(
        r"(?:present address|permanent address|current address|address)(?:\s+is|:)\s*([^.;\n]+(?:,\s*[^.;\n]+)*)",
        text_clean,
        re.IGNORECASE,
    )
    if addr_match:
        val = addr_match.group(1).strip()
        val = re.sub(r"\s+(?:and|my|father|dob|date of birth)\b.*$", "", val, flags=re.IGNORECASE).strip()
        if len(val) > 4:
            facts.append(
                ExtractedFactItem(
                    field_name="present_address",
                    field_value=val,
                    evidence=addr_match.group(0),
                    is_correction=False,
                )
            )

    # 5. Stay Duration
    stay_match = re.search(
        r"([0-9]+\s*years?)\s*(?:in\s*(?:west\s*bengal|wb|kolkata)|of\s*stay|stay)",
        text_clean,
        re.IGNORECASE,
    )
    if stay_match:
        val = stay_match.group(1).strip()
        facts.append(
            ExtractedFactItem(
                field_name="stay_duration",
                field_value=val,
                evidence=stay_match.group(0),
                is_correction=False,
            )
        )

    # 6. Location / District
    loc_match = re.search(
        r"\b(kolkata|calcutta|salt lake|alipore|bowbazar|tollygunge|howrah|barrackpore|asansol|siliguri|darjeeling|durgapur|burdwan|bardhaman|malda|murshidabad|nadia|hooghly|medinipur)\b",
        text_clean,
        re.IGNORECASE,
    )
    if loc_match:
        val = loc_match.group(1).title()
        facts.append(
            ExtractedFactItem(
                field_name="location",
                field_value=val,
                evidence=loc_match.group(0),
                is_correction=False,
            )
        )

    # 7. Purpose
    purpose_match = re.search(
        r"\b(higher studies|college admission|university admission|scholarship|employment|job application|admission)\b",
        text_clean,
        re.IGNORECASE,
    )
    if purpose_match:
        val = purpose_match.group(1).title()
        facts.append(
            ExtractedFactItem(
                field_name="application_purpose",
                field_value=val,
                evidence=purpose_match.group(0),
                is_correction=False,
            )
        )

    # 8. Single-Answer Direct Response to Interview Question (Context-Aware)
    already_extracted_names = {f.field_name for f in facts}
    if target_field and target_field not in already_extracted_names:
        is_intent_prompt = any(
            kw in text_clean.lower()
            for kw in ["need", "want", "certificate", "licence", "license", "help", "how to", "apply", "give me"]
        )
        if not is_intent_prompt:
            val = text_clean.strip(" .;")
            if target_field == "applicant_name":
                if re.match(r"^[A-Za-z]+(?:\s+[A-Za-z]+){1,3}$", val):
                    facts.append(ExtractedFactItem(field_name="applicant_name", field_value=val, evidence=val))
            elif target_field == "father_name":
                if re.match(r"^[A-Za-z]+(?:\s+[A-Za-z]+){1,3}$", val):
                    facts.append(ExtractedFactItem(field_name="father_name", field_value=val, evidence=val))
            elif target_field == "date_of_birth":
                if re.match(r"^[0-9]{1,4}[\/\-\.][0-9]{1,2}[\/\-\.][0-9]{1,4}$", val):
                    facts.append(ExtractedFactItem(field_name="date_of_birth", field_value=val, evidence=val))
            elif target_field in ["present_address", "residence_location"]:
                if len(val) >= 5:
                    facts.append(ExtractedFactItem(field_name="present_address", field_value=val, evidence=val))
            elif target_field in ["location", "business_location"]:
                if len(val) >= 3 and len(val) <= 40:
                    facts.append(ExtractedFactItem(field_name=target_field, field_value=val, evidence=val))
            elif target_field == "application_purpose":
                if len(val) >= 3:
                    facts.append(ExtractedFactItem(field_name="application_purpose", field_value=val, evidence=val))
            elif target_field == "business_type":
                if len(val) >= 3:
                    facts.append(ExtractedFactItem(field_name="business_type", field_value=val, evidence=val))
            elif target_field == "stay_duration":
                if re.search(r"[0-9]+", val):
                    facts.append(ExtractedFactItem(field_name="stay_duration", field_value=val, evidence=val))

    return facts
