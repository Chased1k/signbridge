#!/usr/bin/env python3
"""Build a structured index of the StudioGalt ASL dictionary archive."""

import argparse
import json
import re
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DICTIONARY = PROJECT_ROOT / "data" / "studiogalt" / "SG ASL Dictionary"
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "sign_index.json"

FOLDER_RE = re.compile(
    r"^SG ASL (?P<label>.+?) (?P<date>\d{4}-\d{1,2}-\d{1,2})(?: Upload)?$"
)
EXPLICIT_ALT_RE = re.compile(r"^(?P<name>.+?) Alt(?: (?P<number>\d+))?$", re.IGNORECASE)
NUMBERED_RE = re.compile(r"^(?P<name>.+?) (?P<number>\d+)$")
FBX_SUFFIXES = {
    " No Mesh Full.fbx": "no_mesh_full",
    " No Mesh Mini.fbx": "no_mesh_mini",
    " No Mesh Mixamo.fbx": "no_mesh_mixamo",
    " Mesh.fbx": "mesh",
}


def parse_folder_name(folder_name):
    match = FOLDER_RE.match(folder_name)
    if match:
        label = match.group("label")
        year, month, day = (int(part) for part in match.group("date").split("-"))
        recorded = date(year, month, day).isoformat()
    elif folder_name.startswith("SG ASL ") and folder_name.endswith(" Upload"):
        label = folder_name[len("SG ASL ") : -len(" Upload")]
        recorded = None
    else:
        return None
    alt_match = EXPLICIT_ALT_RE.match(label)
    if alt_match:
        return {
            "name": alt_match.group("name"),
            "alt_number": int(alt_match.group("number") or 1),
            "variant_label": label,
            "date": recorded,
        }
    numbered_match = NUMBERED_RE.match(label)
    if numbered_match:
        return {
            "name": numbered_match.group("name"),
            "alt_number": int(numbered_match.group("number")),
            "variant_label": label,
            "date": recorded,
        }
    return {"name": label, "alt_number": None, "variant_label": label, "date": recorded}


def classify_fbx(filename):
    lowered = filename.lower()
    for suffix, key in FBX_SUFFIXES.items():
        if lowered.endswith(suffix.lower()):
            return key
    return None


def relative_path(path):
    return path.relative_to(PROJECT_ROOT).as_posix()


def build_index(dictionary_root):
    signs = {}
    per_letter = Counter()
    skipped = []
    naming_anomalies = []
    all_dates = []

    letter_dirs = sorted(
        path for path in dictionary_root.iterdir() if path.is_dir() and path.name.startswith("ASL ")
    )
    for letter_dir in letter_dirs:
        for sign_dir in sorted(path for path in letter_dir.iterdir() if path.is_dir()):
            parsed = parse_folder_name(sign_dir.name)
            if parsed is None:
                skipped.append(relative_path(sign_dir))
                continue
            if parsed["date"] is None or not sign_dir.name.endswith(" Upload"):
                naming_anomalies.append(relative_path(sign_dir))
            fbx_files = {key: None for key in FBX_SUFFIXES.values()}
            for candidate in sign_dir.rglob("*.fbx"):
                kind = classify_fbx(candidate.name)
                if kind and fbx_files[kind] is None:
                    fbx_files[kind] = relative_path(candidate)

            variant = {
                "alt_number": parsed["alt_number"],
                "variant_label": parsed["variant_label"],
                "date": parsed["date"],
                "letter_directory": letter_dir.name,
                "directory": relative_path(sign_dir),
                "fbx": fbx_files,
            }
            entry = signs.setdefault(parsed["name"], {"name": parsed["name"], "variants": []})
            entry["variants"].append(variant)
            per_letter[letter_dir.name] += 1
            if parsed["date"] is not None:
                all_dates.append(parsed["date"])

    for entry in signs.values():
        entry["variants"].sort(
            key=lambda item: (
                item["alt_number"] is not None,
                item["alt_number"] if item["alt_number"] is not None else 0,
                item["date"] or "",
            )
        )

    total_entries = sum(per_letter.values())
    multiple_alts = sorted(name for name, entry in signs.items() if len(entry["variants"]) > 1)
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "archive_root": relative_path(dictionary_root.parent),
        "dictionary_root": relative_path(dictionary_root),
        "statistics": {
            "total_sign_entries": total_entries,
            "unique_sign_names": len(signs),
            "signs_with_multiple_variants": len(multiple_alts),
            "multiple_variant_sign_names": multiple_alts,
            "date_range": {
                "earliest": min(all_dates) if all_dates else None,
                "latest": max(all_dates) if all_dates else None,
            },
            "signs_per_letter": dict(sorted(per_letter.items())),
            "skipped_directory_count": len(skipped),
            "skipped_directories": skipped,
            "naming_anomaly_count": len(naming_anomalies),
            "naming_anomalies": naming_anomalies,
        },
        "signs": dict(sorted(signs.items(), key=lambda item: item[0].casefold())),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dictionary", type=Path, default=DEFAULT_DICTIONARY)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    dictionary_root = args.dictionary.resolve()
    if not dictionary_root.is_dir():
        raise SystemExit(f"Dictionary not found: {dictionary_root}")

    index = build_index(dictionary_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    stats = index["statistics"]
    print(f"Index written: {args.output}")
    print(f"Total signs: {stats['total_sign_entries']}")
    print(f"Unique sign names: {stats['unique_sign_names']}")
    print(f"Signs with multiple alts/variants: {stats['signs_with_multiple_variants']}")
    print(f"Date range: {stats['date_range']['earliest']} to {stats['date_range']['latest']}")
    print("Signs per letter:")
    for letter, count in stats["signs_per_letter"].items():
        print(f"  {letter}: {count}")
    print(f"Skipped directories: {stats['skipped_directory_count']}")
    print(f"Naming anomalies retained: {stats['naming_anomaly_count']}")


if __name__ == "__main__":
    main()
