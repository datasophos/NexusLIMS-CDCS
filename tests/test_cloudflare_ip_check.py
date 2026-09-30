"""Checks for drift in the demo Caddy Cloudflare origin allowlist."""

import importlib.util
import unittest
from pathlib import Path

SCRIPT = (
    Path(__file__).resolve().parents[1]
    / ".github/scripts/check_cloudflare_ips.py"
)
spec = importlib.util.spec_from_file_location("check_cloudflare_ips", SCRIPT)
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)


class CloudflareIPCheckTests(unittest.TestCase):
    def test_reports_new_and_removed_cloudflare_ranges(self):
        caddyfile = """@directAdmin {
            path /staff-admin /staff-admin/*
            not remote_ip 203.0.113.0/24 2001:db8::/32
        }"""

        missing, obsolete = check.compare_ranges(
            caddyfile,
            "203.0.113.0/24\n198.51.100.0/24\n",
            "2001:db8:1::/48\n",
        )

        self.assertEqual(
            {str(ip) for ip in missing},
            {"198.51.100.0/24", "2001:db8:1::/48"},
        )
        self.assertEqual({str(ip) for ip in obsolete}, {"2001:db8::/32"})

    def test_rejects_missing_origin_allowlist(self):
        with self.assertRaisesRegex(ValueError, "not remote_ip"):
            check.compare_ranges(
                "respond /staff-admin 403", "203.0.113.0/24", "2001:db8::/32"
            )

    def test_rejects_invalid_cloudflare_response(self):
        caddyfile = "not remote_ip 203.0.113.0/24 2001:db8::/32"

        with self.assertRaisesRegex(ValueError, "invalid"):
            check.compare_ranges(caddyfile, "not an IP range", "2001:db8::/32")
