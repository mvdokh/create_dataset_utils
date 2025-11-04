#!/usr/bin/env python3
"""Count images in `images` and `labels/tongue` for each parent folder under a root.
Also count rows (excluding header) in `labels/jaw/jaw.csv` files.

Example usage (PowerShell):
  python .\count_mask_jaw.py
  python .\count_mask_jaw.py "C:\Users\wanglab\Desktop\Mask+Jaw" --csv counts.csv

The script prints a table and optionally writes a CSV with columns:
  folder, images_count, labels_tongue_count, jaw_csv_rows
"""

from pathlib import Path
import argparse
import csv
import sys

IMAGE_SUFFIXES = {'.png', '.jpg', '.jpeg', '.tif', '.tiff', '.bmp', '.gif', '.webp'}


def is_image(p: Path, suffixes):
    return p.is_file() and p.suffix.lower() in suffixes


def count_images_in_dir(dirpath: Path, suffixes):
    if not dirpath.exists() or not dirpath.is_dir():
        return 0
    return sum(1 for p in dirpath.iterdir() if is_image(p, suffixes))


def count_csv_rows(csv_path: Path):
    """Count rows in CSV file, excluding header (returns count - 1).
    
    Automatically detects delimiter and handles different line endings.
    """
    if not csv_path.exists() or not csv_path.is_file():
        return 0
    try:
        # Read file with universal newlines to handle different line endings
        with open(csv_path, 'r', encoding='utf-8', newline='') as f:
            # Read a sample to detect the delimiter
            sample = f.read(8192)  # Read up to 8KB for detection
            f.seek(0)  # Reset to beginning
            
            # Use csv.Sniffer to detect delimiter
            try:
                sniffer = csv.Sniffer()
                dialect = sniffer.sniff(sample, delimiters=',;\t|')
                reader = csv.reader(f, dialect=dialect)
            except csv.Error:
                # If sniffer fails, try common delimiters manually
                f.seek(0)
                first_line = f.readline()
                f.seek(0)
                
                # Count occurrences of common delimiters
                delimiters = [',', ';', '\t', '|']
                delimiter_counts = [(d, first_line.count(d)) for d in delimiters]
                best_delimiter = max(delimiter_counts, key=lambda x: x[1])[0]
                
                reader = csv.reader(f, delimiter=best_delimiter)
            
            # Count non-empty rows
            row_count = 0
            for row in reader:
                # Skip completely empty rows
                if any(cell.strip() for cell in row):
                    row_count += 1
            
            return max(0, row_count - 1)  # subtract header
    except Exception as e:
        print(f'Warning: Could not read {csv_path}: {e}', file=sys.stderr)
        return 0


def main():
    parser = argparse.ArgumentParser(description='Count images in parent folders and CSV rows')
    parser.add_argument('root', nargs='?',
                        default=r'C:\Users\wanglab\Desktop\Mask+Jaw',
                        help='Root directory containing parent folders (default: %(default)s)')
    parser.add_argument('--csv', '-c', help='Path to write CSV output')
    parser.add_argument('--extensions', '-e', nargs='+',
                        help='List of image extensions to include (with or without leading dot). Example: -e .png .jpg')
    args = parser.parse_args()

    root = Path(args.root)
    if not root.exists():
        print(f'Root path does not exist: {root}', file=sys.stderr)
        sys.exit(2)
    if not root.is_dir():
        print(f'Root is not a directory: {root}', file=sys.stderr)
        sys.exit(2)

    # prepare suffix set
    if args.extensions:
        exts = set()
        for x in args.extensions:
            if not x.startswith('.'):
                x = '.' + x
            exts.add(x.lower())
        suffixes = exts
    else:
        suffixes = IMAGE_SUFFIXES

    rows = []
    total_images = 0
    total_tongue = 0
    total_jaw_rows = 0

    # iterate immediate subdirectories of root
    children = sorted([p for p in root.iterdir() if p.is_dir()])
    for child in children:
        images_dir = child / 'images'
        labels_tongue_dir = child / 'labels' / 'tongue'
        jaw_csv_path = child / 'labels' / 'jaw' / 'jaw.csv'

        images_count = count_images_in_dir(images_dir, suffixes)
        tongue_count = count_images_in_dir(labels_tongue_dir, suffixes)
        jaw_rows = count_csv_rows(jaw_csv_path)

        rows.append((child.name, images_count, tongue_count, jaw_rows))

        total_images += images_count
        total_tongue += tongue_count
        total_jaw_rows += jaw_rows

    # print table header
    print(f"{'Folder':30} {'Images':>10} {'Tongue':>10} {'Jaw CSV Rows':>15}")
    print('-' * 67)
    for name, imcount, ltcount, jaw_rows in rows:
        print(f"{name:30} {imcount:10d} {ltcount:10d} {jaw_rows:15d}")
    print('-' * 67)
    print(f"{'TOTAL':30} {total_images:10d} {total_tongue:10d} {total_jaw_rows:15d}")

    if args.csv:
        try:
            with open(args.csv, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['folder', 'images_count', 'labels_tongue_count', 'jaw_csv_rows'])
                for r in rows:
                    writer.writerow(r)
            print(f'\nWrote CSV to {args.csv}')
        except Exception as e:
            print(f'Failed to write CSV {args.csv}: {e}', file=sys.stderr)
            sys.exit(3)


if __name__ == '__main__':
    main()
