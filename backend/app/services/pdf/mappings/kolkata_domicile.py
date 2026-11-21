"""Coordinate mappings for Kolkata Collectorate Domicile Certificate (Higher Studies).

Dimensions: 612.0 pt x 792.0 pt (US Letter Portrait)
Template Type: Static PDF (Non-fillable AcroForm)
Coordinates format: (x0, y0, x1, y1) in points from top-left origin.
"""

from typing import Dict, Any

KOLKATA_DOMICILE_FIELD_MAP: Dict[str, Dict[str, Any]] = {
    # Page 1 (index 0)
    "purpose": {
        "page": 0,
        "rect": (120, 240, 515, 260),
        "aliases": ["application_purpose", "goal"],
        "default": "Higher Studies",
        "font_size": 10,
        "is_multiline": False,
        "align": 0,  # 0=left
    },
    "applicant_name": {
        "page": 0,
        "rect": (250, 370, 515, 390),
        "aliases": ["name", "full_name", "citizen_name"],
        "font_size": 10,
        "is_multiline": False,
        "align": 0,
    },
    "father_name": {
        "page": 0,
        "rect": (220, 395, 515, 415),
        "aliases": ["parent_name", "guardian_name", "father"],
        "font_size": 10,
        "is_multiline": False,
        "align": 0,
    },
    "father_occupation": {
        "page": 0,
        "rect": (250, 420, 515, 440),
        "aliases": ["parent_occupation"],
        "font_size": 10,
        "is_multiline": False,
        "align": 0,
    },
    "date_of_birth": {
        "page": 0,
        "rect": (200, 445, 515, 465),
        "aliases": ["dob", "birth_date", "birthdate"],
        "font_size": 10,
        "is_multiline": False,
        "align": 0,
    },
    "place_of_birth": {
        "page": 0,
        "rect": (200, 470, 515, 490),
        "aliases": ["birth_place"],
        "font_size": 10,
        "is_multiline": False,
        "align": 0,
    },
    "present_address": {
        "page": 0,
        "rect": (220, 580, 515, 655),
        "aliases": [
            "address",
            "current_address",
            "residential_address",
            "residence_location",
            "residence",
            "residential_location",
        ],
        "font_size": 9.5,
        "is_multiline": True,
        "align": 0,
    },
    "permanent_address": {
        "page": 0,
        "rect": (240, 680, 515, 755),
        "aliases": ["domicile_address"],
        "font_size": 9.5,
        "is_multiline": True,
        "align": 0,
    },

    # Page 2 (index 1)
    "stay_duration": {
        "page": 1,
        "rect": (280, 300, 515, 320),
        "aliases": ["stay_years", "duration_of_stay", "years_in_state"],
        "font_size": 10,
        "is_multiline": False,
        "align": 0,
    },
    "immovable_property": {
        "page": 1,
        "rect": (310, 528, 515, 548),
        "aliases": ["property_details"],
        "default": "N/A",
        "font_size": 10,
        "is_multiline": False,
        "align": 0,
    },
    "applicant_occupation": {
        "page": 1,
        "rect": (200, 566, 515, 586),
        "aliases": ["occupation", "applicant_status"],
        "default": "Student",
        "font_size": 10,
        "is_multiline": False,
        "align": 0,
    },
    "other_info": {
        "page": 1,
        "rect": (260, 585, 515, 605),
        "aliases": ["remarks", "additional_info"],
        "default": "Nil",
        "font_size": 10,
        "is_multiline": False,
        "align": 0,
    },
    "date": {
        "page": 1,
        "rect": (145, 626, 250, 646),
        "aliases": ["application_date", "current_date"],
        "font_size": 10,
        "is_multiline": False,
        "align": 0,
    },
    "place": {
        "page": 1,
        "rect": (145, 651, 250, 671),
        "aliases": ["location", "submission_place"],
        "default": "Kolkata",
        "font_size": 10,
        "is_multiline": False,
        "align": 0,
    },
    "contact_number": {
        "page": 1,
        "rect": (210, 676, 350, 696),
        "aliases": ["phone", "mobile", "mobile_number"],
        "font_size": 10,
        "is_multiline": False,
        "align": 0,
    },
}

REQUIRED_FIELDS = [
    "applicant_name",
    "father_name",
    "date_of_birth",
    "present_address",
]
