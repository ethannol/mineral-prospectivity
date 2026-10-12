"""Install the pinned baseline harness in its dedicated checkout, then sync uv.

Run with system Python; project dependencies are not needed for bootstrapping.
Existing dirty or differently pinned SDK checkouts are refused, never reset.
"""

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SDK_SHA = "a184e0732989373856039dea2919ccd96a88e8b1"
SDK_URL = "https://github.com/ethannol/cairn.git"


def git_output(directory, *args):
    return subprocess.check_output(["git", "-C", str(directory), *args], text=True).strip()


def bootstrap():
    sdk = ROOT.parent / "cairn-mineral-baseline"
    if sdk.exists():
        if git_output(sdk, "rev-parse", "HEAD") != SDK_SHA:
            raise RuntimeError(
                "dedicated cairn checkout has the wrong revision; refusing to change it"
            )
        if git_output(sdk, "status", "--porcelain"):
            raise RuntimeError("dedicated cairn checkout is dirty; refusing to change it")
    else:
        subprocess.run(["git", "clone", "--no-checkout", SDK_URL, str(sdk)], check=True)
        subprocess.run(["git", "-C", str(sdk), "checkout", "--detach", SDK_SHA], check=True)
        if git_output(sdk, "rev-parse", "HEAD") != SDK_SHA:
            raise RuntimeError("cloned cairn did not resolve to the intended pin")
    subprocess.run(["uv", "sync", "--locked", "--group", "dev"], cwd=ROOT, check=True)


if __name__ == "__main__":
    bootstrap()
