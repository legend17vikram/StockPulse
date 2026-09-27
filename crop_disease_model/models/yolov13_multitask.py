import math
import torch
import torch.nn as nn
import torch.nn.functional as F

from .camsa import CAMSA
from .cafa import CropAwareFeatureAdaptation

class YOLOv13Backbone(nn.Module):
    """
    YOLOv13-inspired Multi-Scale Feature Extractor backbone with embedded CAMSA attention blocks.
    Outputs feature maps at 3 scales: P3 (stride 8), P4 (stride 16), P5 (stride 32).
    """
    def __init__(self, in_channels=3, base_channels=32):
        super(YOLOv13Backbone, self).__init__()
        
        # Stem
        self.stem = nn.Sequential(
            nn.Conv2d(in_channels, base_channels, kernel_size=3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(base_channels),
            nn.SiLU()
        )
        
        # Stage 1 (P1 -> P2, stride 4)
        c1 = base_channels * 2
        self.stage1 = nn.Sequential(
            nn.Conv2d(base_channels, c1, kernel_size=3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(c1),
            nn.SiLU(),
            CAMSA(c1)
        )
        
        # Stage 2 (P2 -> P3, stride 8)
        c2 = base_channels * 4
        self.stage2 = nn.Sequential(
            nn.Conv2d(c1, c2, kernel_size=3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(c2),
            nn.SiLU(),
            CAMSA(c2)
        )
        
        # Stage 3 (P3 -> P4, stride 16)
        c3 = base_channels * 8
        self.stage3 = nn.Sequential(
            nn.Conv2d(c2, c3, kernel_size=3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(c3),
            nn.SiLU(),
            CAMSA(c3)
        )
        
        # Stage 4 (P4 -> P5, stride 32)
        c4 = base_channels * 16
        self.stage4 = nn.Sequential(
            nn.Conv2d(c3, c4, kernel_size=3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(c4),
            nn.SiLU(),
            CAMSA(c4)
        )

    def forward(self, x):
        x = self.stem(x)
        x1 = self.stage1(x)
        p3 = self.stage2(x1)  # [B, 128, H/8, W/8]
        p4 = self.stage3(p3)  # [B, 256, H/16, W/16]
        p5 = self.stage4(p4)  # [B, 512, H/32, W/32]
        return p3, p4, p5


class CropClassifierHead(nn.Module):
    """
    Predicts crop species (e.g. Tomato, Potato, Grape, Maize, Pepper)
    and extracts crop embedding C for CAFA conditioning.
    """
    def __init__(self, in_channels, num_crops=5, embed_dim=128):
        super(CropClassifierHead, self).__init__()
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.fc_embed = nn.Sequential(
            nn.Linear(in_channels, embed_dim),
            nn.BatchNorm1d(embed_dim),
            nn.ReLU(inplace=True)
        )
        self.fc_classifier = nn.Linear(embed_dim, num_crops)

    def forward(self, p5):
        b = p5.size(0)
        pooled = self.pool(p5).view(b, -1)
        crop_embed = self.fc_embed(pooled)      # [B, embed_dim]
        crop_logits = self.fc_classifier(crop_embed) # [B, num_crops]
        return crop_logits, crop_embed


class SegmentationDecoder(nn.Module):
    """
    Multi-Scale Lesion Segmentation Head (outputs binary/continuous disease mask M).
    """
    def __init__(self, c3_channels=128, c4_channels=256, c5_channels=512):
        super(SegmentationDecoder, self).__init__()
        self.up5_to_4 = nn.Sequential(
            nn.ConvTranspose2d(c5_channels, c4_channels, kernel_size=2, stride=2),
            nn.BatchNorm2d(c4_channels),
            nn.SiLU()
        )
        self.fuse4 = nn.Sequential(
            nn.Conv2d(c4_channels * 2, c4_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(c4_channels),
            nn.SiLU()
        )
        self.up4_to_3 = nn.Sequential(
            nn.ConvTranspose2d(c4_channels, c3_channels, kernel_size=2, stride=2),
            nn.BatchNorm2d(c3_channels),
            nn.SiLU()
        )
        self.fuse3 = nn.Sequential(
            nn.Conv2d(c3_channels * 2, c3_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(c3_channels),
            nn.SiLU()
        )
        self.final_upsample = nn.Sequential(
            nn.ConvTranspose2d(c3_channels, 64, kernel_size=4, stride=4, padding=0),
            nn.BatchNorm2d(64),
            nn.SiLU(),
            nn.ConvTranspose2d(64, 32, kernel_size=2, stride=2, padding=0),
            nn.BatchNorm2d(32),
            nn.SiLU(),
            nn.Conv2d(32, 1, kernel_size=3, padding=1),
            nn.Sigmoid()
        )

    def forward(self, p3, p4, p5, target_size=None):
        p5_up = self.up5_to_4(p5)
        p4_fused = self.fuse4(torch.cat([p4, p5_up], dim=1))
        
        p4_up = self.up4_to_3(p4_fused)
        p3_fused = self.fuse3(torch.cat([p3, p4_up], dim=1))
        
        mask = self.final_upsample(p3_fused)
        if target_size is not None and mask.shape[-2:] != target_size:
            mask = F.interpolate(mask, size=target_size, mode='bilinear', align_corners=False)
        return mask


class MaskConditionedDiseaseHead(nn.Module):
    """
    Mask-Conditioned Disease Classification Head P(D | I, M).
    Applies predicted segmentation mask M as spatial ROI focus on visual features
    to classify disease symptoms while ignoring background.
    """
    def __init__(self, in_channels=512, num_diseases=10):
        super(MaskConditionedDiseaseHead, self).__init__()
        self.conv_roi = nn.Sequential(
            nn.Conv2d(in_channels, 256, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(256),
            nn.SiLU(),
            nn.Conv2d(256, 128, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(128),
            nn.SiLU()
        )
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.fc = nn.Sequential(
            nn.Linear(128, 64),
            nn.ReLU(inplace=True),
            nn.Linear(64, num_diseases)
        )

    def forward(self, p5_adapted, mask_downsampled):
        # Apply mask ROI attention P(D | I, M)
        roi_features = p5_adapted * (mask_downsampled + 0.1)  # Soft mask conditioning
        feat = self.conv_roi(roi_features)
        b = feat.size(0)
        pooled = self.pool(feat).view(b, -1)
        logits = self.fc(pooled)
        return logits


class YOLOv13DetectionHead(nn.Module):
    """
    YOLO Bounding Box Localization & Object Detection Head.
    Outputs: [batch, num_anchors * (5 + num_diseases), H, W]
    where 5 = (cx, cy, w, h, obj_conf).
    """
    def __init__(self, in_channels, num_classes=10, num_anchors=3):
        super(YOLOv13DetectionHead, self).__init__()
        self.num_classes = num_classes
        self.num_anchors = num_anchors
        self.out_dim = num_anchors * (5 + num_classes)
        
        self.conv = nn.Sequential(
            nn.Conv2d(in_channels, in_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(in_channels),
            nn.SiLU(),
            nn.Conv2d(in_channels, self.out_dim, kernel_size=1)
        )

    def forward(self, x):
        return self.conv(x)


class SeverityEstimatorHead(nn.Module):
    """
    Severity Prediction Engine:
    Computes disease severity score (percentage leaf area affected)
    and classifies severity stage: Healthy (0), Mild (1), Moderate (2), Severe (3).
    """
    def __init__(self, in_channels=512):
        super(SeverityEstimatorHead, self).__init__()
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.regressor = nn.Sequential(
            nn.Linear(in_channels + 1, 64),
            nn.ReLU(inplace=True),
            nn.Linear(64, 1),
            nn.Sigmoid()  # Percentage infected (0.0 to 1.0)
        )
        self.stage_classifier = nn.Sequential(
            nn.Linear(1, 32),
            nn.ReLU(inplace=True),
            nn.Linear(32, 4)  # 4 severity classes
        )

    def forward(self, p5_adapted, mask_ratio):
        """
        mask_ratio: [B, 1] calculated directly from segmentation mask sum / total pixels
        """
        b = p5_adapted.size(0)
        pooled = self.pool(p5_adapted).view(b, -1)
        combined = torch.cat([pooled, mask_ratio], dim=1)
        
        severity_ratio = self.regressor(combined)  # % infected area [0.0, 1.0]
        severity_stage = self.stage_classifier(severity_ratio)
        return severity_ratio, severity_stage


class YOLOv13MultiTaskNet(nn.Module):
    """
    YOLOv13-based Multi-Task Attention Network with Cross-Scale Feature Fusion
    for Multi-Crop Disease Localization, Classification and Severity Prediction.
    """
    def __init__(self, num_crops=5, num_diseases=10, embed_dim=128, enable_camsa=True, enable_cafa=True, enable_seg=True):
        super(YOLOv13MultiTaskNet, self).__init__()
        self.enable_camsa = enable_camsa
        self.enable_cafa = enable_cafa
        self.enable_seg = enable_seg

        # Shared Backbone
        self.backbone = YOLOv13Backbone(in_channels=3, base_channels=32)

        # Crop Classifier & Embedding Head
        self.crop_head = CropClassifierHead(in_channels=512, num_crops=num_crops, embed_dim=embed_dim)

        # CAFA Modules for P3, P4, P5
        self.cafa_p3 = CropAwareFeatureAdaptation(feat_channels=128, embed_dim=embed_dim)
        self.cafa_p4 = CropAwareFeatureAdaptation(feat_channels=256, embed_dim=embed_dim)
        self.cafa_p5 = CropAwareFeatureAdaptation(feat_channels=512, embed_dim=embed_dim)

        # Segmentation Head
        self.seg_decoder = SegmentationDecoder(c3_channels=128, c4_channels=256, c5_channels=512)

        # Detection Heads (P3, P4, P5)
        self.det_p3 = YOLOv13DetectionHead(128, num_classes=num_diseases)
        self.det_p4 = YOLOv13DetectionHead(256, num_classes=num_diseases)
        self.det_p5 = YOLOv13DetectionHead(512, num_classes=num_diseases)

        # Mask-Conditioned Disease Classification Head
        self.disease_head = MaskConditionedDiseaseHead(in_channels=512, num_diseases=num_diseases)

        # Severity Head
        self.severity_head = SeverityEstimatorHead(in_channels=512)

    def forward(self, x):
        h_orig, w_orig = x.shape[-2:]
        
        # 1. Extract Backbone Pyramid Features (P3, P4, P5)
        p3, p4, p5 = self.backbone(x)

        # 2. Crop Classification & Embedding C
        crop_logits, crop_embed = self.crop_head(p5)

        # 3. Crop-Aware Feature Adaptation (CAFA)
        if self.enable_cafa:
            p3_adapted, attn_p3 = self.cafa_p3(p3, crop_embed)
            p4_adapted, attn_p4 = self.cafa_p4(p4, crop_embed)
            p5_adapted, attn_p5 = self.cafa_p5(p5, crop_embed)
        else:
            p3_adapted, p4_adapted, p5_adapted = p3, p4, p5
            attn_p3, attn_p4, attn_p5 = None, None, None

        # 4. Disease Lesion Segmentation Mask M
        if self.enable_seg:
            seg_mask = self.seg_decoder(p3_adapted, p4_adapted, p5_adapted, target_size=(h_orig, w_orig))
        else:
            seg_mask = torch.zeros((x.size(0), 1, h_orig, w_orig), device=x.device)

        # Downsampled mask for feature conditioning on P5
        mask_downsampled = F.interpolate(seg_mask, size=p5_adapted.shape[-2:], mode='bilinear', align_corners=False)

        # 5. Object Detection Outputs (Bounding Boxes)
        det_out_p3 = self.det_p3(p3_adapted)
        det_out_p4 = self.det_p4(p4_adapted)
        det_out_p5 = self.det_p5(p5_adapted)

        # 6. Mask-Conditioned Disease Classifier P(D | I, M)
        disease_logits = self.disease_head(p5_adapted, mask_downsampled)

        # 7. Severity Estimation
        mask_ratio = seg_mask.view(seg_mask.size(0), -1).mean(dim=1, keepdim=True)
        severity_ratio, severity_stage = self.severity_head(p5_adapted, mask_ratio)

        return {
            "crop_logits": crop_logits,
            "crop_embed": crop_embed,
            "seg_mask": seg_mask,
            "det_outputs": [det_out_p3, det_out_p4, det_out_p5],
            "disease_logits": disease_logits,
            "severity_ratio": severity_ratio,
            "severity_stage": severity_stage,
            "attention_maps": [attn_p3, attn_p4, attn_p5]
        }


class UncertaintyLoss(nn.Module):
    """
    Adaptive Uncertainty-Based Task Loss Weighting
    Dynamically learns task precision parameters (log_vars) during multi-task training:
    L_total = sum_i [ exp(-s_i) * L_i + s_i ]
    where s_i = log(sigma_i^2)
    """
    def __init__(self, num_tasks=5):
        super(UncertaintyLoss, self).__init__()
        # 5 tasks: crop, disease, seg, det, severity
        self.log_vars = nn.Parameter(torch.zeros(num_tasks))

    def forward(self, loss_crop, loss_disease, loss_seg, loss_det, loss_sev):
        losses = [loss_crop, loss_disease, loss_seg, loss_det, loss_sev]
        total_loss = 0.0
        weighted_losses = []
        for i, loss in enumerate(losses):
            precision = torch.exp(-self.log_vars[i])
            w_loss = precision * loss + self.log_vars[i]
            total_loss += w_loss
            weighted_losses.append(w_loss.item())

        return total_loss, weighted_losses
