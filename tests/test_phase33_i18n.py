"""Phase 33 — English/Hindi Internationalization Unit & Integration Tests.

Verifies:
1. Asset existence for client-side i18n controller.
2. English and Hindi translation resolution.
3. Fallback logic for missing keys.
4. Parameter interpolation in translations.
5. User language preference getters/setters.
6. AI prompt language directive generation.
"""

from pathlib import Path
import pytest

from central_platform.i18n.registry import (
    LanguageCode,
    TranslationRegistry,
)


def test_i18n_assets_exist():
    js_path = Path("app/ui/design_system/i18n.js")
    assert js_path.exists(), "i18n.js client controller must exist"
    content = js_path.read_text(encoding="utf-8")
    assert "GayatriI18n" in content
    assert "app_title" in content


def test_translation_resolution_en_and_hi():
    # English lookup
    assert TranslationRegistry.get_text("dashboard", lang="en") == "Dashboard"
    assert TranslationRegistry.get_text("fees", lang="en") == "Fees & Payments"

    # Hindi lookup
    assert TranslationRegistry.get_text("dashboard", lang="hi") == "डैशबोर्ड"
    assert TranslationRegistry.get_text("fees", lang="hi") == "शुल्क और भुगतान"


def test_english_fallback_for_missing_key_and_lang():
    # Key missing in Hindi, fallback to English
    text_en_fallback = TranslationRegistry.get_text("non_existent_key", lang="hi")
    assert text_en_fallback == "non_existent_key"

    # Unsupported language fallback
    text_unknown_lang = TranslationRegistry.get_text("curriculum", lang="xyz")
    assert text_unknown_lang == "Curriculum"


def test_translation_interpolation():
    text_en = TranslationRegistry.get_text("welcome", lang="en", name="Aarav")
    assert text_en == "Welcome back, Aarav"

    text_hi = TranslationRegistry.get_text("welcome", lang="hi", name="आरव")
    assert text_hi == "पुनः स्वागत है, आरव"


def test_user_language_preferences():
    user_id = "usr_test_101"
    assert TranslationRegistry.get_user_language(user_id) == "en"

    TranslationRegistry.set_user_language(user_id, "hi")
    assert TranslationRegistry.get_user_language(user_id) == "hi"

    # Invalid language reverts/defaults to English
    TranslationRegistry.set_user_language(user_id, "invalid_lang")
    assert TranslationRegistry.get_user_language(user_id) == "en"


def test_ai_prompt_language_directives():
    en_directive = TranslationRegistry.get_ai_language_prompt_instruction("en")
    assert "Please respond in English" in en_directive

    hi_directive = TranslationRegistry.get_ai_language_prompt_instruction("hi")
    assert "Hindi" in hi_directive
    assert "Devanagari" in hi_directive

    sa_directive = TranslationRegistry.get_ai_language_prompt_instruction("sa")
    assert "Sanskrit" in sa_directive
