import os
import logging


def delete_unwanted_files(root_directory, prefixes=['.DS', '._'], dry_run=False):
    """
    Recursively delete files with specified prefixes from a directory and all its subdirectories.
    
    Args:
        root_directory (str): The root directory to start the search
        prefixes (list): List of prefixes to match for deletion (default: ['.DS', '._'])
        dry_run (bool): If True, only print files that would be deleted without actually deleting
    
    Returns:
        dict: Dictionary with 'deleted' and 'errors' counts
    """
    deleted_count = 0
    error_count = 0
    
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    logger = logging.getLogger(__name__)
    
    if not os.path.exists(root_directory):
        logger.error(f"Directory does not exist: {root_directory}")
        return {'deleted': 0, 'errors': 1}
    
    logger.info(f"{'DRY RUN: ' if dry_run else ''}Scanning directory: {root_directory}")
    logger.info(f"Looking for files with prefixes: {prefixes}")
    
    # Walk through all directories and subdirectories
    for root, dirs, files in os.walk(root_directory):
        for file in files:
            # Check if file starts with any of the specified prefixes
            if any(file.startswith(prefix) for prefix in prefixes):
                file_path = os.path.join(root, file)
                try:
                    if dry_run:
                        logger.info(f"Would delete: {file_path}")
                    else:
                        os.remove(file_path)
                        logger.info(f"Deleted: {file_path}")
                    deleted_count += 1
                except Exception as e:
                    logger.error(f"Error deleting {file_path}: {e}")
                    error_count += 1
    
    logger.info(f"{'DRY RUN: ' if dry_run else ''}Operation completed. Files {'found' if dry_run else 'deleted'}: {deleted_count}, Errors: {error_count}")
    
    return {'deleted': deleted_count, 'errors': error_count}


def clean_directory(directory_path, dry_run=True):
    """
    Convenience function to clean a directory of .DS and ._ files.
    
    Args:
        directory_path (str): Path to the directory to clean
        dry_run (bool): If True, only shows what would be deleted (default: True for safety)
    
    Returns:
        dict: Dictionary with 'deleted' and 'errors' counts
    """
    return delete_unwanted_files(directory_path, dry_run=dry_run)


try:
    from PIL import Image
except Exception:  # pragma: no cover - pillow may not be installed in all environments
    Image = None


def convert_tongue_labels_to_png(root_directory, remove_original=True, verbose=True):
    """Convert all images inside any "labels/tongue" folders under ``root_directory`` to PNG.

    This walks the tree rooted at ``root_directory``. Whenever it finds a folder named
    "tongue" whose parent folder is named "labels", it will convert any non-PNG files in
    that folder to PNG using Pillow.

    Args:
        root_directory (str): Root folder to search under.
        remove_original (bool): If True, remove the original file after successful conversion.
        verbose (bool): If True, log conversions to the standard logger.

    Returns:
        dict: Summary with keys: converted (int), skipped (int), errors (list of (path, error_str)).
    """
    import logging
    import os

    logger = logging.getLogger(__name__)
    if verbose:
        logging.basicConfig(level=logging.INFO, format='%(message)s')

    if Image is None:
        raise RuntimeError('Pillow is required for image conversion. Please install with `pip install pillow`.')

    if not os.path.exists(root_directory):
        raise ValueError(f'Root directory does not exist: {root_directory}')

    converted = 0
    skipped = 0
    errors = []

    # Walk the tree and look for folders named 'tongue' whose parent is 'labels'
    for dirpath, dirnames, filenames in os.walk(root_directory):
        base = os.path.basename(dirpath).lower()
        parent = os.path.basename(os.path.dirname(dirpath)).lower()
        if base == 'tongue' and parent == 'labels':
            if verbose:
                logger.info(f'Processing folder: {dirpath}')

            for fname in filenames:
                src_path = os.path.join(dirpath, fname)
                if not os.path.isfile(src_path):
                    continue
                ext = os.path.splitext(fname)[1].lower()
                if ext == '.png':
                    skipped += 1
                    continue

                try:
                    with Image.open(src_path) as im:
                        # Choose an output mode that preserves alpha if present
                        if im.mode in ('RGBA', 'LA') or (im.mode == 'P' and 'transparency' in im.info):
                            out_mode = 'RGBA'
                        else:
                            out_mode = 'RGB'
                        converted_im = im.convert(out_mode)

                        dst_path = os.path.splitext(src_path)[0] + '.png'
                        # Save as PNG
                        converted_im.save(dst_path, format='PNG', optimize=True)

                    if remove_original:
                        try:
                            os.remove(src_path)
                        except Exception:
                            # If removal fails, leave the file but still count as converted
                            logger.warning(f'Could not remove original file: {src_path}')

                    converted += 1
                    if verbose:
                        logger.info(f'Converted: {src_path} -> {dst_path}')

                except Exception as e:
                    errors.append((src_path, str(e)))
                    logger.exception(f'Failed to convert {src_path}: {e}')

    return {'converted': converted, 'skipped': skipped, 'errors': errors}


