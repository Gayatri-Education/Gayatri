"""Gayatri AI Platform — Fee Management Service & Financial Ledger (Phase 30).

Provides authoritative business logic for:
- Fee Structures & Plans
- Student Account Ledger & Balance Calculation
- Invoice Generation & Status Lifecycle
- Payment Processing & Automated Receipt Generation
- Discount Allocation & Refund Handling
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import uuid
from typing import Any, Dict, List, Optional

from central_platform.models.fees import (
    Discount,
    DiscountType,
    FeeAccount,
    FeeFrequency,
    FeePlan,
    FeeStructure,
    Invoice,
    InvoiceStatus,
    Payment,
    PaymentMethod,
    PaymentStatus,
    Receipt,
    Refund,
    RefundStatus,
)


class FeeService:
    """Authoritative Fee Subsystem Service."""

    def __init__(self, db: Optional[Any] = None):
        self.db = db

    def create_fee_structure(
        self,
        org_id: str,
        name: str,
        code: str,
        amount: float,
        description: str = "",
        currency: str = "INR",
        frequency: FeeFrequency = FeeFrequency.ONE_TIME,
    ) -> FeeStructure:
        fs = FeeStructure(
            org_id=org_id,
            name=name,
            code=code,
            description=description,
            amount=amount,
            currency=currency,
            frequency=frequency,
        )
        if self.db and hasattr(self.db, "create_fee_structure"):
            return self.db.create_fee_structure(fs)
        return fs

    def create_fee_plan(
        self,
        org_id: str,
        name: str,
        total_amount: float,
        installments_count: int = 1,
        fee_structure_ids: Optional[List[str]] = None,
        description: str = "",
    ) -> FeePlan:
        plan = FeePlan(
            org_id=org_id,
            name=name,
            description=description,
            total_amount=total_amount,
            installments_count=installments_count,
            fee_structure_ids=fee_structure_ids or [],
        )
        if self.db and hasattr(self.db, "create_fee_plan"):
            return self.db.create_fee_plan(plan)
        return plan

    def create_fee_account(
        self,
        student_id: str,
        org_id: str,
        fee_plan_id: Optional[str] = None,
        initial_due: float = 0.0,
    ) -> FeeAccount:
        account = FeeAccount(
            student_id=student_id,
            org_id=org_id,
            fee_plan_id=fee_plan_id,
            total_due=initial_due,
            balance_due=initial_due,
            status="active" if initial_due > 0 else "clear",
        )
        if self.db and hasattr(self.db, "create_fee_account"):
            return self.db.create_fee_account(account)
        return account

    def generate_invoice(
        self,
        fee_account: FeeAccount,
        amount_due: float,
        due_date: str,
        invoice_number: Optional[str] = None,
        notes: str = "",
    ) -> Invoice:
        if amount_due <= 0:
            raise ValueError("Invoice amount_due must be positive.")

        if not invoice_number:
            inv_count = getattr(fee_account, "invoice_count", 1)
            invoice_number = f"INV-{fee_account.student_id[:6].upper()}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

        invoice = Invoice(
            fee_account_id=fee_account.id,
            student_id=fee_account.student_id,
            org_id=fee_account.org_id,
            invoice_number=invoice_number,
            amount_due=amount_due,
            amount_paid=0.0,
            due_date=due_date,
            status=InvoiceStatus.ISSUED,
            notes=notes,
        )

        fee_account.total_due += amount_due
        fee_account.recalculate_balance()

        if self.db:
            if hasattr(self.db, "create_invoice"):
                invoice = self.db.create_invoice(invoice)
            if hasattr(self.db, "update_fee_account"):
                self.db.update_fee_account(fee_account)

        return invoice

    def record_payment(
        self,
        invoice: Invoice,
        fee_account: FeeAccount,
        amount: float,
        payment_method: PaymentMethod = PaymentMethod.UPI,
        transaction_reference: str = "",
        notes: str = "",
    ) -> tuple[Payment, Receipt]:
        if amount <= 0:
            raise ValueError("Payment amount must be positive.")

        payment = Payment(
            invoice_id=invoice.id,
            fee_account_id=fee_account.id,
            student_id=fee_account.student_id,
            org_id=fee_account.org_id,
            amount=amount,
            payment_method=payment_method,
            transaction_reference=transaction_reference,
            status=PaymentStatus.COMPLETED,
            payment_date=datetime.now(timezone.utc).isoformat(),
            notes=notes,
        )

        # Update invoice
        invoice.amount_paid += amount
        if invoice.amount_paid >= invoice.amount_due:
            invoice.status = InvoiceStatus.PAID
        else:
            invoice.status = InvoiceStatus.PARTIALLY_PAID
        invoice.updated_at = datetime.now(timezone.utc).isoformat()

        # Update account ledger
        fee_account.total_paid += amount
        fee_account.recalculate_balance()

        # Generate receipt
        receipt_no = f"RCT-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{payment.id[:4].upper()}"
        receipt = Receipt(
            payment_id=payment.id,
            receipt_number=receipt_no,
            amount=amount,
            issued_to=fee_account.student_id,
            issued_at=datetime.now(timezone.utc).isoformat(),
            notes=f"Receipt for payment against {invoice.invoice_number}",
        )

        if self.db:
            if hasattr(self.db, "create_payment"):
                payment = self.db.create_payment(payment)
            if hasattr(self.db, "create_receipt"):
                receipt = self.db.create_receipt(receipt)
            if hasattr(self.db, "update_invoice"):
                self.db.update_invoice(invoice)
            if hasattr(self.db, "update_fee_account"):
                self.db.update_fee_account(fee_account)

        return payment, receipt

    def apply_discount(
        self,
        fee_account: FeeAccount,
        code: str,
        discount_type: DiscountType,
        value: float,
        reason: str = "",
        invoice: Optional[Invoice] = None,
    ) -> Discount:
        if value <= 0:
            raise ValueError("Discount value must be positive.")

        base_amount = invoice.amount_due if invoice else fee_account.balance_due
        if discount_type == DiscountType.PERCENTAGE:
            applied_amount = (value / 100.0) * base_amount
        else:
            applied_amount = min(value, base_amount)

        discount = Discount(
            fee_account_id=fee_account.id,
            invoice_id=invoice.id if invoice else None,
            code=code,
            discount_type=discount_type,
            value=value,
            applied_amount=applied_amount,
            reason=reason,
        )

        if invoice:
            invoice.amount_due = max(0.0, invoice.amount_due - applied_amount)
            if invoice.amount_paid >= invoice.amount_due:
                invoice.status = InvoiceStatus.PAID
            invoice.updated_at = datetime.now(timezone.utc).isoformat()
            if self.db and hasattr(self.db, "update_invoice"):
                self.db.update_invoice(invoice)

        fee_account.total_discount += applied_amount
        fee_account.recalculate_balance()

        if self.db:
            if hasattr(self.db, "create_discount"):
                discount = self.db.create_discount(discount)
            if hasattr(self.db, "update_fee_account"):
                self.db.update_fee_account(fee_account)

        return discount

    def process_refund(
        self,
        payment: Payment,
        fee_account: FeeAccount,
        amount: float,
        reason: str = "",
    ) -> Refund:
        if amount <= 0 or amount > payment.amount:
            raise ValueError(f"Refund amount must be between 0 and payment amount ({payment.amount}).")

        refund = Refund(
            payment_id=payment.id,
            fee_account_id=fee_account.id,
            amount=amount,
            reason=reason,
            refund_date=datetime.now(timezone.utc).isoformat(),
            status=RefundStatus.PROCESSED,
        )

        payment.status = PaymentStatus.REFUNDED
        fee_account.total_paid = max(0.0, fee_account.total_paid - amount)
        fee_account.recalculate_balance()

        if self.db:
            if hasattr(self.db, "create_refund"):
                refund = self.db.create_refund(refund)
            if hasattr(self.db, "update_payment"):
                self.db.update_payment(payment)
            if hasattr(self.db, "update_fee_account"):
                self.db.update_fee_account(fee_account)

        return refund
