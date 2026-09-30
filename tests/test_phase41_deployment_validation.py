"""
Tests for Phase 41 — Deployment Validation Subsystem.
"""

import os
import tempfile
import pytest
from central_platform.deployment.validator import (
    ValidationStatus,
    ValidationCategory,
    ValidationResult,
    DeploymentValidationReport,
    DeploymentValidator,
)


def test_deployment_validator_full_run_default():
    validator = DeploymentValidator()
    report = validator.run_full_validation()

    assert isinstance(report, DeploymentValidationReport)
    assert report.total_checks == 9
    assert report.passed_checks + report.warning_checks + report.failed_checks == 9
    assert isinstance(report.summary, str)
    assert len(report.summary) > 0

    d = report.to_dict()
    assert "is_ready" in d
    assert "total_checks" in d
    assert "results" in d
    assert len(d["results"]) == 9


def test_validate_environment_modes():
    # Dev mode -> WARN
    v_dev = DeploymentValidator(env_vars={"APP_ENV": "development"})
    r_dev = v_dev.validate_environment()
    assert r_dev.status == ValidationStatus.WARN

    # Prod mode -> PASS
    v_prod = DeploymentValidator(env_vars={"APP_ENV": "production"})
    r_prod = v_prod.validate_environment()
    assert r_prod.status == ValidationStatus.PASS

    # Invalid mode -> FAIL
    v_inv = DeploymentValidator(env_vars={"APP_ENV": "invalid_mode"})
    r_inv = v_inv.validate_environment()
    assert r_inv.status == ValidationStatus.FAIL


def test_validate_secrets():
    # Weak secret -> FAIL
    v_weak = DeploymentValidator(env_vars={"SECRET_KEY": "123456"})
    r_weak = v_weak.validate_secrets()
    assert r_weak.status == ValidationStatus.FAIL

    # Missing secret -> WARN
    v_missing = DeploymentValidator(env_vars={})
    r_missing = v_missing.validate_secrets()
    assert r_missing.status == ValidationStatus.WARN

    # Strong secret -> PASS
    v_strong = DeploymentValidator(env_vars={"SECRET_KEY": "a_very_secure_long_random_secret_key_12345"})
    r_strong = v_strong.validate_secrets()
    assert r_strong.status == ValidationStatus.PASS


def test_validate_database_and_migrations():
    # Non-existent DB file -> FAIL
    v_nodb = DeploymentValidator(db_path="non_existent_db_file.db")
    r_nodb = v_nodb.validate_database_and_migrations()
    assert r_nodb.status == ValidationStatus.FAIL

    # Existing local DB -> PASS or WARN depending on schema
    v_db = DeploymentValidator()
    r_db = v_db.validate_database_and_migrations()
    assert r_db.status in (ValidationStatus.PASS, ValidationStatus.WARN)


def test_validate_backups():
    with tempfile.TemporaryDirectory() as tmpdir:
        v = DeploymentValidator(root_dir=tmpdir)
        r = v.validate_backups()
        assert r.status == ValidationStatus.PASS
        assert os.path.exists(os.path.join(tmpdir, "backups"))


def test_validate_logging_and_monitoring():
    with tempfile.TemporaryDirectory() as tmpdir:
        v = DeploymentValidator(root_dir=tmpdir)
        r = v.validate_logging_and_monitoring()
        assert r.status == ValidationStatus.PASS
        assert os.path.exists(os.path.join(tmpdir, "logs"))


def test_validate_health_checks():
    v = DeploymentValidator()
    r = v.validate_health_checks()
    assert r.status == ValidationStatus.PASS
    assert r.details["services"]["database"] == "UP"


def test_validate_model_providers():
    v = DeploymentValidator()
    r = v.validate_model_providers()
    assert r.status == ValidationStatus.PASS
    assert r.details["models_count"] > 0


def test_validate_static_assets():
    v = DeploymentValidator()
    r = v.validate_static_assets()
    assert r.status == ValidationStatus.PASS
    assert r.details["asset_count"] == 16


def test_validate_https_security():
    # Prod with FORCE_HTTPS=false -> FAIL
    v_fail = DeploymentValidator(env_vars={"APP_ENV": "production", "FORCE_HTTPS": "false"})
    r_fail = v_fail.validate_https_security()
    assert r_fail.status == ValidationStatus.FAIL

    # Prod with FORCE_HTTPS=true -> PASS
    v_pass = DeploymentValidator(env_vars={"APP_ENV": "production", "FORCE_HTTPS": "true"})
    r_pass = v_pass.validate_https_security()
    assert r_pass.status == ValidationStatus.PASS
