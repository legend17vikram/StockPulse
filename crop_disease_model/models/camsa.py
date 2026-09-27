import math
import torch
import torch.nn as nn
import torch.nn.functional as F

class ECA(nn.Module):
    """
    Efficient Channel Attention (ECA) module.
    Avoids dimensionality reduction and captures cross-channel interactions efficiently
    via 1D convolution with adaptive kernel size k based on channel dimension C.
    """
    def __init__(self, channels, gamma=2, b=1):
        super(ECA, self).__init__()
        t = int(abs((math.log2(channels) if channels > 0 else 1) / gamma + b / gamma))
        k_size = t if t % 2 != 0 else t + 1
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        self.conv = nn.Conv1d(1, 1, kernel_size=k_size, padding=(k_size - 1) // 2, bias=False)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        b, c, h, w = x.size()
        y = self.avg_pool(x)                          # [B, C, 1, 1]
        y = y.squeeze(-1).transpose(-1, -2)           # [B, 1, C]
        y = self.conv(y)                              # [B, 1, C]
        y = y.transpose(-1, -2).unsqueeze(-1)         # [B, C, 1, 1]
        y = self.sigmoid(y)
        return x * y.expand_as(x)


class LocalSpatialBranch(nn.Module):
    """
    Local Spatial Branch: Captures high-resolution spatial details to handle
    small lesions and irregular disease boundaries.
    """
    def __init__(self, in_channels):
        super(LocalSpatialBranch, self).__init__()
        self.spatial_conv = nn.Sequential(
            nn.Conv2d(in_channels, in_channels // 2, kernel_size=1, bias=False),
            nn.BatchNorm2d(in_channels // 2),
            nn.SiLU(),
            nn.Conv2d(in_channels // 2, in_channels // 2, kernel_size=3, padding=1, groups=in_channels // 2, bias=False),
            nn.BatchNorm2d(in_channels // 2),
            nn.SiLU(),
            nn.Conv2d(in_channels // 2, in_channels, kernel_size=1, bias=False),
            nn.BatchNorm2d(in_channels)
        )
        self.spatial_attn = nn.Sequential(
            nn.Conv2d(2, 1, kernel_size=7, padding=3, bias=False),
            nn.Sigmoid()
        )

    def forward(self, x):
        feat = self.spatial_conv(x)
        avg_out = torch.mean(feat, dim=1, keepdim=True)
        max_out, _ = torch.max(feat, dim=1, keepdim=True)
        spatial_map = self.spatial_attn(torch.cat([avg_out, max_out], dim=1))
        return feat * spatial_map


class MultiScaleConvBranch(nn.Module):
    """
    Multi-scale convolution branch with parallel receptive fields:
    - 3x3 standard conv
    - 5x5 effective conv (via two stacked 3x3s)
    - Dilated 3x3 conv (dilation rate 2)
    Tackles different lesion scales (from tiny spots to broad blights).
    """
    def __init__(self, in_channels):
        super(MultiScaleConvBranch, self).__init__()
        branch_c = in_channels // 3
        rem_c = in_channels - (branch_c * 2)

        # 3x3 Branch
        self.b3x3 = nn.Sequential(
            nn.Conv2d(in_channels, branch_c, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(branch_c),
            nn.SiLU()
        )

        # 5x5 Branch (Stacked 3x3)
        self.b5x5 = nn.Sequential(
            nn.Conv2d(in_channels, branch_c, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(branch_c),
            nn.SiLU(),
            nn.Conv2d(branch_c, branch_c, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(branch_c),
            nn.SiLU()
        )

        # Dilated 3x3 Branch (dilation=2)
        self.bdilated = nn.Sequential(
            nn.Conv2d(in_channels, rem_c, kernel_size=3, padding=2, dilation=2, bias=False),
            nn.BatchNorm2d(rem_c),
            nn.SiLU()
        )

        self.fuse_proj = nn.Sequential(
            nn.Conv2d(in_channels, in_channels, kernel_size=1, bias=False),
            nn.BatchNorm2d(in_channels)
        )

    def forward(self, x):
        f1 = self.b3x3(x)
        f2 = self.b5x5(x)
        f3 = self.bdilated(x)
        concat = torch.cat([f1, f2, f3], dim=1)
        return self.fuse_proj(concat)


class CrossScaleFusion(nn.Module):
    """
    Cross-scale fusion module aggregating spatial features, ECA channel attention,
    and multi-scale receptive field features with residual skip connection.
    """
    def __init__(self, in_channels):
        super(CrossScaleFusion, self).__init__()
        self.fuse_conv = nn.Sequential(
            nn.Conv2d(in_channels * 3, in_channels, kernel_size=1, bias=False),
            nn.BatchNorm2d(in_channels),
            nn.SiLU(),
            nn.Conv2d(in_channels, in_channels, kernel_size=3, padding=1, groups=in_channels, bias=False),
            nn.BatchNorm2d(in_channels),
            nn.SiLU()
        )
        self.alpha = nn.Parameter(torch.ones(1) * 0.5)

    def forward(self, spatial_feat, channel_feat, multiscale_feat, residual):
        concat_feat = torch.cat([spatial_feat, channel_feat, multiscale_feat], dim=1)
        fused = self.fuse_conv(concat_feat)
        return F.silu(residual + self.alpha * fused)


class CAMSA(nn.Module):
    """
    Crop-Aware Multi-Scale Attention Module (CAMSA)
    Structure:
    Input Feature -> 
      ├── Local spatial branch
      ├── Channel attention (ECA)
      ├── Multi-scale convolution (3x3, 5x5, dilated 3x3)
      └── Cross-scale fusion
             │
             ▼
       Enhanced Feature Output
    """
    def __init__(self, channels):
        super(CAMSA, self).__init__()
        self.spatial_branch = LocalSpatialBranch(channels)
        self.eca_branch = ECA(channels)
        self.multiscale_branch = MultiScaleConvBranch(channels)
        self.fusion = CrossScaleFusion(channels)

    def forward(self, x):
        spatial_out = self.spatial_branch(x)
        eca_out = self.eca_branch(x)
        multiscale_out = self.multiscale_branch(x)
        return self.fusion(spatial_out, eca_out, multiscale_out, x)
