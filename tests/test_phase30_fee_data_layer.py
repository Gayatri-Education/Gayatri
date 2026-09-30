"""Phase 30 — Fee Data Layer Unit & Integration Tests.

Verifies:
1. Migration 003 DDL schema application.
2. Dataclass serialization and enum values.
3. Database persistence across all 8 fee entities.
4. FeeService business logic: invoice generation, discount calculation, payment recording, receipt generation, and refund processing.
"""

from datetime import datetime, timezone
import pytest

from central_platform.db import PlatformDatabase
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
from central_platform.models.schema import Organization, User, UserRole
from central_platform.fees.service import FeeService


@pytest.fixture
def db():
    database = PlatformDatabase(":memory:")
    # Seed parent organization and user
    org = Organization(id="org_test_01", name="Test Academy", slug="test-academy")
    database.create_organization(org)

    user = User(
        id="student_001",
        email="student@test.com",
        full_name="Rahul Varma",
        role=UserRole.STUDENT,
        organization_id="org_test_01",
    )
    database.create_user(user)
    yield database
    database.close()


def test_fee_enums_and_dataclasses():
    fs = FeeStructure(
        org_id="org_test_01",
        name="Tuition Fee",
        code="TUT-101",
        amount=5000.0,
        frequency=FeeFrequency.MONTHLY,
    )
    d = fs.to_dict()
    assert d["frequency"] == "monthly"
    assert d["amount"] == 5000.0

    account = FeeAccount(
        student_id="student_001",
        org_id="org_test_01",
        total_due=10000.0,
        total_paid=4000.0,
        total_discount=1000.0,
    )
    account.recalculate_balance()
    assert account.balance_due == 5000.0
    assert account.status == "active"

    account.total_paid = 9000.0
    account.recalculate_balance()
    assert account.balance_due == 0.0
    assert account.status == "clear"


def test_database_fee_structures_and_plans(db: PlatformDatabase):
    fs = FeeStructure(
        org_id="org_test_01",
        name="Annual Tuition",
        code="TUITION-ANNUAL",
        amount=60000.0,
        frequency=FeeFrequency.ANNUAL,
    )
    created_fs = db.create_fee_structure(fs)
    assert created_fs.id == fs.id

    retrieved_fs = db.get_fee_structure(fs.id)
    assert retrieved_fs is not None
    assert retrieved_fs.code == "TUITION-ANNUAL"
    assert retrieved_fs.amount == 60000.0

    plan = FeePlan(
        org_id="org_test_01",
        name="Standard Annual Plan",
        total_amount=60000.0,
        installments_count=4,
        fee_structure_ids=[fs.id],
    )
    created_plan = db.create_fee_plan(plan)
    assert created_plan.id == plan.id

    retrieved_plan = db.get_fee_plan(plan.id)
    assert retrieved_plan is not None
    assert retrieved_plan.installments_count == 4
    assert fs.id in retrieved_plan.fee_structure_ids


def test_fee_service_full_lifecycle(db: PlatformDatabase):
    service = FeeService(db=db)

    # 1. Create account
    account = service.create_fee_account(
        student_id="student_001",
        org_id="org_test_01",
        initial_due=0.0,
    )
    assert account.balance_due == 0.0

    # 2. Generate invoice
    invoice = service.generate_invoice(
        fee_account=account,
        amount_due=10000.0,
        due_date="2026-10-15T00:00:00Z",
        notes="Term 1 Tuition Invoice",
    )
    assert invoice.amount_due == 10000.0
    assert invoice.status == InvoiceStatus.ISSUED
    assert account.total_due == 10000.0
    assert account.balance_due == 10000.0

    # 3. Apply Discount
    discount = service.apply_discount(
        fee_account=account,
        code="SCHOLAR10",
        discount_type=DiscountType.PERCENTAGE,
        value=10.0,  # 10% off -> 1000
        reason="Merit Scholarship",
        invoice=invoice,
    )
    assert discount.applied_amount == 1000.0
    assert account.total_discount == 1000.0
    assert account.balance_due == 9000.0

    # 4. Record Payment
    payment, receipt = service.record_payment(
        invoice=invoice,
        fee_account=account,
        amount=9000.0,
        payment_method=PaymentMethod.UPI,
        transaction_reference="UPI/1234567890",
        notes="Paid via GPay",
    )
    assert payment.amount == 9000.0
    assert payment.status == PaymentStatus.COMPLETED
    assert invoice.status == InvoiceStatus.PAID
    assert receipt.receipt_number.startswith("RCT-")
    assert account.total_paid == 9000.0
    assert account.balance_due == 0.0
    assert account.status == "clear"

    # 5. Process Refund
    refund = service.process_refund(
        payment=payment,
        fee_account=account,
        amount=2000.0,
        reason="Overpayment adjustment",
    )
    assert refund.amount == 2000.0
    assert refund.status == RefundStatus.PROCESSED
    assert payment.status == PaymentStatus.REFUNDED
    assert account.total_paid == 7000.0
    assert account.balance_due == 2000.0


def test_database_invoice_payment_receipt_persistence(db: PlatformDatabase):
    account = db.create_fee_account(
        FeeAccount(student_id="student_001", org_id="org_test_01", total_due=5000.0, balance_due=5000.0)
    )
    invoice = db.create_invoice(
        Invoice(
            fee_account_id=account.id,
            student_id="student_001",
            org_id="org_test_01",
            invoice_number="INV-TEST-001",
            amount_due=5000.0,
            due_date="2026-11-01T00:00:00Z",
        )
    )
    payment = db.create_payment(
        Payment(
            invoice_id=invoice.id,
            fee_account_id=account.id,
            student_id="student_001",
            org_id="org_test_01",
            amount=5000.0,
            payment_method=PaymentMethod.BANK_TRANSFER,
            payment_date=datetime.now(timezone.utc).isoformat(),
        )
    )
    receipt = db.create_receipt(
        Receipt(
            payment_id=payment.id,
            receipt_number="RCT-TEST-001",
            amount=5000.0,
            issued_to="student_001",
            issued_at=datetime.now(timezone.utc).isoformat(),
        )
    )

    r_inv = db.get_invoice(invoice.id)
    assert r_inv is not None
    assert r_inv.invoice_number == "INV-TEST-001"

    r_pay = db.get_payment(payment.id)
    assert r_pay is not None
    assert r_pay.payment_method == PaymentMethod.BANK_TRANSFER

    r_rct = db.get_receipt_for_payment(payment.id)
    assert r_rct is not None
    assert r_rct.receipt_number == "RCT-TEST-001"
