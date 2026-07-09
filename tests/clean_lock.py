import os
import shutil
from pathlib import Path
import logging


def clean_reflex_artifacts():
    """
    Utility script to remove stale Reflex lockfiles and artifacts.
    This resolves the 'persisted lockfile is out of sync' error.
    """
    root_dir = Path(__file__).parent.parent
    lock_dir = root_dir / "reflex.lock"

    if lock_dir.exists() and lock_dir.is_dir():
        print(f"Removing stale lock directory: {lock_dir}")
        try:
            shutil.rmtree(lock_dir)
            print("Successfully removed reflex.lock directory.")
        except Exception as e:
            logging.exception("Unexpected error")
            print(f"Failed to remove reflex.lock: {e}")
    else:
        print("No reflex.lock directory found. Environment is clean.")

    # Also clean .web directory if exists to ensure a full fresh rebuild
    web_dir = root_dir / ".web"
    if web_dir.exists() and web_dir.is_dir():
        print(f"Removing .web directory for a fresh build: {web_dir}")
        try:
            shutil.rmtree(web_dir)
            print("Successfully removed .web directory.")
        except Exception as e:
            logging.exception("Unexpected error")
            print(f"Failed to remove .web: {e}")


if __name__ == "__main__":
    clean_reflex_artifacts()
