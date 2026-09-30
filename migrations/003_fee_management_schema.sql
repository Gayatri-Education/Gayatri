-- Gayatri AI Central Platform — DDL Migration 003: Fee Management Subsystem (Phase 30)
-- Compatible with PostgreSQL and SQLite

CREATE TABLE IF NOT EXISTS fee_structures (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    name TEXT NOT NULL,
    code TEXT NOT NULL,
    description TEXT DEFAULT '',
    amount REAL NOT NULL DEFAULT 0.0,
    currency TEXT NOT NULL DEFAULT 'INR',
    frequency TEXT NOT NULL DEFAULT 'one_time',
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    is_deleted INTEGER NOT NULL DEFAULT 0,
    deleted_at TEXT,
    FOREIGN KEY(org_id) REFERENCES organizations(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_fee_structures_org ON fee_structures(org_id);
CREATE INDEX IF NOT EXISTS idx_fee_structures_code ON fee_structures(code);

CREATE TABLE IF NOT EXISTS fee_plans (
    id TEXT PRIMARY KEY,
    org_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    total_amount REAL NOT NULL DEFAULT 0.0,
    installments_count INTEGER NOT NULL DEFAULT 1,
    fee_structure_ids_json TEXT DEFAULT '[]',
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    is_deleted INTEGER NOT NULL DEFAULT 0,
    deleted_at TEXT,
    FOREIGN KEY(org_id) REFERENCES organizations(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_fee_plans_org ON fee_plans(org_id);

CREATE TABLE IF NOT EXISTS fee_accounts (
    id TEXT PRIMARY KEY,
    student_id TEXT NOT NULL,
    org_id TEXT NOT NULL,
    fee_plan_id TEXT,
    total_due REAL NOT NULL DEFAULT 0.0,
    total_paid REAL NOT NULL DEFAULT 0.0,
    total_discount REAL NOT NULL DEFAULT 0.0,
    balance_due REAL NOT NULL DEFAULT 0.0,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    is_deleted INTEGER NOT NULL DEFAULT 0,
    deleted_at TEXT,
    FOREIGN KEY(student_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY(org_id) REFERENCES organizations(id) ON DELETE CASCADE,
    FOREIGN KEY(fee_plan_id) REFERENCES fee_plans(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_fee_accounts_student ON fee_accounts(student_id);
CREATE INDEX IF NOT EXISTS idx_fee_accounts_org ON fee_accounts(org_id);

CREATE TABLE IF NOT EXISTS invoices (
    id TEXT PRIMARY KEY,
    fee_account_id TEXT NOT NULL,
    student_id TEXT NOT NULL,
    org_id TEXT NOT NULL,
    invoice_number TEXT UNIQUE NOT NULL,
    amount_due REAL NOT NULL DEFAULT 0.0,
    amount_paid REAL NOT NULL DEFAULT 0.0,
    due_date TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'issued',
    notes TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    is_deleted INTEGER NOT NULL DEFAULT 0,
    deleted_at TEXT,
    FOREIGN KEY(fee_account_id) REFERENCES fee_accounts(id) ON DELETE CASCADE,
    FOREIGN KEY(student_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY(org_id) REFERENCES organizations(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_invoices_account ON invoices(fee_account_id);
CREATE INDEX IF NOT EXISTS idx_invoices_student ON invoices(student_id);
CREATE INDEX IF NOT EXISTS idx_invoices_number ON invoices(invoice_number);

CREATE TABLE IF NOT EXISTS payments (
    id TEXT PRIMARY KEY,
    invoice_id TEXT NOT NULL,
    fee_account_id TEXT NOT NULL,
    student_id TEXT NOT NULL,
    org_id TEXT NOT NULL,
    amount REAL NOT NULL DEFAULT 0.0,
    payment_method TEXT NOT NULL DEFAULT 'upi',
    transaction_reference TEXT DEFAULT '',
    status TEXT NOT NULL DEFAULT 'completed',
    payment_date TEXT NOT NULL,
    notes TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    is_deleted INTEGER NOT NULL DEFAULT 0,
    deleted_at TEXT,
    FOREIGN KEY(invoice_id) REFERENCES invoices(id) ON DELETE CASCADE,
    FOREIGN KEY(fee_account_id) REFERENCES fee_accounts(id) ON DELETE CASCADE,
    FOREIGN KEY(student_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY(org_id) REFERENCES organizations(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_payments_invoice ON payments(invoice_id);
CREATE INDEX IF NOT EXISTS idx_payments_account ON payments(fee_account_id);

CREATE TABLE IF NOT EXISTS receipts (
    id TEXT PRIMARY KEY,
    payment_id TEXT UNIQUE NOT NULL,
    receipt_number TEXT UNIQUE NOT NULL,
    amount REAL NOT NULL DEFAULT 0.0,
    issued_to TEXT NOT NULL,
    issued_at TEXT NOT NULL,
    notes TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    is_deleted INTEGER NOT NULL DEFAULT 0,
    deleted_at TEXT,
    FOREIGN KEY(payment_id) REFERENCES payments(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_receipts_payment ON receipts(payment_id);
CREATE INDEX IF NOT EXISTS idx_receipts_number ON receipts(receipt_number);

CREATE TABLE IF NOT EXISTS discounts (
    id TEXT PRIMARY KEY,
    fee_account_id TEXT NOT NULL,
    invoice_id TEXT,
    code TEXT NOT NULL,
    discount_type TEXT NOT NULL DEFAULT 'fixed_amount',
    value REAL NOT NULL DEFAULT 0.0,
    applied_amount REAL NOT NULL DEFAULT 0.0,
    reason TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    is_deleted INTEGER NOT NULL DEFAULT 0,
    deleted_at TEXT,
    FOREIGN KEY(fee_account_id) REFERENCES fee_accounts(id) ON DELETE CASCADE,
    FOREIGN KEY(invoice_id) REFERENCES invoices(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_discounts_account ON discounts(fee_account_id);

CREATE TABLE IF NOT EXISTS refunds (
    id TEXT PRIMARY KEY,
    payment_id TEXT NOT NULL,
    fee_account_id TEXT NOT NULL,
    amount REAL NOT NULL DEFAULT 0.0,
    reason TEXT DEFAULT '',
    refund_date TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'processed',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    is_deleted INTEGER NOT NULL DEFAULT 0,
    deleted_at TEXT,
    FOREIGN KEY(payment_id) REFERENCES payments(id) ON DELETE CASCADE,
    FOREIGN KEY(fee_account_id) REFERENCES fee_accounts(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_refunds_payment ON refunds(payment_id);
CREATE INDEX IF NOT EXISTS idx_refunds_account ON refunds(fee_account_id);
