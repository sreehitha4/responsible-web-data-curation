
import re
import unittest

from src.pii_patterns import (
    EMAIL_PATTERN,
    PHONE_PATTERN,
    EMAIL_PLACEHOLDER,
    PHONE_PLACEHOLDER
)


def redact_text(text):
    """Apply the same patterns used by the production pipeline."""

    text = re.sub(
        EMAIL_PATTERN,
        EMAIL_PLACEHOLDER,
        text
    )

    text = re.sub(
        PHONE_PATTERN,
        PHONE_PLACEHOLDER,
        text
    )

    return text


class TestPIIRedaction(unittest.TestCase):

    def test_email_detection(self):
        text = "Contact: test@example.com"

        result = redact_text(text)

        self.assertIn(EMAIL_PLACEHOLDER, result)
        self.assertNotIn("test@example.com", result)

    def test_phone_detection(self):
        text = "Call 9876543210 for assistance."

        result = redact_text(text)

        self.assertIn(PHONE_PLACEHOLDER, result)
        self.assertNotIn("9876543210", result)

    def test_international_phone_detection(self):
        text = "Contact +91 9876543210."

        result = redact_text(text)

        self.assertIn(PHONE_PLACEHOLDER, result)
        self.assertNotIn("9876543210", result)

    def test_multiple_pii_patterns(self):
        text = (
            "Email: user@example.org. "
            "Phone: 9876543210"
        )

        result = redact_text(text)

        self.assertIn(EMAIL_PLACEHOLDER, result)
        self.assertIn(PHONE_PLACEHOLDER, result)

        self.assertNotIn("user@example.org", result)
        self.assertNotIn("9876543210", result)

    def test_ordinary_text_preserved(self):
        text = "This is a normal public information article."

        result = redact_text(text)

        self.assertEqual(text, result)

    def test_empty_text(self):
        result = redact_text("")

        self.assertEqual(result, "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
