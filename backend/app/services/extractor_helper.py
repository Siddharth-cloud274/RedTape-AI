import re
from typing import List
from app.schemas.facts import ExtractedFactItem


def extract_heuristic_applicant_facts(text: str) -> List[ExtractedFactItem]:
    """
    Extracts explicit applicant particulars (name, father, DOB, address, duration)
    from natural language citizen messages to ensure no form details are lost.
    """
    facts: List[ExtractedFactItem] = []
    text_clean = text.strip()

    # 1. Applicant Name
    # Matches: "my name is Sourav Mukherjee", "name: Sourav Mukherjee", "I am Sourav Mukherjee"
    name_match = re.search(
        r"(?:my name is|i am|name[:\s]+)\s*([A-Za-z]+(?:\s+[A-Za-z]+){1,3})",
        text_clean,
        re.IGNORECASE,
    )
    if name_match:
        val = name_match.group(1).strip()
        # Avoid common false positives
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
    # Matches: "father is Debabrata Mukherjee", "father's name is Debabrata Mukherjee", "father: Debabrata Mukherjee"
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
    # Matches: "date of birth is 14/05/2003", "dob is 14/05/2003", "dob: 2003-05-14"
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
    # Matches: "present address is 12 Park Street, Kolkata 700016", "address: 12 Park Street..."
    addr_match = re.search(
        r"(?:present address|permanent address|current address|address)(?:\s+is|:)\s*([^.;\n]+(?:,\s*[^.;\n]+)*)",
        text_clean,
        re.IGNORECASE,
    )
    if addr_match:
        val = addr_match.group(1).strip()
        # Clean trailing connectors
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

    return facts
