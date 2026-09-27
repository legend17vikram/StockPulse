import torch
import torch.nn as nn
import torch.nn.functional as F

class CropAwareFeatureAdaptation(nn.Module):
    """
    Crop-Aware Feature Adaptation (CAFA) Module
    
    Conditions visual feature representations based on crop species identity:
    F_adapted = F ⊙ A(F, C)
    
    Where:
    - F: visual feature map [B, C_feat, H, W]
    - C: crop embedding vector [B, D_embed]
    - A(F, C): cross-attention weight map [B, C_feat, H, W]
    """
    def __init__(self, feat_channels, embed_dim=128):
        super(CropAwareFeatureAdaptation, self).__init__()
        self.feat_channels = feat_channels
        self.embed_dim = embed_dim

        # Project crop embedding to match channel dimensions
        self.crop_proj = nn.Sequential(
            nn.Linear(embed_dim, feat_channels),
            nn.ReLU(inplace=True),
            nn.Linear(feat_channels, feat_channels)
        )

        # Spatial feature projection
        self.feat_proj = nn.Sequential(
            nn.Conv2d(feat_channels, feat_channels, kernel_size=1, bias=False),
            nn.BatchNorm2d(feat_channels)
        )

        # Cross-attention generator producing channel & spatial gates
        self.attention_gen = nn.Sequential(
            nn.Conv2d(feat_channels, feat_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(feat_channels),
            nn.SiLU(),
            nn.Conv2d(feat_channels, feat_channels, kernel_size=1, bias=True),
            nn.Sigmoid()
        )

    def forward(self, F_visual, C_embed):
        """
        F_visual: [B, C_feat, H, W]
        C_embed:  [B, D_embed] or [B, D_embed, 1, 1]
        """
        b, c, h, w = F_visual.size()

        if C_embed.dim() == 2:
            c_proj = self.crop_proj(C_embed).unsqueeze(-1).unsqueeze(-1)  # [B, C_feat, 1, 1]
        else:
            c_proj = C_embed

        f_proj = self.feat_proj(F_visual)  # [B, C_feat, H, W]
        
        # Combine visual features and crop conditioning context
        conditioned_feat = f_proj + c_proj.expand_as(f_proj)
        
        # Compute Crop-Aware Attention Map A(F, C)
        A_crop_aware = self.attention_gen(conditioned_feat)  # [B, C_feat, H, W]
        
        # F_adapted = F ⊙ A(F, C)
        F_adapted = F_visual * A_crop_aware
        return F_adapted, A_crop_aware
