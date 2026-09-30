"""Gayatri AI Platform — Fee Management Models & Enums (Phase 30).

Provides authoritative data contracts for:
- Fee Structures & Fee Plans
- Student Fee Accounts
- Invoices & Invoice Status tracking
- Payments & Payment Methods
- Receipts & Receipts Ledger
- Discounts & Discount Calculation
- Refunds & Refund Processing
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
import uuid
from typing import Any, Dict, List, Optional


class FeeFrequency(str, Enum):
    ONE_TIME = "one_time"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"


class InvoiceStatus(str, Enum):
    DRAFT = "draft"
    ISSUED = "issued"
    PAID = "paid"
    PARTIALLY_PAID = "partially_paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class PaymentMethod(str, Enum):
    CASH = "cash"
    BANK_TRANSFER = "bank_transfer"
    UPI = "upi"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    CHEQUE = "cheque"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class DiscountType(str, Enum):
    PERCENTAGE = "percentage"
    FIXED_AMOUNT = "fixed_amount"


class RefundStatus(str, Enum):
    PENDING = "pending"
    PROCESSED = "processed"
    REJECTED = "rejected"


@dataclass
class FeeStructure:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    org_id: str = ""
    name: str = ""
    code: str = ""
    description: str = ""
    amount: float = 0.0
    currency: str = "INR"
    frequency: FeeFrequency = FeeFrequency.ONE_TIME
    is_active: bool = True
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    is_deleted: bool = False
    deleted_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["frequency"] = self.frequency.value if isinstance(self.frequency, FeeFrequency) else self.frequency
        return d


@dataclass
class FeePlan:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    org_id: str = ""
    name: str = ""
    description: str = ""
    total_amount: float = 0.0
    installments_count: int = 1
    fee_structure_ids: List[str] = field(default_factory=list)
    is_active: bool = True
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    is_deleted: bool = False
    deleted_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class FeeAccount:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str = ""
    org_id: str = ""
    fee_plan_id: Optional[str] = None
    total_due: float = 0.0
    total_paid: float = 0.0
    total_discount: float = 0.0
    balance_due: float = 0.0
    status: str = "active"  # "active", "clear", "overdue"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    is_deleted: bool = False
    deleted_at: Optional[str] = None

    def recalculate_balance(self) -> None:
        self.balance_due = max(0.0, self.total_due - self.total_paid - self.total_discount)
        if self.balance_due == 0.0 and self.total_due > 0:
            self.status = "clear"
        elif self.balance_due > 0 and self.status == "clear":
            self.status = "active"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Invoice:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    fee_account_id: str = ""
    student_id: str = ""
    org_id: str = ""
    invoice_number: str = ""
    amount_due: float = 0.0
    amount_paid: float = 0.0
    due_date: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: InvoiceStatus = InvoiceStatus.ISSUED
    notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    is_deleted: bool = False
    deleted_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value if isinstance(self.status, InvoiceStatus) else self.status
        return d


@dataclass
class Payment:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    invoice_id: str = ""
    fee_account_id: str = ""
    student_id: str = ""
    org_id: str = ""
    amount: float = 0.0
    payment_method: PaymentMethod = PaymentMethod.UPI
    transaction_reference: str = ""
    status: PaymentStatus = PaymentStatus.COMPLETED
    payment_date: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    is_deleted: bool = False
    deleted_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["payment_method"] = self.payment_method.value if isinstance(self.payment_method, PaymentMethod) else self.payment_method
        d["status"] = self.status.value if isinstance(self.status, PaymentStatus) else self.status
        return d


@dataclass
class Receipt:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    payment_id: str = ""
    receipt_number: str = ""
    amount: float = 0.0
    issued_to: str = ""
    issued_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    is_deleted: bool = False
    deleted_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Discount:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    fee_account_id: str = ""
    invoice_id: Optional[str] = None
    code: str = ""
    discount_type: DiscountType = DiscountType.FIXED_AMOUNT
    value: float = 0.0
    applied_amount: float = 0.0
    reason: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    is_deleted: bool = False
    deleted_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["discount_type"] = self.discount_type.value if isinstance(self.discount_type, DiscountType) else self.discount_type
        return d


@dataclass
class Refund:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    payment_id: str = ""
    fee_account_id: str = ""
    amount: float = 0.0
    reason: str = ""
    refund_date: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: RefundStatus = RefundStatus.PROCESSED
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    is_deleted: bool = False
    deleted_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value if isinstance(self.status, RefundStatus) else self.status
        return d
