import hashlib
import hmac
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Configuration – override via environment variables in CI
# ---------------------------------------------------------------------------
ENDPOINT = "https://b12.io/apply/submission"
SIGNING_SECRET = os.environ.get("SIGNING_SECRET", "hello-there-from-b12")

NAME          = os.environ.get("APPLICANT_NAME", "Tchokote Noubissie Hervé")
EMAIL         = os.environ.get("APPLICANT_EMAIL", "hervenoubs@gmail.com")
RESUME_LINK   = os.environ.get("RESUME_LINK",
                    "https://www.linkedin.com/in/hervenoubissie")
REPO_LINK     = os.environ.get("REPOSITORY_LINK",
                    "https://github.com/hervenoubs/b12-application")
ACTION_LINK   = os.environ.get("ACTION_RUN_LINK", "")   # injected by CI

# ---------------------------------------------------------------------------
# Build canonical payload
# ---------------------------------------------------------------------------
timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.") + \
            f"{datetime.now(timezone.utc).microsecond // 1000:03d}Z"

payload = {
    "action_run_link": ACTION_LINK,
    "email":           EMAIL,
    "name":            NAME,
    "repository_link": REPO_LINK,
    "resume_link":     RESUME_LINK,
    "timestamp":       timestamp,
}

# Compact, keys sorted alphabetically, UTF-8 encoded – no extra whitespace
body_bytes: bytes = json.dumps(
    payload, separators=(",", ":"), sort_keys=True
).encode("utf-8")

# ---------------------------------------------------------------------------
# HMAC-SHA256 signature
# ---------------------------------------------------------------------------
digest = hmac.new(
    SIGNING_SECRET.encode("utf-8"),
    body_bytes,
    hashlib.sha256,
).hexdigest()

signature_header = f"sha256={digest}"

# ---------------------------------------------------------------------------
# POST request (stdlib only – no third-party dependencies)
# ---------------------------------------------------------------------------
req = urllib.request.Request(
    ENDPOINT,
    data=body_bytes,
    headers={
        "Content-Type":   "application/json; charset=utf-8",
        "X-Signature-256": signature_header,
    },
    method="POST",
)

try:
    with urllib.request.urlopen(req) as response:
        status   = response.status
        raw_body = response.read().decode("utf-8")
except urllib.error.HTTPError as exc:
    status   = exc.code
    raw_body = exc.read().decode("utf-8")

print(f"HTTP {status}")
print(f"Response body: {raw_body}")

if status == 200:
    data = json.loads(raw_body)
    if data.get("success"):
        print(f"\n✅ Submission successful!")
        print(f"   Receipt: {data.get('receipt')}")
    else:
        print("⚠️  Server returned 200 but success=false")
        sys.exit(1)
else:
    print(f"❌ Submission failed (HTTP {status})")
    sys.exit(1)
