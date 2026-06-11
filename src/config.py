"""
Configuration settings for the Payment Exception Resolution Agent system.
All values loaded from environment / .env file via python-dotenv.
"""

import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

load_dotenv()


class Config:
    """Centralised configuration for the payment exception system."""

    # ------------------------------------------------------------------
    # OpenAI
    # ------------------------------------------------------------------
    OPENAI_API_KEY: str  = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str    = os.getenv("OPENAI_MODEL", "gpt-4o")
    TEMPERATURE: float   = float(os.getenv("TEMPERATURE", "0.3"))

    # ------------------------------------------------------------------
    # MySQL Database
    # ------------------------------------------------------------------
    DB_HOST: str     = os.getenv("DB_HOST", "localhost")
    DB_PORT: int     = int(os.getenv("DB_PORT", "3306"))
    DB_NAME: str     = os.getenv("DB_NAME", "payment_exception_db")
    DB_USER: str     = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")

    @classmethod
    def get_db_url(cls) -> str:
        password = quote_plus(cls.DB_PASSWORD)
        return (
            f"mysql+pymysql://{cls.DB_USER}:{password}"
            f"@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}"
        )

    # ------------------------------------------------------------------
    # Application / Logging
    # ------------------------------------------------------------------
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str  = os.getenv("LOG_FILE", "logs/payment_exception.log")

    # ------------------------------------------------------------------
    # API
    # ------------------------------------------------------------------
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))

    # ------------------------------------------------------------------
    # Exception / Retry Settings
    # ------------------------------------------------------------------
    EXCEPTION_ID_PREFIX: str      = os.getenv("EXCEPTION_ID_PREFIX", "EXC")
    MAX_RETRY_ATTEMPTS: int       = int(os.getenv("MAX_RETRY_ATTEMPTS", "3"))
    RETRY_BACKOFF_SECONDS: int    = int(os.getenv("RETRY_BACKOFF_SECONDS", "60"))
    LATENCY_BUDGET_MS: int        = int(os.getenv("LATENCY_BUDGET_MS", "5000"))

    # ------------------------------------------------------------------
    # Compliance thresholds
    # ------------------------------------------------------------------
    AML_AMOUNT_THRESHOLD: float   = float(os.getenv("AML_AMOUNT_THRESHOLD", "10000"))
    HIGH_VALUE_THRESHOLD: float   = float(os.getenv("HIGH_VALUE_THRESHOLD", "50000"))
    DUPLICATE_WINDOW_SECONDS: int = int(os.getenv("DUPLICATE_WINDOW_SECONDS", "300"))

    # ------------------------------------------------------------------
    # Rail cut-off times (24 h, UTC)
    # ------------------------------------------------------------------
    RAIL_CUTOFFS: dict = {
        "NEFT":     os.getenv("NEFT_CUTOFF",  "18:30"),
        "RTGS":     os.getenv("RTGS_CUTOFF",  "17:00"),
        "IMPS":     os.getenv("IMPS_CUTOFF",  "23:59"),
        "SWIFT":    os.getenv("SWIFT_CUTOFF", "15:00"),
        "UPI":      "23:59",
        "INTERNAL": "23:59",
    }

    # ------------------------------------------------------------------
    # Failure codes → FailureType mapping (from payment rail error codes)
    # ------------------------------------------------------------------
    FAILURE_CODE_MAP: dict = {
        "INSUF_FUNDS":          "INSUFFICIENT_FUNDS",
        "BALANCE_LOW":          "INSUFFICIENT_FUNDS",
        "INVALID_ACCOUNT":      "INCORRECT_BENEFICIARY",
        "INVALID_IFSC":         "INCORRECT_BENEFICIARY",
        "INVALID_UPI":          "INCORRECT_BENEFICIARY",
        "BENEFICIARY_MISMATCH": "INCORRECT_BENEFICIARY",
        "DUPLICATE_TXN":        "DUPLICATE_PAYMENT",
        "AML_HOLD":             "COMPLIANCE_HOLD",
        "SANCTIONS_HOLD":       "COMPLIANCE_HOLD",
        "COMPLIANCE_BLOCK":     "COMPLIANCE_HOLD",
        "NETWORK_ERROR":        "NETWORK_RAIL_FAILURE",
        "CLEARING_TIMEOUT":     "NETWORK_RAIL_FAILURE",
        "RAIL_UNAVAILABLE":     "NETWORK_RAIL_FAILURE",
        "CUTOFF_EXCEEDED":      "CUTOFF_TIME_MISS",
        "RETRY_PENDING":        "UNCERTAIN_RETRY_STATUS",
        "RETRY_UNKNOWN":        "UNCERTAIN_RETRY_STATUS",
    }

    @classmethod
    def validate(cls) -> bool:
        """Raise if required config is missing."""
        if not cls.OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY is required. Set it in .env or environment."
            )
        if not cls.DB_PASSWORD and cls.DB_USER != "root":
            raise ValueError("DB_PASSWORD is required for non-root DB user.")
        return True


config = Config()