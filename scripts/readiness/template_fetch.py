#!/usr/bin/env python3
"""Download a journal template from an explicitly verified official source.

The command does not discover or guess publisher URLs. The Agent/user must first
verify the current official template page. `--verified-official` records that
provenance decision; without it the downloaded material remains UNVERIFIED and
preflight must not treat it as an official journal template.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sys
from urllib.parse import urlparse
import zipfile

import requests


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--journal", required=True)
    ap.add_argument("--template-url", required=True)
    ap.add_argument("--official-source-url", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--verified-official", action="store_true")
    ap.add_argument("--expected-sha256")
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    name = Path(urlparse(args.template_url).path).name or "journal-template.bin"
    target = out / name
    r = requests.get(args.template_url, timeout=45, allow_redirects=True)
    r.raise_for_status()
    target.write_bytes(r.content)
    digest = sha256(target)
    integrity_ok = True
    if args.expected_sha256:
        integrity_ok = digest.lower() == args.expected_sha256.lower()

    extracted = []
    if target.suffix.lower() == ".zip" and integrity_ok:
        extract_dir = out / "template"
        extract_dir.mkdir(exist_ok=True)
        with zipfile.ZipFile(target) as zf:
            # Zip-slip guard.
            for member in zf.infolist():
                dest = (extract_dir / member.filename).resolve()
                if extract_dir.resolve() not in dest.parents and dest != extract_dir.resolve():
                    raise RuntimeError(f"unsafe zip member: {member.filename}")
            zf.extractall(extract_dir)
            extracted = [x.filename for x in zf.infolist()]

    manifest = {
        "schema_version": "1.0",
        "journal": args.journal,
        "downloaded_at": datetime.now(timezone.utc).isoformat(),
        "template_url": args.template_url,
        "official_source_url": args.official_source_url,
        "source_verified_by_agent_or_user": bool(args.verified_official),
        "status": "VERIFIED_OFFICIAL_SOURCE" if args.verified_official and integrity_ok else "UNVERIFIED",
        "downloaded_file": str(target),
        "sha256": digest,
        "expected_sha256": args.expected_sha256,
        "integrity_ok": integrity_ok,
        "extracted_members": extracted,
        "note": "Official status is provenance-based; this tool does not infer publisher legitimacy from the URL alone.",
    }
    with (out / "template-provenance.json").open("w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(out / "template-provenance.json")
    return 0 if manifest["status"] == "VERIFIED_OFFICIAL_SOURCE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
