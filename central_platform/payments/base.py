"""Gayatri AI Platform — Payment Provider Abstraction Base & Contracts (Phase 32).

Defines the authoritative payment gateway interface keeping provider-specific
logic decoupled from core financial ledger models.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional


class PaymentProviderType(str, Enum):
    MOCK = "mock"
    RAZORPAY = "razorpay"
    UPI = "upi"
    STRIPE = "stripe"


@dataclass
class PaymentOrderResponse:
    """Standardized response after creating a payment gateway order."""
    order_id: str
    amount: float
    currency: str
    receipt_id: str
    provider: str
    checkout_url: Optional[str] = None
    raw_payload: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PaymentStatusResponse:
    """Standardized status response for a transaction query."""
    payment_id: str
    order_id: str
    status: str  # "created", "captured", "failed", "refunded"
    amount: float
    currency: str
    payment_method: str  # "upi", "card", "netbanking", "wallet"
    transaction_ref: str
    provider: str
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PaymentRefundResponse:
    """Standardized response after initiating a gateway refund."""
    refund_id: str
    payment_id: str
    amount: float
    currency: str
    status: str  # "processed", "pending", "failed"
    provider: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PaymentProvider(ABC):
    """Abstract Base Class for all Payment Gateway Adapters."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return unique provider identifier string."""
        pass

    @abstractmethod
    def create_order(
        self,
        amount: float,
        currency: str = "INR",
        receipt_id: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PaymentOrderResponse:
        """Create a payment gateway order / transaction Intent."""
        pass

    @abstractmethod
    def verify_payment_signature(
        self,
        order_id: str,
        payment_id: str,
        signature: str,
    ) -> bool:
        """Verify payment completion cryptographic signature."""
        pass

    @abstractmethod
    def verify_webhook_signature(
        self,
        payload_bytes: bytes,
        signature_header: str,
        secret: str,
    ) -> bool:
        """Verify authenticity of webhook notifications."""
        pass

    @abstractmethod
    def fetch_payment_status(self, payment_id: str) -> PaymentStatusResponse:
        """Fetch current payment status directly from gateway."""
        pass

    @abstractmethod
    def process_refund(
        self,
        payment_id: str,
        amount: float,
        reason: str = "",
    ) -> PaymentRefundResponse:
        """Process refund via payment gateway."""
        pass