def delete_non_png_in_tongue(root_directory, dry_run=False, verbose=True):
    """Delete any files that are not .png inside any `labels/tongue` folders under root.

    Args:
        root_directory (str): Root folder to search under.
        dry_run (bool): If True, only log what would be deleted.
        verbose (bool): If True, print progress messages.

    Returns:
        dict: {'deleted': int, 'errors': [(path, err_str), ...]}
    """
    import logging
    import os

    logger = logging.getLogger(__name__)
    if verbose:
        logging.basicConfig(level=logging.INFO, format='%(message)s')

    if not os.path.exists(root_directory):
        raise ValueError(f'Root directory does not exist: {root_directory}')

    deleted = 0
    errors = []

    for dirpath, dirnames, filenames in os.walk(root_directory):
        base = os.path.basename(dirpath).lower()
        parent = os.path.basename(os.path.dirname(dirpath)).lower()
        if base == 'tongue' and parent == 'labels':
            if verbose:
                logger.info(f'Checking folder for non-PNG files: {dirpath}')

            for fname in filenames:
                if fname.lower().endswith('.png'):
                    continue
                src_path = os.path.join(dirpath, fname)
                try:
                    if dry_run:
                        logger.info(f'Would delete: {src_path}')
                    else:
                        os.remove(src_path)
                        if verbose:
                            logger.info(f'Deleted: {src_path}')
                    deleted += 1
                except Exception as e:
                    errors.append((src_path, str(e)))
                    logger.exception(f'Could not remove original file: {src_path}: {e}')

    return {'deleted': deleted, 'errors': errors}


