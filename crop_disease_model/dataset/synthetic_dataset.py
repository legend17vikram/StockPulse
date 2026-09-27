import os
import math
import random
import numpy as np
import cv2
import torch
from torch.utils.data import Dataset, DataLoader

# Define Crop and Disease Vocabularies
CROP_CLASSES = ["Tomato", "Potato", "Grape", "Maize", "Pepper"]
DISEASE_CLASSES = [
    "Healthy",
    "Tomato_Early_Blight",
    "Tomato_Late_Blight",
    "Potato_Early_Blight",
    "Potato_Late_Blight",
    "Grape_Black_Rot",
    "Grape_Esca",
    "Maize_Common_Rust",
    "Pepper_Bacterial_Spot",
    "Leaf_Spot"
]
SEVERITY_CLASSES = ["Healthy", "Mild", "Moderate", "Severe"]


def generate_synthetic_crop_image(img_size=256):
    """
    Generates a realistic synthetic agricultural leaf image with:
    - Custom leaf shape & background texture for 5 crop types
    - Disease lesions with irregular boundaries and varied scale
    - Ground truth segmentation mask, bounding box, crop index, disease index, and severity %
    """
    crop_idx = random.randint(0, len(CROP_CLASSES) - 1)
    crop_name = CROP_CLASSES[crop_idx]
    
    # Map crop to possible disease classes
    if crop_idx == 0:  # Tomato
        d_choices = [0, 1, 2, 9]
    elif crop_idx == 1:  # Potato
        d_choices = [0, 3, 4, 9]
    elif crop_idx == 2:  # Grape
        d_choices = [0, 5, 6, 9]
    elif crop_idx == 3:  # Maize
        d_choices = [0, 7, 9]
    else:  # Pepper
        d_choices = [0, 8, 9]

    disease_idx = random.choice(d_choices)
    is_healthy = (disease_idx == 0)

    # 1. Create soil/background texture
    bg_color = np.array([random.randint(40, 80), random.randint(50, 90), random.randint(60, 100)], dtype=np.uint8)
    image = np.full((img_size, img_size, 3), bg_color, dtype=np.uint8)

    # 2. Draw leaf outline based on crop species
    center = (img_size // 2, img_size // 2)
    leaf_mask = np.zeros((img_size, img_size), dtype=np.uint8)

    if crop_name == "Maize":
        # Long elongated leaf
        axes = (int(img_size * 0.15), int(img_size * 0.42))
        cv2.ellipse(leaf_mask, center, axes, 25, 0, 360, 255, -1)
    elif crop_name in ["Tomato", "Potato"]:
        # Serrated compound leaf shape
        axes = (int(img_size * 0.32), int(img_size * 0.38))
        cv2.ellipse(leaf_mask, center, axes, 0, 0, 360, 255, -1)
    else:
        # Round/palmate leaf shape
        axes = (int(img_size * 0.35), int(img_size * 0.35))
        cv2.ellipse(leaf_mask, center, axes, 0, 0, 360, 255, -1)

    # Apply leaf green texture
    leaf_green = np.array([random.randint(30, 70), random.randint(120, 190), random.randint(40, 80)], dtype=np.uint8)
    image[leaf_mask == 255] = leaf_green

    # Add leaf veins
    cv2.line(image, (center[0], center[1] - axes[1] + 10), (center[0], center[1] + axes[1] - 10), (20, 100, 30), 2)

    # 3. Create Disease Lesion Spots if not healthy
    lesion_mask = np.zeros((img_size, img_size), dtype=np.uint8)
    boxes = []

    if not is_healthy:
        num_spots = random.randint(2, 6)
        for _ in range(num_spots):
            # Random position within leaf area
            offset_x = random.randint(-int(axes[0] * 0.5), int(axes[0] * 0.5))
            offset_y = random.randint(-int(axes[1] * 0.5), int(axes[1] * 0.5))
            spot_center = (center[0] + offset_x, center[1] + offset_y)
            
            # Lesion size & irregular shape
            rx = random.randint(8, 25)
            ry = random.randint(8, 25)
            
            spot_mask = np.zeros((img_size, img_size), dtype=np.uint8)
            cv2.ellipse(spot_mask, spot_center, (rx, ry), random.randint(0, 180), 0, 360, 255, -1)
            
            # Restrict spot to leaf area only
            spot_mask = cv2.bitwise_and(spot_mask, leaf_mask)
            lesion_mask = cv2.bitwise_or(lesion_mask, spot_mask)

            # Compute spot bounding box
            ys, xs = np.where(spot_mask == 255)
            if len(xs) > 0 and len(ys) > 0:
                xmin, xmax = np.min(xs), np.max(xs)
                ymin, ymax = np.min(ys), np.max(ys)
                boxes.append([xmin, ymin, xmax, ymax])

        # Apply brownish/yellowish disease color to lesions
        lesion_color = np.array([random.randint(20, 50), random.randint(60, 110), random.randint(110, 160)], dtype=np.uint8)
        image[lesion_mask == 255] = lesion_color

    # Compute overall bounding box for diseased leaf region
    if len(boxes) > 0:
        boxes_arr = np.array(boxes)
        overall_box = [np.min(boxes_arr[:, 0]), np.min(boxes_arr[:, 1]), np.max(boxes_arr[:, 2]), np.max(boxes_arr[:, 3])]
    else:
        overall_box = [0, 0, 0, 0]

    # Calculate severity ratio
    leaf_pixel_count = max(np.sum(leaf_mask == 255), 1)
    lesion_pixel_count = np.sum(lesion_mask == 255)
    severity_ratio = float(lesion_pixel_count) / float(leaf_pixel_count)

    # Classify severity stage
    if severity_ratio == 0.0:
        severity_stage = 0  # Healthy
    elif severity_ratio < 0.15:
        severity_stage = 1  # Mild
    elif severity_ratio < 0.40:
        severity_stage = 2  # Moderate
    else:
        severity_stage = 3  # Severe

    # Normalize image to [0, 1] tensor format
    img_tensor = torch.from_numpy(image.transpose(2, 0, 1)).float() / 255.0
    seg_tensor = torch.from_numpy(lesion_mask).float().unsqueeze(0) / 255.0

    return {
        "image": img_tensor,
        "crop_idx": torch.tensor(crop_idx, dtype=torch.long),
        "disease_idx": torch.tensor(disease_idx, dtype=torch.long),
        "seg_mask": seg_tensor,
        "bbox": torch.tensor(overall_box, dtype=torch.float32) / float(img_size),
        "severity_ratio": torch.tensor([severity_ratio], dtype=torch.float32),
        "severity_stage": torch.tensor(severity_stage, dtype=torch.long),
        "crop_name": crop_name,
        "disease_name": DISEASE_CLASSES[disease_idx]
    }


class MultiCropDiseaseDataset(Dataset):
    """
    PyTorch Dataset for Multi-Crop Disease Diagnosis & Severity Prediction.
    Pre-caches synthetic samples in RAM for high throughput.
    """
    def __init__(self, num_samples=300, img_size=256):
        super(MultiCropDiseaseDataset, self).__init__()
        self.num_samples = num_samples
        self.img_size = img_size
        self.samples = []
        
        # Pre-cache samples in memory
        for idx in range(num_samples):
            np.random.seed(idx)
            random.seed(idx)
            self.samples.append(generate_synthetic_crop_image(self.img_size))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        return self.samples[idx]


def get_dataloaders(num_train=400, num_val=100, batch_size=16, img_size=256):
    train_ds = MultiCropDiseaseDataset(num_samples=num_train, img_size=img_size)
    val_ds = MultiCropDiseaseDataset(num_samples=num_val, img_size=img_size)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, drop_last=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False)

    return train_loader, val_loader
