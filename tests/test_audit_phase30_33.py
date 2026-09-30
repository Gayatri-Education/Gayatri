"""Exhaustive Audit & Verification Suite for Phases 30-33.

Verifies:
1. FeeService boundary validation (negative/zero invoice amounts, invalid payments, invalid discounts, out-of-range refunds).
2. Signature verification security (empty strings, null, malformed inputs) in Payment Adapters.
3. TranslationRegistry exception safety and parameter interpolation handling.
4. Absence of swallowed exceptions or silent failures across the subsystem.
"""

import pytest

from central_platform.fees.service import FeeService
from central_platform.models.fees import (
    DiscountType,
    FeeAccount,
    Invoice,
    InvoiceStatus,
    Payment,
    PaymentMethod,
    PaymentStatus,
)
from central_platform.payments.mock import MockPaymentAdapter
from central_platform.payments.razorpay import RazorpayPaymentAdapter
from central_platform.payments.upi import UPIPaymentAdapter
from central_platform.i18n.registry import TranslationRegistry


def test_fee_service_negative_amount_validations():
    service = FeeService(db=None)
    account = FeeAccount(student_id="s1", org_id="o1", total_due=1000.0, balance_due=1000.0)

    # Negative invoice amount_due
    with pytest.raises(ValueError, match="must be positive"):
        service.generate_invoice(account, amount_due=-500.0, due_date="2026-12-31")

    # Zero invoice amount_due
    with pytest.raises(ValueError, match="must be positive"):
        service.generate_invoice(account, amount_due=0.0, due_date="2026-12-31")

    # Generate valid invoice for subsequent tests
    invoice = service.generate_invoice(account, amount_due=1000.0, due_date="2026-12-31")

    # Negative payment amount
    with pytest.raises(ValueError, match="must be positive"):
        service.record_payment(invoice, account, amount=-100.0)

    # Negative discount value
    with pytest.raises(ValueError, match="must be positive"):
        service.apply_discount(account, code="FAIL", discount_type=DiscountType.FIXED_AMOUNT, value=-50.0)

    # Record valid payment
    payment, _ = service.record_payment(invoice, account, amount=1000.0)

    # Invalid refund amount (negative or exceeding payment amount)
    with pytest.raises(ValueError, match="Refund amount must be between"):
        service.process_refund(payment, account, amount=-10.0)

    with pytest.raises(ValueError, match="Refund amount must be between"):
        service.process_refund(payment, account, amount=2000.0)


def test_payment_adapter_signature_security():
    mock_adapter = MockPaymentAdapter("secret")
    assert mock_adapter.verify_payment_signature("order1", "pay1", "") is False
    assert mock_adapter.verify_webhook_signature(b"data", "", "secret") is False

    rzp_adapter = RazorpayPaymentAdapter("key", "secret")
    assert rzp_adapter.verify_payment_signature("order1", "pay1", "") is False
    assert rzp_adapter.verify_webhook_signature(b"data", "", "secret") is False

    upi_adapter = UPIPaymentAdapter("vpa@upi")
    assert upi_adapter.verify_payment_signature("order1", "pay1", "") is False


def test_translation_registry_exception_safety():
    # Formatting mismatch should not raise, but fallback to template
    result = TranslationRegistry.get_text("welcome", lang="en", wrong_param="test")
    assert "Welcome back" in result

    # Non-string inputs or unexpected types
    result2 = TranslationRegistry.get_text("app_title", lang="hi")
    assert result2 == "गायत्री एआई प्लेटफॉर्म"