def replace_frame_numbers_with_image_names(jaw_csv_path, images_folder_path, output_csv_path=None):
    """Replace the 'frame' column values in a Jaw CSV with the corresponding image basenames

    This reads a CSV with header 'frame,x,y' where frame numbers represent indices into
    a chronologically sorted list of images. It replaces the frame number with the actual
    image basename at that index. Frame numbers can have gaps (e.g., 89, 106, 120) because
    not all images have keypoints annotated.

    Args:
        jaw_csv_path (str): Path to the jaw CSV file to modify.
        images_folder_path (str): Path to the images folder containing image files.
        output_csv_path (str|None): Path to write the modified CSV. If None,
            will overwrite ``jaw_csv_path``.

    Returns:
        dict: Summary with keys: 'rows', 'images_found', 'written' (bool),
              'output_path' (str), 'error' (str or None), 'max_frame_index' (int or None)
    """
    import csv

    # Basic validation
    if not os.path.exists(jaw_csv_path):
        return {'rows': 0, 'images_found': 0, 'written': False, 'output_path': None,
                'error': f'jaw_csv_path does not exist: {jaw_csv_path}', 'max_frame_index': None}

    if not os.path.isdir(images_folder_path):
        return {'rows': 0, 'images_found': 0, 'written': False, 'output_path': None,
                'error': f'images_folder_path does not exist or is not a directory: {images_folder_path}',
                'max_frame_index': None}

    # List files in images folder and extract basenames
    all_files = [f for f in os.listdir(images_folder_path) if os.path.isfile(os.path.join(images_folder_path, f))]
    if not all_files:
        return {'rows': 0, 'images_found': 0, 'written': False, 'output_path': None,
                'error': 'No files found in images folder', 'max_frame_index': None}

    # Map to basenames without extension
    basenames = [os.path.splitext(f)[0] for f in all_files]

    # Try to sort basenames numerically when possible, otherwise lexicographically
    def sort_key(s):
        try:
            return (0, int(s))
        except Exception:
            return (1, s)

    basenames_sorted = sorted(basenames, key=sort_key)

    # Read jaw csv rows
    rows = []
    with open(jaw_csv_path, 'r', newline='') as fh:
        reader = csv.reader(fh)
        try:
            header = next(reader)
        except StopIteration:
            return {'rows': 0, 'images_found': len(basenames_sorted), 'written': False,
                    'output_path': None, 'error': 'Empty CSV', 'max_frame_index': None}
        # Keep the rest
        for r in reader:
            if not r:
                continue
            rows.append(r)

    num_rows = len(rows)
    num_images = len(basenames_sorted)

    # Find the maximum frame index used in the CSV
    max_frame_index = None
    try:
        frame_indices = [int(row[0]) for row in rows if row[0].strip()]
        max_frame_index = max(frame_indices) if frame_indices else None
    except (ValueError, IndexError):
        return {'rows': num_rows, 'images_found': num_images, 'written': False, 'output_path': None,
                'error': 'Could not parse frame numbers as integers', 'max_frame_index': None}

    # Check if we have enough images for the maximum frame index
    if max_frame_index is not None and max_frame_index >= num_images:
        return {'rows': num_rows, 'images_found': num_images, 'written': False, 'output_path': None,
                'error': f'Not enough images. Max frame index is {max_frame_index} but only have {num_images} images (need at least {max_frame_index + 1})',
                'max_frame_index': max_frame_index}

    # Replace frame indices with corresponding image basenames
    new_rows = []
    for row in rows:
        try:
            frame_index = int(row[0])
            new_frame = basenames_sorted[frame_index]
            # Ensure row has at least 3 columns; if not, pad with empty strings
            while len(row) < 3:
                row.append('')
            new_rows.append([new_frame, row[1], row[2]])
        except (ValueError, IndexError) as e:
            return {'rows': num_rows, 'images_found': num_images, 'written': False, 'output_path': None,
                    'error': f'Error processing row {row}: {e}', 'max_frame_index': max_frame_index}

    # Decide output path
    if output_csv_path is None:
        output_csv_path = jaw_csv_path

    # Write CSV
    try:
        with open(output_csv_path, 'w', newline='') as fh:
            writer = csv.writer(fh)
            writer.writerow(header)
            for r in new_rows:
                writer.writerow(r)
        return {'rows': num_rows, 'images_found': num_images, 'written': True, 
                'output_path': output_csv_path, 'error': None, 'max_frame_index': max_frame_index}
    except Exception as e:
        return {'rows': num_rows, 'images_found': num_images, 'written': False, 
                'output_path': output_csv_path, 'error': str(e), 'max_frame_index': max_frame_index}


def count_csv_rows(csv_path):
    """Count rows in CSV file, excluding header (returns count - 1).
    
    Automatically detects delimiter (comma, space, semicolon, tab, pipe) 
    and handles different line endings.
    
    Args:
        csv_path: Path object or string path to CSV file
        
    Returns:
        tuple: (row_count, status_message) where row_count is None if error occurred
    """
    import csv
    from pathlib import Path
    
    csv_path = Path(csv_path)
    if not csv_path.exists() or not csv_path.is_file():
        return None, "File not found"
    
    try:
        with open(csv_path, 'r', encoding='utf-8', newline='') as f:
            sample = f.read(8192)
            f.seek(0)
            
            try:
                sniffer = csv.Sniffer()
                dialect = sniffer.sniff(sample, delimiters=', ;\t|')
                reader = csv.reader(f, dialect=dialect)
            except csv.Error:
                f.seek(0)
                first_line = f.readline()
                f.seek(0)
                
                delimiters = [',', ' ', ';', '\t', '|']
                delimiter_counts = [(d, first_line.count(d)) for d in delimiters]
                best_delimiter = max(delimiter_counts, key=lambda x: x[1])[0]
                
                reader = csv.reader(f, delimiter=best_delimiter)
            
            row_count = 0
            for row in reader:
                if any(cell.strip() for cell in row):
                    row_count += 1
            
            return max(0, row_count - 1), "Success"
    except Exception as e:
        return None, f"Error: {e}"


