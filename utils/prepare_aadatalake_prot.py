#!/usr/bin/env python3
"""Regenerate the two small proteomics indexes; source CSVs are never modified.

Specify a study directory (required; indexes are written beside the study CSVs):
    python3 utils/prepare_aadatalake_prot.py /path/to/aaprotlake
An optional second argument selects a separate output directory:
    python3 utils/prepare_aadatalake_prot.py /path/to/studies /path/to/index

Existing indexes are replaced only after all source files pass basic checks.
PseudoAge is preserved when supplied; otherwise it is set to the placeholder 0.
Deploy the indexes together with their study CSVs and invalidate the app cache.
metadata.csv and file_index.csv are reserved output names and excluded from input.
"""

import argparse
from collections import Counter
import csv
from pathlib import Path
import tempfile


META = ("study", "genotype", "condition", "time", "day", "note")
SAMPLE_COLUMNS = ("sample_id", *META, "PseudoAge", "source_file", "source_row")
FILE_COLUMNS = ("source_file", "study", "sample_count", "gene_count", "size_bytes")
INDEX_FILES = ("metadata.csv", "file_index.csv")


def prepare(source, output=None):
    output = source if output is None else output
    files = sorted(path for path in source.glob("*.csv") if path.name not in INDEX_FILES)
    if not files:
        raise ValueError(f"No study CSVs found in {source}")
    samples, file_index, seen = [], [], set()
    expected_genes = None
    for path in files:
        before = path.stat()
        studies = Counter()
        with path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.reader(handle, strict=True)
            header = next(reader, [])
            if not header or len(header) != len(set(header)) or not set(META).issubset(header):
                raise ValueError(f"{path.name}: missing metadata or duplicate column names")
            if header[0] not in ("", "sample_id"):
                raise ValueError(f"{path.name}: expected sample IDs in the first column")
            genes = [name for name in header if name.startswith("WBGene")]
            if not genes or (expected_genes is not None and genes != expected_genes):
                raise ValueError(f"{path.name}: missing or inconsistent gene columns")
            expected_genes = genes
            positions = {name: header.index(name) for name in META}
            age_position = header.index("PseudoAge") if "PseudoAge" in header else None
            for number, row in enumerate(reader, 2):
                if len(row) != len(header):
                    raise ValueError(f"{path.name}, record {number}: incorrect number of fields")
                sample = row[0]
                values = {name: row[pos] for name, pos in positions.items()}
                if not sample.strip() or not values["study"].strip() or sample in seen:
                    raise ValueError(f"{path.name}, record {number}: empty sample/study or duplicate sample ID")
                seen.add(sample)
                studies[values["study"]] += 1
                samples.append({"sample_id": sample, **values,
                                "PseudoAge": row[age_position] if age_position is not None else 0,
                                "source_file": path.name, "source_row": number})
        after = path.stat()
        if not studies or (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise ValueError(f"{path.name}: empty file or source changed during reading")
        for study, count in sorted(studies.items()):
            file_index.append(dict(zip(FILE_COLUMNS, (path.name, study, count, len(genes), before.st_size))))

    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output) as temporary:
        for name, columns, rows in (("metadata.csv", SAMPLE_COLUMNS, samples),
                                    ("file_index.csv", FILE_COLUMNS, file_index)):
            with (Path(temporary) / name).open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=columns)
                writer.writeheader()
                writer.writerows(rows)
        for name in INDEX_FILES:
            (Path(temporary) / name).replace(output / name)
    print(f"Indexed {len(samples):,} samples from {len(files)} files into {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Directory containing the study CSVs (required)")
    parser.add_argument("output", nargs="?", type=Path, help="Defaults to the source directory")
    args = parser.parse_args()
    try:
        prepare(args.source, args.output)
    except (ValueError, OSError, csv.Error) as error:
        parser.exit(1, f"Index preparation failed: {error}\n")
