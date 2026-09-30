"""Check the demo Caddy allowlist against Cloudflare's published ranges."""

import argparse
import ipaddress
import re
import sys
from pathlib import Path
from urllib.request import Request, urlopen


IPV4_URL = "https://www.cloudflare.com/ips-v4/"
IPV6_URL = "https://www.cloudflare.com/ips-v6/"
DEFAULT_CADDYFILE = (
    Path(__file__).resolve().parents[2] / "deployment/caddy/Caddyfile.demo"
)


def parse_ranges(text, source, version=None):
    """Parse and validate a nonempty list of CIDR ranges."""
    ranges = set()
    for token in text.split():
        try:
            network = ipaddress.ip_network(token, strict=True)
        except ValueError as exc:
            raise ValueError(f"{source}: invalid IP range {token!r}") from exc
        if version is not None and network.version != version:
            raise ValueError(
                f"{source}: unexpected IPv{network.version} range {token!r}"
            )
        if network in ranges:
            raise ValueError(f"{source}: duplicate IP range {token!r}")
        ranges.add(network)
    if not ranges:
        raise ValueError(f"{source}: empty IP range list")
    return ranges


def compare_ranges(caddyfile, ipv4_text, ipv6_text):
    """Return (ranges missing from Caddy, obsolete ranges in Caddy)."""
    matches = re.findall(
        r"^\s*not remote_ip\s+([^#\n]+)", caddyfile, re.MULTILINE
    )
    if len(matches) != 1:
        raise ValueError(
            f"expected one 'not remote_ip' allowlist, found {len(matches)}"
        )

    configured = parse_ranges(matches[0], "Caddyfile")
    published = parse_ranges(ipv4_text, IPV4_URL, version=4)
    published |= parse_ranges(ipv6_text, IPV6_URL, version=6)
    return published - configured, configured - published


def download_ranges(url):
    request = Request(
        url, headers={"User-Agent": "NexusLIMS-CDCS-Cloudflare-IP-check"}
    )
    with urlopen(request, timeout=20) as response:
        return response.read().decode("utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--caddyfile", type=Path, default=DEFAULT_CADDYFILE)
    args = parser.parse_args()

    try:
        configured = args.caddyfile.read_text(encoding="utf-8")
        missing, obsolete = compare_ranges(
            configured,
            download_ranges(IPV4_URL),
            download_ranges(IPV6_URL),
        )
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"Could not check Cloudflare IP ranges: {exc}", file=sys.stderr)
        return 2

    if missing or obsolete:
        print(f"Cloudflare IP ranges differ from {args.caddyfile}:")
        for network in sorted(
            missing, key=lambda item: (item.version, int(item.network_address))
        ):
            print(f"  Add: {network}")
        for network in sorted(
            obsolete,
            key=lambda item: (item.version, int(item.network_address)),
        ):
            print(f"  Remove: {network}")
        return 1

    print(f"Cloudflare IP ranges match {args.caddyfile}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
