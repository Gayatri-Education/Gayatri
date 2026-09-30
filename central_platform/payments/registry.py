"""Gayatri AI Platform — Payment Gateway Registry & Factory (Phase 32).

Central registry for registering, configuring, and resolving payment gateway providers.
"""

from __future__ import annotations

from typing import Dict, Type

from central_platform.payments.base import PaymentProvider
from central_platform.payments.mock import MockPaymentAdapter
from central_platform.payments.razorpay import RazorpayPaymentAdapter
from central_platform.payments.upi import UPIPaymentAdapter


class PaymentGatewayRegistry:
    """Registry managing available payment provider implementations."""

    _providers: Dict[str, PaymentProvider] = {}

    @classmethod
    def register_provider(cls, name: str, provider: PaymentProvider) -> None:
        cls._providers[name.lower()] = provider

    @classmethod
    def get_provider(cls, name: str = "mock") -> PaymentProvider:
        name_clean = name.strip().lower()
        if name_clean in cls._providers:
            return cls._providers[name_clean]

        # Default instantiate standard adapters
        if name_clean == "razorpay":
            adapter = RazorpayPaymentAdapter()
            cls._providers["razorpay"] = adapter
            return adapter
        elif name_clean == "upi":
            adapter = UPIPaymentAdapter()
            cls._providers["upi"] = adapter
            return adapter
        else:
            adapter = MockPaymentAdapter()
            cls._providers["mock"] = adapter
            return adapter

    @classmethod
    def list_available_providers(cls) -> list[str]:
        return ["mock", "razorpay", "upi"]
