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