def scan_csv_in_labels_subfolders(root_dir, subfolder_name='jaw'):
    """Scan folders for CSV files in labels/<subfolder_name> and count rows.
    
    Args:
        root_dir: Path to root directory containing subfolders
        subfolder_name: Name of subfolder within labels to search (default: 'jaw')
        
    Returns:
        dict: Contains 'results' (list of dicts), 'total_rows', 'folders_found', 'folders_missing'
    """
    from pathlib import Path
    
    root = Path(root_dir)
    if not root.exists():
        raise FileNotFoundError(f'Root path does not exist: {root}')
    if not root.is_dir():
        raise NotADirectoryError(f'Root is not a directory: {root}')
    
    results = []
    total_rows = 0
    folders_found = 0
    folders_missing = 0
    
    children = sorted([p for p in root.iterdir() if p.is_dir()])
    
    print(f"Scanning {len(children)} folders in {root_dir}")
    print(f"Looking for CSV files in: labels/{subfolder_name}/\n")
    
    for child in children:
        target_dir = child / 'labels' / subfolder_name
        
        if not target_dir.exists() or not target_dir.is_dir():
            results.append({
                'Folder': child.name,
                'CSV File': 'N/A',
                'Rows (excluding header)': 0,
                'Status': f'labels/{subfolder_name} directory not found'
            })
            folders_missing += 1
            continue
        
        csv_files = list(target_dir.glob('*.csv'))
        
        if not csv_files:
            results.append({
                'Folder': child.name,
                'CSV File': 'N/A',
                'Rows (excluding header)': 0,
                'Status': 'No CSV files found'
            })
            folders_missing += 1
        else:
            for csv_file in csv_files:
                row_count, status = count_csv_rows(csv_file)
                
                if row_count is not None:
                    results.append({
                        'Folder': child.name,
                        'CSV File': csv_file.name,
                        'Rows (excluding header)': row_count,
                        'Status': status
                    })
                    total_rows += row_count
                    folders_found += 1
                else:
                    results.append({
                        'Folder': child.name,
                        'CSV File': csv_file.name,
                        'Rows (excluding header)': 0,
                        'Status': status
                    })
    
    print(f"Found CSV files in {folders_found} cases")
    print(f"Missing or failed: {folders_missing}")
    print(f"Total rows (excluding headers): {total_rows}\n")
    
    return {
        'results': results,
        'total_rows': total_rows,
        'folders_found': folders_found,
        'folders_missing': folders_missing
    }


def display_csv_scan_results(scan_data):
    """Display results from scan_csv_in_labels_subfolders in a formatted table.
    
    Args:
        scan_data: Dictionary returned from scan_csv_in_labels_subfolders
        
    Returns:
        tuple: (df_with_totals, df_valid) - DataFrames with all results and valid results only
    """
    import pandas as pd
    
    results = scan_data['results']
    total_rows = scan_data['total_rows']
    folders_found = scan_data['folders_found']
    folders_missing = scan_data['folders_missing']
    
    df = pd.DataFrame(results)
    
    totals = pd.DataFrame([{
        'Folder': 'TOTAL',
        'CSV File': f'{folders_found} files',
        'Rows (excluding header)': total_rows,
        'Status': f'{folders_found} found, {folders_missing} missing'
    }])
    
    df_with_totals = pd.concat([df, totals], ignore_index=True)
    
    print("=" * 80)
    print("CSV Row Counts by Folder:")
    print("=" * 80)
    
    df_valid = df[df['Status'] == 'Success'].copy()
    
    if len(df_valid) > 0:
        print(f"\nStatistics for valid CSV files:")
        print(f"  Min rows: {df_valid['Rows (excluding header)'].min()}")
        print(f"  Max rows: {df_valid['Rows (excluding header)'].max()}")
        print(f"  Mean rows: {df_valid['Rows (excluding header)'].mean():.2f}")
        print(f"  Median rows: {df_valid['Rows (excluding header)'].median():.2f}")
    
    return df_with_totals, df_valid


if __name__ == '__main__':
    # Simple CLI for local runs
    import argparse
    parser = argparse.ArgumentParser(description='Convert images in labels/tongue to PNG')
    parser.add_argument('root', help='Root directory to search under')
    parser.add_argument('--keep-original', dest='remove_original', action='store_false',
                        help='Do not remove original files after conversion')
    parser.add_argument('--quiet', dest='verbose', action='store_false', help='Do not print conversion logs')
    args = parser.parse_args()
    summary = convert_tongue_labels_to_png(args.root, remove_original=args.remove_original, verbose=args.verbose)
    print('Summary:', summary)