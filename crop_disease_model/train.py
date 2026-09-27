import os
import time
import argparse
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader

from models.yolov13_multitask import YOLOv13MultiTaskNet, UncertaintyLoss
from dataset.synthetic_dataset import get_dataloaders, CROP_CLASSES, DISEASE_CLASSES

def dice_loss(pred_mask, gt_mask, smooth=1e-5):
    intersection = (pred_mask * gt_mask).sum()
    return 1.0 - (2.0 * intersection + smooth) / (pred_mask.sum() + gt_mask.sum() + smooth)

def train_one_epoch(model, uncertainty_loss_fn, dataloader, optimizer, device):
    model.train()
    total_loss_accum = 0.0
    crop_loss_accum = 0.0
    disease_loss_accum = 0.0
    seg_loss_accum = 0.0
    det_loss_accum = 0.0
    sev_loss_accum = 0.0

    ce_loss = nn.CrossEntropyLoss()
    bce_loss = nn.BCELoss()
    l1_loss = nn.SmoothL1Loss()

    for step, batch in enumerate(dataloader):
        images = batch["image"].to(device)
        gt_crop = batch["crop_idx"].to(device)
        gt_disease = batch["disease_idx"].to(device)
        gt_seg = batch["seg_mask"].to(device)
        gt_bbox = batch["bbox"].to(device)
        gt_sev_ratio = batch["severity_ratio"].to(device)
        gt_sev_stage = batch["severity_stage"].to(device)

        optimizer.zero_grad()

        outputs = model(images)

        # 1. Crop Loss
        l_crop = ce_loss(outputs["crop_logits"], gt_crop)

        # 2. Disease Classification Loss
        l_disease = ce_loss(outputs["disease_logits"], gt_disease)

        # 3. Segmentation Loss (BCE + Dice)
        pred_seg = outputs["seg_mask"]
        l_seg_bce = bce_loss(pred_seg, gt_seg)
        l_seg_dice = dice_loss(pred_seg, gt_seg)
        l_seg = l_seg_bce + l_seg_dice

        # 4. Detection Loss (Simplified anchor-free Bounding Box Loss)
        p5_det = outputs["det_outputs"][2]
        b, _, h, w = p5_det.shape
        pred_bbox = p5_det[:, :4, :, :].mean(dim=[-2, -1])  # Aggregated box prediction
        l_det = l1_loss(pred_bbox, gt_bbox)

        # 5. Severity Loss (Ratio L1 + Stage CE)
        l_sev_ratio = l1_loss(outputs["severity_ratio"], gt_sev_ratio)
        l_sev_stage = ce_loss(outputs["severity_stage"], gt_sev_stage)
        l_sev = l_sev_ratio + l_sev_stage

        # Adaptive Multi-Task Uncertainty Weighting
        total_loss, weighted_losses = uncertainty_loss_fn(l_crop, l_disease, l_seg, l_det, l_sev)

        total_loss.backward()
        optimizer.step()

        total_loss_accum += total_loss.item()
        crop_loss_accum += l_crop.item()
        disease_loss_accum += l_disease.item()
        seg_loss_accum += l_seg.item()
        det_loss_accum += l_det.item()
        sev_loss_accum += l_sev.item()

    num_steps = len(dataloader)
    return {
        "loss": total_loss_accum / num_steps,
        "l_crop": crop_loss_accum / num_steps,
        "l_disease": disease_loss_accum / num_steps,
        "l_seg": seg_loss_accum / num_steps,
        "l_det": det_loss_accum / num_steps,
        "l_sev": sev_loss_accum / num_steps
    }

def validate(model, dataloader, device):
    model.eval()
    crop_correct = 0
    disease_correct = 0
    total_samples = 0
    total_dice = 0.0

    with torch.no_grad():
        for batch in dataloader:
            images = batch["image"].to(device)
            gt_crop = batch["crop_idx"].to(device)
            gt_disease = batch["disease_idx"].to(device)
            gt_seg = batch["seg_mask"].to(device)

            outputs = model(images)

            # Crop accuracy
            crop_preds = torch.argmax(outputs["crop_logits"], dim=1)
            crop_correct += (crop_preds == gt_crop).sum().item()

            # Disease accuracy
            disease_preds = torch.argmax(outputs["disease_logits"], dim=1)
            disease_correct += (disease_preds == gt_disease).sum().item()

            # Segmentation Dice
            pred_seg = (outputs["seg_mask"] > 0.5).float()
            intersection = (pred_seg * gt_seg).sum().item()
            total_dice += (2.0 * intersection + 1e-5) / (pred_seg.sum().item() + gt_seg.sum().item() + 1e-5)

            total_samples += images.size(0)

    crop_acc = crop_correct / total_samples
    disease_acc = disease_correct / total_samples
    mean_dice = total_dice / len(dataloader)

    return {
        "crop_acc": crop_acc,
        "disease_acc": disease_acc,
        "mean_dice": mean_dice
    }

def main():
    parser = argparse.ArgumentParser(description="Train YOLOv13 Multi-Task Crop Disease Model")
    parser.add_argument("--epochs", type=int, default=5, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=8, help="Batch size")
    parser.add_argument("--lr", type=float, default=1e-3, help="Learning rate")
    parser.add_argument("--num_train", type=int, default=300, help="Train samples")
    parser.add_argument("--num_val", type=int, default=60, help="Validation samples")
    parser.add_argument("--save_path", type=str, default="best_model.pth", help="Path to save best checkpoint")
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[+] Running training on device: {device}")

    # Load Data
    train_loader, val_loader = get_dataloaders(num_train=args.num_train, num_val=args.num_val, batch_size=args.batch_size)

    # Initialize Model & Uncertainty Weighting Loss
    model = YOLOv13MultiTaskNet(num_crops=len(CROP_CLASSES), num_diseases=len(DISEASE_CLASSES)).to(device)
    uncertainty_loss_fn = UncertaintyLoss(num_tasks=5).to(device)

    optimizer = optim.AdamW(list(model.parameters()) + list(uncertainty_loss_fn.parameters()), lr=args.lr, weight_decay=1e-4)

    best_acc = 0.0
    print("\n--- Starting Multi-Task Training ---")
    start_time = time.time()

    for epoch in range(1, args.epochs + 1):
        t0 = time.time()
        metrics = train_one_epoch(model, uncertainty_loss_fn, train_loader, optimizer, device)
        val_metrics = validate(model, val_loader, device)
        elapsed = time.time() - t0

        print(f"Epoch [{epoch}/{args.epochs}] ({elapsed:.2f}s) | "
              f"Total Loss: {metrics['loss']:.4f} | "
              f"Crop Acc: {val_metrics['crop_acc']*100:.1f}% | "
              f"Disease Acc: {val_metrics['disease_acc']*100:.1f}% | "
              f"Dice: {val_metrics['mean_dice']:.4f}", flush=True)

        # Save Best Model
        if val_metrics["disease_acc"] >= best_acc:
            best_acc = val_metrics["disease_acc"]
            checkpoint = {
                "epoch": epoch,
                "model_state": model.state_dict(),
                "uncertainty_state": uncertainty_loss_fn.state_dict(),
                "val_metrics": val_metrics
            }
            torch.save(checkpoint, args.save_path)

    total_time = time.time() - start_time
    print(f"\n[OK] Training Complete in {total_time:.2f}s! Best Validation Disease Accuracy: {best_acc*100:.2f}%", flush=True)
    print(f"[OK] Saved best checkpoint to: {args.save_path}", flush=True)

if __name__ == "__main__":
    main()
