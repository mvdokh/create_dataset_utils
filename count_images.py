#!/usr/bin/env python3
"""
Script to count images in a directory and all its subdirectories.
Counts common image formats: .jpg, .jpeg, .png, .bmp, .tiff, .tif, .gif, .webp
"""

import os
import argparse
from collections import defaultdict

def count_images_in_directory(directory_path):
    """
    Count images in a directory and all its subdirectories.
    
    Args:
        directory_path (str): Path to the directory to search
        
    Returns:
        tuple: (total_count, format_counts, folder_counts)
    """
    # Common image extensions
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.gif', '.webp'}
    
    total_count = 0
    format_counts = defaultdict(int)
    folder_counts = defaultdict(int)
    
    print(f"Scanning directory: {directory_path}")
    print("=" * 60)
    
    for root, dirs, files in os.walk(directory_path):
        folder_image_count = 0
        
        for file in files:
            # Get file extension (case insensitive)
            _, ext = os.path.splitext(file)
            ext = ext.lower()
            
            if ext in image_extensions:
                total_count += 1
                folder_image_count += 1
                format_counts[ext] += 1
        
        if folder_image_count > 0:
            folder_counts[root] = folder_image_count
            print(f"{root}: {folder_image_count} images")
    
    return total_count, format_counts, folder_counts

def main():
    parser = argparse.ArgumentParser(description='Count images in a directory and subdirectories')
    parser.add_argument('directory', nargs='?', default='/home/wanglab/Whisker_Dataset',
                       help='Directory path to scan (default: /home/wanglab/Whisker_Dataset)')
    
    args = parser.parse_args()
    
    directory_path = args.directory
    
    if not os.path.exists(directory_path):
        print(f"Error: Directory '{directory_path}' does not exist.")
        return
    
    if not os.path.isdir(directory_path):
        print(f"Error: '{directory_path}' is not a directory.")
        return
    
    print(f"Counting images in: {directory_path}")
    print()
    
    total_count, format_counts, folder_counts = count_images_in_directory(directory_path)
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total images found: {total_count}")
    
    if format_counts:
        print("\nBy format:")
        for ext, count in sorted(format_counts.items()):
            print(f"  {ext}: {count}")
    
    print(f"\nImages found in {len(folder_counts)} folders")
    
    if total_count == 0:
        print("\nNo images found in the specified directory.")
    
    # Show top 10 folders with most images
    if folder_counts:
        print("\nTop folders by image count:")
        sorted_folders = sorted(folder_counts.items(), key=lambda x: x[1], reverse=True)
        for folder, count in sorted_folders[:10]:
            relative_path = os.path.relpath(folder, directory_path)
            print(f"  {relative_path}: {count} images")

if __name__ == "__main__":
    main()