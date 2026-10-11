#!/usr/bin/env python3
"""
Check for TA_VERSION state.

install with:
pre-commit install --hook-type pre-commit --hook-type pre-push
"""

import os
import re
import subprocess
import sys

SETTINGS_PATH = "backend/config/settings.py"
VERSION_RE = re.compile(r'^TA_VERSION = "([^"]+)"$', re.MULTILINE)
RELEASE_TAG_RE = re.compile(r"^v\d+\.\d+\.\d+$")
UNSTABLE_VERSION_RE = re.compile(r"^v\d+\.\d+\.\d+-unstable$")


def git(*args):
    """base command"""
    return subprocess.run(
        ["git", *args],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def fail(message):
    """error message"""
    print(f"TA version check failed: {message}", file=sys.stderr)
    raise SystemExit(1)


def version_at(revision):
    """find TA_VERSION"""
    settings = git("show", f"{revision}:{SETTINGS_PATH}")
    match = VERSION_RE.search(settings)
    if not match:
        fail(f"could not find TA_VERSION in {SETTINGS_PATH} at {revision}")

    return match.group(1)


def main():
    """entry point"""
    remote_ref = os.environ.get("PRE_COMMIT_REMOTE_BRANCH", "")
    pushed_revision = os.environ.get("PRE_COMMIT_TO_REF", "")

    if not remote_ref or not pushed_revision:
        fail("pre-push environment variables are missing")

    if set(pushed_revision) == {"0"}:
        return  # Ref deletion.

    commit = git("rev-parse", f"{pushed_revision}^{{commit}}")
    version = version_at(commit)

    if remote_ref.startswith("refs/tags/"):
        tag = remote_ref.removeprefix("refs/tags/")
        if RELEASE_TAG_RE.fullmatch(tag) and version != tag:
            fail(
                f"tag {tag} points to TA_VERSION {version}; "
                f"expected {tag}"
            )

    if remote_ref == "refs/heads/master":
        subject = git("show", "-s", "--format=%s", commit)
        if subject.endswith("#build"):
            if not UNSTABLE_VERSION_RE.fullmatch(version):
                fail(
                    f"master commit ends in #build but TA_VERSION "
                    f"is {version}; expected vX.Y.Z-unstable"
                )


if __name__ == "__main__":
    main()
