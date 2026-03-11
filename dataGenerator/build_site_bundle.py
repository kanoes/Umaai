#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from backend.site_data import write_site_dataset


def main() -> None:
    parser = argparse.ArgumentParser(description="Build standardized site dataset files for Umaai.")
    parser.add_argument("--output-dir", default="data", help="Output directory for derived site files")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    dataset = write_site_dataset(output_dir=output_dir)
    manifest = dataset["manifest"]
    print(
        "Site dataset built:",
        output_dir.as_posix(),
        f"(generated_at={manifest.get('generated_at_utc')}, total={manifest.get('counts', {}).get('total_characters', 0)})",
    )


if __name__ == "__main__":
    main()
