# src/settings_manager.py
"""
Utility helpers for managing company profile data and application-level
preferences that live inside ``data/invoices.db``.

This module is intentionally lightweight so that both the UI layer and
headless scripts (e.g. report generation) can reuse the same behaviour
without having to instantiate the heavier ``Database`` class.
"""

from __future__ import annotations

import os
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from typing import Dict, Optional
import hashlib


DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "invoices.db")
DEFAULT_PDF_DIR = os.path.join(os.path.dirname(__file__), "..", "invoices")

PREF_DEFAULTS = {
    "invoice_prefix": "INV-",
    "invoice_sequence": "1",
    "default_pdf_dir": os.path.abspath(DEFAULT_PDF_DIR),
    "auto_open_pdf": "0",
}


# --------------------------------------------------------------------------- #
# Dataclasses
# --------------------------------------------------------------------------- #
@dataclass
class CompanyProfile:
    name: str = ""
    address: str = ""
    contact: str = ""
    ntn: str = ""
    strn: str = ""


@dataclass
class Preferences:
    invoice_prefix: str = PREF_DEFAULTS["invoice_prefix"]
    invoice_sequence: int = int(PREF_DEFAULTS["invoice_sequence"])
    default_pdf_dir: str = PREF_DEFAULTS["default_pdf_dir"]
    auto_open_pdf: bool = False


# --------------------------------------------------------------------------- #
# Connection helpers
# --------------------------------------------------------------------------- #
def _connect() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _ensure_defaults():
    os.makedirs(DEFAULT_PDF_DIR, exist_ok=True)


# --------------------------------------------------------------------------- #
# Settings persistence
# --------------------------------------------------------------------------- #
def set_setting(key: str, value: str) -> None:
    with closing(_connect()) as conn:
        conn.execute(
            """
            INSERT INTO settings (key, value)
            VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value
            """,
            (key, value),
        )
        conn.commit()


def get_setting(key: str, default: Optional[str] = None) -> Optional[str]:
    with closing(_connect()) as conn:
        row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row["value"] if row else default


# --------------------------------------------------------------------------- #
# Company profile helpers
# --------------------------------------------------------------------------- #
def get_company_profile() -> CompanyProfile:
    with closing(_connect()) as conn:
        row = conn.execute("SELECT * FROM company LIMIT 1").fetchone()
        if not row:
            return CompanyProfile()
        return CompanyProfile(
            name=row["name"] or "",
            address=row["address"] or "",
            contact=row["contact"] or "",
            ntn=row["ntn"] or "",
            strn=row["strn"] or "",
        )


def save_company_profile(profile: CompanyProfile) -> None:
    if not profile.name.strip():
        raise ValueError("Company name is required")

    with closing(_connect()) as conn:
        existing = conn.execute("SELECT id FROM company LIMIT 1").fetchone()
        params = (
            profile.name.strip(),
            profile.address.strip(),
            profile.contact.strip(),
            profile.ntn.strip(),
            profile.strn.strip(),
        )

        if existing:
            conn.execute(
                """
                UPDATE company
                   SET name=?, address=?, contact=?, ntn=?, strn=?
                 WHERE id=?
                """,
                (*params, existing["id"]),
            )
        else:
            conn.execute(
                """
                INSERT INTO company (name, address, contact, ntn, strn)
                VALUES (?, ?, ?, ?, ?)
                """,
                params,
            )
        conn.commit()


# --------------------------------------------------------------------------- #
# Preferences helpers
# --------------------------------------------------------------------------- #
def get_preferences() -> Preferences:
    _ensure_defaults()

    keys = tuple(PREF_DEFAULTS.keys())
    placeholders = ",".join("?" for _ in keys)

    prefs: Dict[str, str] = PREF_DEFAULTS.copy()
    if placeholders:
        with closing(_connect()) as conn:
            rows = conn.execute(
                f"SELECT key, value FROM settings WHERE key IN ({placeholders})",
                keys,
            ).fetchall()
            for row in rows:
                prefs[row["key"]] = row["value"]

    return Preferences(
        invoice_prefix=prefs["invoice_prefix"] or PREF_DEFAULTS["invoice_prefix"],
        invoice_sequence=int(prefs["invoice_sequence"] or PREF_DEFAULTS["invoice_sequence"]),
        default_pdf_dir=prefs["default_pdf_dir"] or PREF_DEFAULTS["default_pdf_dir"],
        auto_open_pdf=(prefs["auto_open_pdf"] == "1"),
    )


def save_preferences(prefs: Preferences) -> None:
    _ensure_defaults()

    pdf_dir = prefs.default_pdf_dir.strip() or PREF_DEFAULTS["default_pdf_dir"]
    os.makedirs(pdf_dir, exist_ok=True)

    payload = [
        ("invoice_prefix", prefs.invoice_prefix.strip() or PREF_DEFAULTS["invoice_prefix"]),
        ("invoice_sequence", str(max(1, prefs.invoice_sequence))),
        ("default_pdf_dir", pdf_dir),
        ("auto_open_pdf", "1" if prefs.auto_open_pdf else "0"),
    ]

    with closing(_connect()) as conn:
        conn.executemany(
            """
            INSERT INTO settings (key, value)
            VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value
            """,
            payload,
        )
        conn.commit()


# --------------------------------------------------------------------------- #
# Invoice numbering helpers
# --------------------------------------------------------------------------- #
def get_next_invoice_number(increment: bool = True) -> str:
    prefs = get_preferences()
    invoice_no = f"{prefs.invoice_prefix}{prefs.invoice_sequence:04d}"
    if increment:
        update_invoice_sequence(prefs.invoice_sequence + 1)
    return invoice_no


def update_invoice_sequence(next_value: int) -> None:
    next_value = max(1, int(next_value))
    set_setting("invoice_sequence", str(next_value))



# --------------------------------------------------------------------------- #
# Security helpers
# --------------------------------------------------------------------------- #
def set_app_password(password: str) -> None:
    """Set a password for the application (stored as SHA256 hash). Empty string removes it."""
    if not password:
        set_setting("app_password_hash", "")
        return

    hashed = hashlib.sha256(password.encode("utf-8")).hexdigest()
    set_setting("app_password_hash", hashed)


def verify_app_password(password: str) -> bool:
    """Check if the provided password matches the stored hash."""
    stored_hash = get_setting("app_password_hash")
    if not stored_hash:
        return True  # No password set means anything passes
    
    hashed = hashlib.sha256(password.encode("utf-8")).hexdigest()
    return hashed == stored_hash


def is_password_protected() -> bool:
    """Return True if a password is set."""
    stored_hash = get_setting("app_password_hash")
    return bool(stored_hash)


if __name__ == "__main__":

    # Simple manual run to sanity check functionality
    profile = get_company_profile()
    print("Loaded profile:", profile)
    prefs = get_preferences()
    print("Loaded prefs:", prefs)
    print("Next invoice number preview:", get_next_invoice_number(increment=False))
