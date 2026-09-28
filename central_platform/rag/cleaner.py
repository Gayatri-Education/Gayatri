"""Gayatri AI Platform — Document Cleaner & Normalizer (Phase 16).

Cleans parsed text by normalizing Unicode, stripping control characters,
removing boilerplate artifacts, and standardizing whitespace.
"""
from __future__ import annotations

import re
import unicodedata


class DocumentCleaner:
    """Provides robust text cleaning and normalization for RAG chunks."""

    @classmethod
    def clean(cls, text: str) -> str:
        """Execute full cleaning pipeline on document text."""
        if not text:
            return ""

        # 1. Normalize Unicode (NFC)
        normalized = unicodedata.normalize("NFC", text)

        # 2. Remove null bytes and unprintable ASCII control characters (keep \n and \t)
        cleaned = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", normalized)

        # 3. Standardize curly quotes and unicode dashes
        cleaned = (
            cleaned.replace("“", '"')
            .replace("”", '"')
            .replace("‘", "'")
            .replace("’", "'")
            .replace("—", " - ")
            .replace("–", " - ")
            .replace("…", "...")
        )

        # 4. Remove repeated whitespace on the same line
        cleaned = re.sub(r"[ \t]+", " ", cleaned)

        # 5. Normalize line breaks (collapse 3+ newlines to 2)
        cleaned = re.sub(r"\r\n|\r", "\n", cleaned)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

        # 6. Strip leading and trailing whitespace per line
        cleaned_lines = [line.strip() for line in cleaned.split("\n")]
        cleaned = "\n".join(cleaned_lines).strip()

        return cleaned
