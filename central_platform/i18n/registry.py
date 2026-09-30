"""Gayatri AI Platform — Translation Registry & i18n Subsystem (Phase 33).

Provides authoritative translation resolution, English fallback logic,
user language preference management, and AI prompt language instructions.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional


class LanguageCode(str, Enum):
    EN = "en"  # English (Default)
    HI = "hi"  # Hindi (हिन्दी)
    SA = "sa"  # Sanskrit (संस्कृतम्)
    TA = "ta"  # Tamil (தமிழ்)
    TE = "te"  # Telugu (తెలుగు)
    KN = "kn"  # Kannada (ಕನ್ನಡ)
    MR = "mr"  # Marathi (मराठी)
    BN = "bn"  # Bengali (বাংলা)


# ── Translation Dictionaries ──────────────────────────────────────────────────

TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "en": {
        "app_title": "Gayatri AI Platform",
        "welcome": "Welcome back, {name}",
        "dashboard": "Dashboard",
        "curriculum": "Curriculum",
        "learning_graph": "Learning Graph",
        "progress": "Progress",
        "review_queue": "Review Queue",
        "assignments": "Assignments",
        "assessments": "Assessments",
        "activity": "Activity",
        "profile": "Profile",
        "notifications": "Notifications",
        "class_overview": "Class Overview",
        "students": "Students",
        "learning_health": "Learning Health",
        "interventions": "Interventions",
        "teacher_instructions": "Teacher Instructions",
        "ai_copilot": "AI Copilot",
        "child_progress": "Child Progress",
        "attendance": "Attendance",
        "teacher_updates": "Teacher Updates",
        "recommendations": "Recommendations",
        "fees": "Fees & Payments",
        "fee_setup": "Fee Setup",
        "monthly_billing": "Monthly Billing",
        "student_accounts": "Student Fee Accounts",
        "record_payment": "Record Payment",
        "receipts": "Receipts Ledger",
        "outstanding_reports": "Outstanding Reports",
        "search_placeholder": "Search topics, concepts, or courses...",
        "ask_tutor_placeholder": "Ask Gayatri AI tutor a question...",
        "language_selector": "Select Language",
        "theme_toggle": "Toggle Theme",
        "logout": "Log Out",
    },
    "hi": {
        "app_title": "गायत्री एआई प्लेटफॉर्म",
        "welcome": "पुनः स्वागत है, {name}",
        "dashboard": "डैशबोर्ड",
        "curriculum": "पाठ्यक्रम",
        "learning_graph": "शिक्षण ग्राफ",
        "progress": "प्रगति",
        "review_queue": "समीक्षा कतार",
        "assignments": "असाइनमेंट",
        "assessments": "मूल्यांकन",
        "activity": "गतिविधि",
        "profile": "प्रोफ़ाइल",
        "notifications": "सूचनाएं",
        "class_overview": "कक्षा अवलोकन",
        "students": "छात्र",
        "learning_health": "शिक्षण स्वास्थ्य",
        "interventions": "हस्तक्षेप",
        "teacher_instructions": "शिक्षक निर्देश",
        "ai_copilot": "एआई सह-पायलट",
        "child_progress": "बच्चे की प्रगति",
        "attendance": "उपस्थिति",
        "teacher_updates": "शिक्षक अपडेट",
        "recommendations": "सिफारिशें",
        "fees": "शुल्क और भुगतान",
        "fee_setup": "शुल्क व्यवस्था",
        "monthly_billing": "मासिक बिलिंग",
        "student_accounts": "छात्र शुल्क खाते",
        "record_payment": "भुगतान दर्ज करें",
        "receipts": "रसीद खाता",
        "outstanding_reports": "बकाया रिपोर्ट",
        "search_placeholder": "विषय, अवधारणाएं या पाठ्यक्रम खोजें...",
        "ask_tutor_placeholder": "गायत्री एआई ट्यूटर से प्रश्न पूछें...",
        "language_selector": "भाषा चुनें",
        "theme_toggle": "थीम बदलें",
        "logout": "लॉग आउट",
    },
}

# User preference storage mock (In production, stored in user settings DB)
USER_LANGUAGE_PREFERENCES: Dict[str, str] = {}


class TranslationRegistry:
    """Authoritative i18n Registry & Fallback Engine."""

    @classmethod
    def get_text(cls, key: str, lang: str = "en", **kwargs: Any) -> str:
        """Resolve translation key with English fallback and parameter interpolation."""
        lang_code = lang.strip().lower()
        lang_dict = TRANSLATIONS.get(lang_code, TRANSLATIONS["en"])

        text_template = lang_dict.get(key)
        if text_template is None:
            # Fallback to English
            text_template = TRANSLATIONS["en"].get(key, key)

        if kwargs:
            try:
                return text_template.format(**kwargs)
            except (KeyError, ValueError):
                return text_template
        return text_template

    @classmethod
    def get_user_language(cls, user_id: str) -> str:
        """Get language preference for a given user, defaulting to English ('en')."""
        return USER_LANGUAGE_PREFERENCES.get(user_id, LanguageCode.EN.value)

    @classmethod
    def set_user_language(cls, user_id: str, lang: str) -> str:
        """Set user language preference."""
        lang_code = lang.strip().lower()
        if lang_code not in TRANSLATIONS and lang_code not in [m.value for m in LanguageCode]:
            lang_code = LanguageCode.EN.value
        USER_LANGUAGE_PREFERENCES[user_id] = lang_code
        return lang_code

    @classmethod
    def get_ai_language_prompt_instruction(cls, lang: str = "en") -> str:
        """Generate system prompt language directive for AI responses."""
        lang_code = lang.strip().lower()
        if lang_code == LanguageCode.HI.value:
            return (
                "SYSTEM LANGUAGE DIRECTIVE: Please respond primarily in Hindi (हिन्दी) using Devanagari script. "
                "Keep technical and scientific terms easily understandable, using Hindi terminology alongside standard English in parentheses where beneficial."
            )
        elif lang_code == LanguageCode.SA.value:
            return "SYSTEM LANGUAGE DIRECTIVE: Please respond in simple Sanskrit (संस्कृतम्) with English transliteration where helpful."
        elif lang_code == LanguageCode.TA.value:
            return "SYSTEM LANGUAGE DIRECTIVE: Please respond in Tamil (தமிழ்)."
        elif lang_code == LanguageCode.TE.value:
            return "SYSTEM LANGUAGE DIRECTIVE: Please respond in Telugu (తెలుగు)."
        elif lang_code == LanguageCode.KN.value:
            return "SYSTEM LANGUAGE DIRECTIVE: Please respond in Kannada (ಕನ್ನಡ)."
        elif lang_code == LanguageCode.MR.value:
            return "SYSTEM LANGUAGE DIRECTIVE: Please respond in Marathi (मराठी)."
        elif lang_code == LanguageCode.BN.value:
            return "SYSTEM LANGUAGE DIRECTIVE: Please respond in Bengali (বাংলা)."
        else:
            return "SYSTEM LANGUAGE DIRECTIVE: Please respond in English."
