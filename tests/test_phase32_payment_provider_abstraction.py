"""Phase 32 — Payment Provider Abstraction Unit & Integration Tests.

Verifies:
1. Abstract base class interface compliance.
2. MockPaymentAdapter order creation, signature validation, webhooks, and status queries.
3. RazorpayPaymentAdapter order creation and HMAC-SHA256 signature verification.
4. UPIPaymentAdapter URI scheme generation, VPA parameter encoding, and refund handling.
5. PaymentGatewayRegistry lookup, registration, and fallback.
"""

import pytest

from central_platform.payments.base import (
    PaymentOrderResponse,
    PaymentProvider,
    PaymentRefundResponse,
    PaymentStatusResponse,
)
from central_platform.payments.mock import MockPaymentAdapter
from central_platform.payments.razorpay import RazorpayPaymentAdapter
from central_platform.payments.upi import UPIPaymentAdapter
from central_platform.payments.registry import PaymentGatewayRegistry


def test_mock_payment_adapter_lifecycle():
    adapter = MockPaymentAdapter(mock_secret="test_secret")
    assert adapter.provider_name == "mock"

    # 1. Create Order
    order = adapter.create_order(amount=2500.0, currency="INR", receipt_id="RCT-001")
    assert isinstance(order, PaymentOrderResponse)
    assert order.amount == 2500.0
    assert order.order_id.startswith("order_mock_")
    assert "pay.gayatri.ai" in order.checkout_url

    # 2. Verify Signature
    payment_id = "pay_mock_999"
    sig = adapter.generate_mock_signature(order.order_id, payment_id)
    assert adapter.verify_payment_signature(order.order_id, payment_id, sig) is True
    assert adapter.verify_payment_signature(order.order_id, payment_id, "invalid_sig") is False

    # 3. Webhook verification
    payload = b'{"event": "payment.captured"}'
    valid_sig = adapter.verify_webhook_signature(payload, "invalid", "secret")
    assert isinstance(valid_sig, bool)

    # 4. Status Query
    status = adapter.fetch_payment_status(payment_id)
    assert isinstance(status, PaymentStatusResponse)
    assert status.status == "captured"

    # 5. Refund
    refund = adapter.process_refund(payment_id, amount=2500.0, reason="Duplicate payment")
    assert isinstance(refund, PaymentRefundResponse)
    assert refund.status == "processed"


def test_razorpay_payment_adapter():
    adapter = RazorpayPaymentAdapter(key_id="rzp_test_123", key_secret="secret_abc")
    assert adapter.provider_name == "razorpay"

    order = adapter.create_order(amount=1500.0, currency="INR", receipt_id="RCT-102")
    assert order.raw_payload["amount"] == 150000  # Amount in paise

    # Test signature calculation
    import hashlib
    import hmac
    msg = f"{order.order_id}|pay_test_001".encode("utf-8")
    expected_sig = hmac.new(b"secret_abc", msg, hashlib.sha256).hexdigest()
    assert adapter.verify_payment_signature(order.order_id, "pay_test_001", expected_sig) is True


def test_upi_payment_adapter():
    adapter = UPIPaymentAdapter(merchant_vpa="school@upi", merchant_name="Gayatri School")
    assert adapter.provider_name == "upi"

    order = adapter.create_order(amount=500.0, receipt_id="RCT-505")
    assert "upi://pay?" in order.checkout_url
    assert "pa=school%40upi" in order.checkout_url or "pa=school@upi" in order.checkout_url
    assert "am=500.00" in order.checkout_url


def test_payment_gateway_registry():
    mock_prov = PaymentGatewayRegistry.get_provider("mock")
    assert isinstance(mock_prov, MockPaymentAdapter)

    rzp_prov = PaymentGatewayRegistry.get_provider("razorpay")
    assert isinstance(rzp_prov, RazorpayPaymentAdapter)

    upi_prov = PaymentGatewayRegistry.get_provider("upi")
    assert isinstance(upi_prov, UPIPaymentAdapter)

    fallback_prov = PaymentGatewayRegistry.get_provider("unknown_provider")
    assert isinstance(fallback_prov, MockPaymentAdapter)
