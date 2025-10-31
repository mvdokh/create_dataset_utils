import csv
import os
import sys
import numpy as np
import cv2
from tqdm import tqdm
from typing import List, Tuple, Union, Optional

# Add parent directories to path for utils access
sys.path.append('../..')
from utils import image_manip


def load_licking_data(data_folder: str,
                      target_resolution: Tuple[int, int] = (256, 256),
                      csv_delimiter: str = ' ',
                      csv_has_header: bool = True,
                      original_resolution: Tuple[int, int] = (480, 640),
                      gaussian_sigma: Tuple[int, int] = (25, 25),
                      image_extensions: Tuple[str, ...] = ('.png', '.jpg', '.jpeg'),
                      images_dir_name: str = 'images',
                      labels_dir_name: str = 'labels',
                      tongue_folder_name: str = 'tongue',
                      jaw_folder_name: str = 'jaw',
                      occlusion_markers: Tuple[str, ...] = ('nan', 'NaN', 'NAN', 'None', ''),
                      return_numpy: bool = True,
                      load_all_images: bool = True) -> Tuple[Union[List, np.ndarray], List[str], Union[List, np.ndarray]]:
    """
    Load licking dataset with tongue masks and jaw keypoints from CSV files.
    
    Parameters
    ----------
    data_folder : str
        Path to the root folder containing experiment subfolders
    target_resolution : Tuple[int, int]
        Target resolution to resize images to (width, height)
    csv_delimiter : str
        Delimiter character used in CSV files
    csv_has_header : bool
        Whether CSV files have a header row
    original_resolution : Tuple[int, int]
        Original resolution of images for jaw coordinate scaling (height, width)
    gaussian_sigma : Tuple[int, int]
        Sigma values for creating Gaussian masks for jaw (y_sigma, x_sigma)
    image_extensions : Tuple[str, ...]
        Tuple of valid image file extensions
    images_dir_name : str
        Name of the directory containing images
    labels_dir_name : str
        Name of the directory containing label data
    tongue_folder_name : str
        Name of the folder containing tongue mask images
    jaw_folder_name : str
        Name of the folder containing jaw CSV files
    occlusion_markers : Tuple[str, ...]
        Values in CSV that indicate the keypoint is occluded/missing
    return_numpy : bool
        If True, returns numpy arrays instead of lists
    load_all_images : bool
        If True, loads all images and pads missing labels with NaN/zeros
        
    Returns
    -------
    Tuple containing:
        - training_images: List or numpy array of resized images
        - training_image_filenames: List of image file paths
        - training_labels: List or numpy array of labels [tongue_masks, jaw_masks]
    """
    
    experiment_folders = [filename for filename in os.listdir(data_folder) 
                         if os.path.isdir(os.path.join(data_folder, filename))]
    
    # Progress bar setup
    iterable = enumerate(experiment_folders)
    progress = tqdm(iterable, desc='Loading', total=len(experiment_folders), 
                   ascii=True, leave=True, position=0)
    
    training_images = []
    training_image_filenames = []
    training_labels = [[], []]  # [tongue_masks, jaw_masks]
    
    n_features = 2  # tongue and jaw
    
    for i, experiment_folder in progress:
        experiment_path = os.path.join(data_folder, experiment_folder)
        
        print(f'Loading experiment folder: {experiment_folder}')
        
        # Check if required label folders exist
        labels_path = os.path.join(experiment_path, labels_dir_name)
        if not os.path.exists(labels_path):
            print(f'Skipping {experiment_folder}: No {labels_dir_name} folder found')
            continue
            
        label_folders = os.listdir(labels_path)
        # Filter out 'tip' folders if they exist
        label_folders = [folder for folder in label_folders if folder != 'tip']
        
        tongue_path = os.path.join(labels_path, tongue_folder_name)
        jaw_path = os.path.join(labels_path, jaw_folder_name)
        
        if not os.path.exists(tongue_path) or not os.path.exists(jaw_path):
            print(f'Skipping {experiment_folder}: Missing tongue or jaw folder')
            print(f'Found label folders: {label_folders}')
            continue
        
        # Process images
        img_folder = os.path.join(experiment_path, images_dir_name)
        if not os.path.exists(img_folder):
            print(f'Skipping {experiment_folder}: No {images_dir_name} folder found')
            continue
            
        image_paths = [os.path.join(img_folder, img) for img in os.listdir(img_folder)
                      if any(img.lower().endswith(ext) for ext in image_extensions)]
        
        if not image_paths:
            print(f'Skipping {experiment_folder}: No images found')
            continue
            
        print(f'Found {len(image_paths)} images')
        
        # Extract frame numbers from image names
        img_names = [os.path.basename(img_path) for img_path in image_paths]
        
        # Remove .png suffix if present
        if img_names[0].endswith('.png'):
            img_names_no_ext = [img[:-4] for img in img_names]
        else:
            img_names_no_ext = [os.path.splitext(img)[0] for img in img_names]
            
        # Remove scene prefix if present
        if img_names_no_ext[0].startswith('scene'):
            img_nums = [img[5:] for img in img_names_no_ext]
        else:
            img_nums = img_names_no_ext
            
        # Create mapping from frame number to image path and processed name
        frame_to_path = {}
        frame_to_name = {}
        for path, name, num in zip(image_paths, img_names_no_ext, img_nums):
            try:
                frame_num = int(num)
                frame_to_path[frame_num] = path
                frame_to_name[frame_num] = name
            except ValueError:
                print(f'Warning: Could not convert frame number "{num}" to int for {path}')
                continue
        
        # Load jaw coordinates from CSV
        jaw_csv_files = [f for f in os.listdir(jaw_path) if f.endswith('.csv')]
        if not jaw_csv_files:
            print(f'Skipping {experiment_folder}: No CSV file found in jaw folder')
            continue
            
        jaw_csv_file = jaw_csv_files[0]
        jaw_coords = {}
        
        with open(os.path.join(jaw_path, jaw_csv_file), mode='r') as file:
            if csv_has_header:
                next(file)
                
            # Try different delimiters to handle various CSV formats
            content = file.read()
            file.seek(0)
            if csv_has_header:
                next(file)
                
            # Detect delimiter by checking first data line
            first_line = file.readline().strip()
            if ',' in first_line:
                delimiter = ','
            elif ' ' in first_line:
                delimiter = ' '
            elif '\t' in first_line:
                delimiter = '\t'
            else:
                delimiter = csv_delimiter  # use provided default
                
            # Reset file position
            file.seek(0)
            if csv_has_header:
                next(file)
                
            reader = csv.reader(file, delimiter=delimiter)
            for row in reader:
                # Skip empty rows
                if not row:
                    continue
                    
                # Handle different numbers of columns - look for at least 3 values
                if len(row) == 1:
                    # Try to split by other delimiters
                    if ',' in row[0]:
                        row = row[0].split(',')
                    elif ' ' in row[0]:
                        row = row[0].split()
                    elif '\t' in row[0]:
                        row = row[0].split('\t')
                        
                # Skip rows with insufficient columns
                if len(row) < 3:
                    print(f"Skipping row with insufficient columns: {row}")
                    continue
                    
                # Skip rows with empty values in first 3 columns
                if not row[0].strip() or not row[1].strip() or not row[2].strip():
                    print(f"Skipping row with empty values: {row}")
                    continue
                    
                try:
                    frame_num = int(row[0].strip())
                    x_str = row[1].strip()
                    y_str = row[2].strip()
                    
                    # Check for occlusion markers
                    if x_str in occlusion_markers or y_str in occlusion_markers:
                        jaw_coords[frame_num] = None  # Mark as occluded/missing
                    else:
                        x = int(float(x_str))
                        y = int(float(y_str))
                        jaw_coords[frame_num] = [x, y]
                        
                except ValueError as e:
                    print(f"Error converting values in row {row}: {e}")
                    continue
        
        # Get first valid image to determine actual resolution
        if not frame_to_path:
            print(f'Skipping {experiment_folder}: No valid frame numbers found')
            continue
            
        first_frame = next(iter(frame_to_path.keys()))
        first_img = cv2.imread(frame_to_path[first_frame])
        if first_img is None:
            print(f'Skipping {experiment_folder}: Could not read first image')
            continue
            
        actual_original_resolution = (first_img.shape[0], first_img.shape[1])
        print(f'Original resolution: {actual_original_resolution}')
        
        # Determine which frames to process
        all_frames = sorted(frame_to_path.keys())
        if load_all_images:
            valid_frames = all_frames
        else:
            # Only process frames that have jaw coordinates
            valid_frames = [frame for frame in all_frames if frame in jaw_coords]
            
        if not valid_frames:
            print(f'Skipping {experiment_folder}: No valid frames found')
            continue
            
        print(f'Processing {len(valid_frames)} frames')
        
        # Process each frame
        experiment_images = []
        experiment_image_filenames = []
        experiment_labels = [[], []]  # [tongue_masks, jaw_masks]
        
        for frame_num in valid_frames:
            image_path = frame_to_path[frame_num]
            
            # Load and resize image
            image = cv2.imread(image_path)
            if image is None:
                print(f'Could not read image: {image_path}')
                continue
                
            try:
                image_resized = cv2.resize(image, target_resolution, interpolation=cv2.INTER_AREA)
                experiment_images.append(image_resized)
                experiment_image_filenames.append(image_path)
            except Exception as e:
                print(f'Error resizing image {image_path}: {e}')
                continue
                
            # Process tongue mask
            img_name = frame_to_name[frame_num]
            tongue_label_path = os.path.join(tongue_path, img_name + '.png')
            
            if os.path.exists(tongue_label_path):
                mask = cv2.imread(tongue_label_path, cv2.IMREAD_GRAYSCALE)
                if mask is not None:
                    mask = cv2.resize(mask, target_resolution)
                    mask = mask > 0
                    experiment_labels[0].append(mask)
                else:
                    # Create empty mask
                    experiment_labels[0].append(np.zeros(target_resolution, dtype=bool))
            else:
                # Create empty mask for missing tongue labels
                experiment_labels[0].append(np.zeros(target_resolution, dtype=bool))
                
            # Process jaw coordinates
            if frame_num in jaw_coords and jaw_coords[frame_num] is not None:
                jaw_coord = jaw_coords[frame_num]
                jaw_mask = image_manip.create_gaussian_mask(
                    actual_original_resolution, target_resolution, jaw_coord, gaussian_sigma)
                # Convert to uint8
                jaw_mask = (jaw_mask * 255).astype(np.uint8)
                experiment_labels[1].append(jaw_mask)
            else:
                # Create empty mask for missing jaw coordinates
                jaw_mask = np.zeros(target_resolution, dtype=np.uint8)
                experiment_labels[1].append(jaw_mask)
                if load_all_images:
                    print(f'No jaw label for frame {frame_num} in {experiment_folder}, using empty mask')
        
        # Add experiment data to training data
        training_images.extend(experiment_images)
        training_image_filenames.extend(experiment_image_filenames)
        for i in range(n_features):
            training_labels[i].extend(experiment_labels[i])
    
    print(f'Loaded {len(training_images)} images total')
    
    if return_numpy:
        # Convert to numpy arrays
        images_np = np.stack(training_images) if training_images else np.array([])
        labels_np = np.moveaxis(np.stack(training_labels), [0], [-1]) if training_labels[0] else np.array([])
        return images_np, training_image_filenames, labels_np
    else:
        return training_images, training_image_filenames, training_labels