"""CSAM detection stage.

IMPORTANT: NudeNet is a nudity classifier, not a CSAM detector, and must
never be treated as one. Real CSAM handling requires an authorized
hash-matching provider (Thorn Safer, Google CSAI Match, Microsoft PhotoDNA)
or NCMEC's hash list. Registering with one of these is an independent
legal/business process that this repo cannot perform — it must be pursued
outside of code.

This module defines the interface that stage will implement, plus a
NotConfigured placeholder so the pipeline's shape is correct today. Swapping
in a real provider later only requires a new CSAMScanner subclass and config
wiring; pipeline.py, models.py, and the DB schema do not change.
"""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CSAMScanResult:
    status: str  # not_configured|pending|clear|match|error
    provider: str
    raw: dict | None = None


class CSAMScanner:
    def scan(self, path):
        raise NotImplementedError


class NotConfiguredCSAMScanner(CSAMScanner):
    """Performs no detection of any kind. This is a structural placeholder,
    not a safeguard — do not treat its result as a pass/clear signal."""

    def scan(self, path):
        logger.warning(
            "CSAM scanning is NOT configured for %s — no hash-matching "
            "provider is wired in. This result is not a safety signal.",
            path,
        )
        return CSAMScanResult(status="not_configured", provider="not_configured")


def get_scanner():
    return NotConfiguredCSAMScanner()
