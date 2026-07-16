"""One-time interactive OAuth setup for the Google Health API.

Google's Health API setup guide has you register a fixed
https://www.google.com redirect URI with nothing listening behind it — the
authorization code is read back from the browser's address bar by hand, so
this has to be run interactively (a real browser + your Google login), never
from Cloud Run. Run it once per environment (local dev is fine — the
refresh token it mints gets pushed to Secret Manager and used from there).

Usage:
    cd ingest
    .venv/bin/python scripts/google_health_auth.py
    .venv/bin/python scripts/google_health_auth.py --push --project my-gcp-project
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.pipelines.google_health.authorization_flow import GoogleHealthAuthFlow  # noqa: E402


def _tfvars_value(key: str) -> str | None:
    """Same lookup terraform/bootstrap.sh does, for --push's --project default."""
    tfvars_file = ROOT_DIR / "terraform" / "terraform.tfvars"
    if not tfvars_file.exists():
        return None
    match = re.search(rf'^\s*{key}\s*=\s*"([^"]*)"', tfvars_file.read_text(), re.MULTILINE)
    return match.group(1) if match else None


def _push_to_secret_manager(refresh_token: str, project: str) -> None:
    print(f"==> Pushing GOOGLE_HEALTH_REFRESH_TOKEN to Secret Manager (project={project})")
    subprocess.run(
        [
            "gcloud", "secrets", "versions", "add", "GOOGLE_HEALTH_REFRESH_TOKEN",
            f"--project={project}", "--data-file=-",
        ],
        input=refresh_token,
        text=True,
        check=True,
    )
    print("    done.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--push", action="store_true",
        help="Push the resulting refresh token straight to Secret Manager via gcloud "
             "instead of just printing it.",
    )
    parser.add_argument(
        "--project", default=None,
        help="GCP project id for --push (defaults to project_id in terraform/terraform.tfvars).",
    )
    args = parser.parse_args()

    load_dotenv(ROOT_DIR / ".env")

    import os
    client_id = os.environ.get("GOOGLE_HEALTH_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_HEALTH_CLIENT_SECRET")
    if not client_id or not client_secret:
        print(
            "GOOGLE_HEALTH_CLIENT_ID / GOOGLE_HEALTH_CLIENT_SECRET aren't set — "
            f"add them to {ROOT_DIR / '.env'} first.",
            file=sys.stderr,
        )
        sys.exit(1)

    flow = GoogleHealthAuthFlow(client_id, client_secret)
    tokens = flow.run()
    refresh_token = tokens["refresh_token"]

    if args.push:
        project = args.project or _tfvars_value("project_id")
        if not project:
            print(
                "Got a refresh token, but couldn't resolve a project for --push "
                "(pass --project explicitly). Printing it instead:",
                file=sys.stderr,
            )
            print(refresh_token)
            sys.exit(1)
        _push_to_secret_manager(refresh_token, project)
    else:
        print("\nrefresh_token:", refresh_token)
        print(
            "\nAdd this as GOOGLE_HEALTH_REFRESH_TOKEN in .env and re-run "
            "terraform/bootstrap.sh, or re-run this script with --push to send "
            "it straight to Secret Manager."
        )


if __name__ == "__main__":
    main()
