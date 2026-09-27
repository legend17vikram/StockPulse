import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Set clean style
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['font.size'] = 11

def draw_camsa_diagram(save_path="diagrams/camsa_diagram.png"):
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
    ax.axis('off')
    
    # Background card
    rect = patches.FancyBboxPatch((0.02, 0.02), 0.96, 0.96, boxstyle="round,pad=0.02",
                                  ec="#1E3A8A", fc="#F8FAFC", lw=2)
    ax.add_patch(rect)

    # Title
    ax.text(0.5, 0.92, "Crop-Aware Multi-Scale Attention Module (CAMSA)", 
            ha='center', va='center', fontsize=14, fontweight='bold', color="#1E3A8A")

    # Input Box
    ax.text(0.5, 0.81, "Input Feature X [B, C, H, W]", ha='center', va='center',
            bbox=dict(boxstyle="round,pad=0.5", fc="#3B82F6", ec="#1E3A8A", lw=1.5),
            color="white", fontweight='bold', fontsize=11)

    # Downward arrow to branches
    ax.annotate("", xy=(0.5, 0.73), xytext=(0.5, 0.77),
                arrowprops=dict(arrowstyle="->", lw=2, color="#1E3A8A"))

    # Branch Boxes
    branches = [
        ("Local Spatial Branch", "1x1 Conv -> 3x3 Depthwise -> 7x7 Spatial Attn\n(Captures Small Lesions & Irregular Borders)", 0.15),
        ("Channel Attention (ECA)", "Adaptive 1D Conv Channel Weighting\n(Efficient Cross-Channel Interdependencies)", 0.50),
        ("Multi-Scale Convolution", "Parallel 3x3, 5x5, & Dilated 3x3 (rate 2)\n(Multi-Scale Lesion Receptive Fields)", 0.85)
    ]

    for title, desc, x_pos in branches:
        # Branch box
        bbox = patches.FancyBboxPatch((x_pos - 0.14, 0.42), 0.28, 0.28, boxstyle="round,pad=0.02",
                                       ec="#10B981", fc="#FFFFFF", lw=1.5)
        ax.add_patch(bbox)
        ax.text(x_pos, 0.65, title, ha='center', va='center', fontweight='bold', color="#065F46", fontsize=10.5)
        ax.text(x_pos, 0.52, desc, ha='center', va='center', fontsize=8.5, color="#1F2937", multialignment='center')

        # Line from input to branch
        ax.plot([0.5, x_pos], [0.73, 0.70], color="#1E3A8A", lw=1.5)
        ax.annotate("", xy=(x_pos, 0.70), xytext=(0.5, 0.73),
                    arrowprops=dict(arrowstyle="->", lw=1.5, color="#1E3A8A"))

        # Line from branch to fusion
        ax.annotate("", xy=(0.5, 0.27), xytext=(x_pos, 0.42),
                    arrowprops=dict(arrowstyle="->", lw=1.5, color="#1E3A8A"))

    # Cross Scale Fusion Box
    ax.text(0.5, 0.23, "Cross-Scale Fusion Module\nConcat(Spatial, ECA, MultiScale) -> Conv1x1 + Residual Skip (α)", 
            ha='center', va='center',
            bbox=dict(boxstyle="round,pad=0.5", fc="#10B981", ec="#065F46", lw=1.5),
            color="white", fontweight='bold', fontsize=10.5)

    # Final Output arrow
    ax.annotate("", xy=(0.5, 0.08), xytext=(0.5, 0.16),
                arrowprops=dict(arrowstyle="->", lw=2.5, color="#1E3A8A"))
    ax.text(0.5, 0.05, "Enhanced Feature Output F_enhanced", ha='center', va='center',
            fontweight='bold', fontsize=12, color="#1E3A8A")

    plt.tight_layout()
    plt.savefig(save_path, bbox_inches='tight')
    plt.close()
    print(f"[OK] Saved CAMSA diagram to {save_path}")

def draw_cafa_diagram(save_path="diagrams/cafa_diagram.png"):
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
    ax.axis('off')

    rect = patches.FancyBboxPatch((0.02, 0.02), 0.96, 0.96, boxstyle="round,pad=0.02",
                                  ec="#10B981", fc="#F8FAFC", lw=2)
    ax.add_patch(rect)

    ax.text(0.5, 0.92, "Crop-Aware Feature Adaptation (CAFA) Mechanism", 
            ha='center', va='center', fontsize=14, fontweight='bold', color="#065F46")

    # Inputs
    ax.text(0.2, 0.78, "Visual Features (F)\n[B, C_feat, H, W]", ha='center', va='center',
            bbox=dict(boxstyle="round,pad=0.5", fc="#3B82F6", ec="#1E3A8A", lw=1.5),
            color="white", fontweight='bold', fontsize=10.5)

    ax.text(0.8, 0.78, "Crop Embedding (C)\n[B, D_embed]", ha='center', va='center',
            bbox=dict(boxstyle="round,pad=0.5", fc="#EC4899", ec="#9D174D", lw=1.5),
            color="white", fontweight='bold', fontsize=10.5)

    # Connections to Attention Generator
    ax.annotate("", xy=(0.5, 0.58), xytext=(0.2, 0.71),
                arrowprops=dict(arrowstyle="->", lw=2, color="#1E3A8A"))
    ax.annotate("", xy=(0.5, 0.58), xytext=(0.8, 0.71),
                arrowprops=dict(arrowstyle="->", lw=2, color="#9D174D"))

    # Crop-Aware Attention Generator Box
    ax.text(0.5, 0.53, "Crop-Aware Attention Generator A(F, C)\nSigmoid( Conv3x3( Conv1x1(F) + Linear(C) ) )", 
            ha='center', va='center',
            bbox=dict(boxstyle="round,pad=0.5", fc="#8B5CF6", ec="#5B21B6", lw=1.5),
            color="white", fontweight='bold', fontsize=11)

    # Arrow to Multiplication
    ax.annotate("", xy=(0.5, 0.38), xytext=(0.5, 0.46),
                arrowprops=dict(arrowstyle="->", lw=2, color="#5B21B6"))

    # Direct line from F to Multiplication
    ax.annotate("", xy=(0.35, 0.30), xytext=(0.2, 0.71),
                arrowprops=dict(arrowstyle="->", lw=1.5, color="#3B82F6", connectionstyle="arc3,rad=0.2"))

    # Element-wise Multiplication Box
    ax.text(0.5, 0.30, "Element-Wise Multiplication (⊙)", ha='center', va='center',
            bbox=dict(boxstyle="circle,pad=0.4", fc="#F59E0B", ec="#B45309", lw=1.5),
            color="white", fontweight='bold', fontsize=10)

    # Arrow to Output
    ax.annotate("", xy=(0.5, 0.16), xytext=(0.5, 0.24),
                arrowprops=dict(arrowstyle="->", lw=2.5, color="#1E3A8A"))

    # Equation Banner
    ax.text(0.5, 0.10, "F_adapted = F ⊙ A(F, C)", ha='center', va='center',
            bbox=dict(boxstyle="round,pad=0.5", fc="#10B981", ec="#065F46", lw=2),
            color="white", fontweight='bold', fontsize=13)

    plt.tight_layout()
    plt.savefig(save_path, bbox_inches='tight')
    plt.close()
    print(f"[OK] Saved CAFA diagram to {save_path}")

def draw_mask_conditioned_pipeline(save_path="diagrams/mask_conditioned_pipeline.png"):
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
    ax.axis('off')

    rect = patches.FancyBboxPatch((0.02, 0.02), 0.96, 0.96, boxstyle="round,pad=0.02",
                                  ec="#3B82F6", fc="#F8FAFC", lw=2)
    ax.add_patch(rect)

    ax.text(0.5, 0.92, "Mask-Conditioned Disease Classification P(D | I, M)", 
            ha='center', va='center', fontsize=14, fontweight='bold', color="#1E3A8A")

    # Image -> Backbone
    ax.text(0.12, 0.70, "Input Image (I)", ha='center', va='center',
            bbox=dict(boxstyle="round,pad=0.4", fc="#3B82F6", ec="#1E3A8A"), color="white", fontweight='bold')
    
    ax.annotate("", xy=(0.28, 0.70), xytext=(0.20, 0.70), arrowprops=dict(arrowstyle="->", lw=2, color="#1E3A8A"))

    ax.text(0.38, 0.70, "Shared Backbone\n(YOLOv13 + CAMSA)", ha='center', va='center',
            bbox=dict(boxstyle="round,pad=0.4", fc="#8B5CF6", ec="#5B21B6"), color="white", fontweight='bold')

    # Branches from Backbone
    ax.annotate("", xy=(0.60, 0.85), xytext=(0.48, 0.70), arrowprops=dict(arrowstyle="->", lw=1.5, color="#1E3A8A"))
    ax.text(0.75, 0.85, "Crop Classification Head --> Crop Embed C", ha='center', va='center',
            bbox=dict(boxstyle="round,pad=0.3", fc="#EC4899", ec="#9D174D"), color="white", fontweight='bold', fontsize=9.5)

    ax.annotate("", xy=(0.60, 0.55), xytext=(0.48, 0.70), arrowprops=dict(arrowstyle="->", lw=1.5, color="#1E3A8A"))
    ax.text(0.75, 0.55, "Disease Segmentation Decoder\nOutputs Disease Mask M", ha='center', va='center',
            bbox=dict(boxstyle="round,pad=0.4", fc="#10B981", ec="#065F46"), color="white", fontweight='bold', fontsize=10)

    # Arrow from Mask M to ROI Masking
    ax.annotate("", xy=(0.75, 0.38), xytext=(0.75, 0.47), arrowprops=dict(arrowstyle="->", lw=2, color="#065F46"))

    ax.text(0.75, 0.32, "Lesion ROI Spatial Masking\nF_roi = F_adapted ⊙ (M + 0.1)", ha='center', va='center',
            bbox=dict(boxstyle="round,pad=0.4", fc="#F59E0B", ec="#B45309"), color="white", fontweight='bold', fontsize=10)

    # Arrow to Disease Classifier
    ax.annotate("", xy=(0.75, 0.18), xytext=(0.75, 0.26), arrowprops=dict(arrowstyle="->", lw=2, color="#B45309"))

    ax.text(0.75, 0.12, "Mask-Conditioned Classifier P(D | I, M)", ha='center', va='center',
            bbox=dict(boxstyle="round,pad=0.5", fc="#EF4444", ec="#991B1B"), color="white", fontweight='bold', fontsize=11)

    # Comparison note
    ax.text(0.30, 0.22, "Traditional Approach: P(D | I) [Cheats on Background]\nProposed Approach: P(D | I, M) [Focuses on Lesion ROI]", 
            ha='center', va='center', fontsize=9.5, fontweight='bold', color="#1E3A8A",
            bbox=dict(boxstyle="round,pad=0.4", fc="#EFF6FF", ec="#3B82F6"))

    plt.tight_layout()
    plt.savefig(save_path, bbox_inches='tight')
    plt.close()
    print(f"[OK] Saved Mask-Conditioned pipeline diagram to {save_path}")

if __name__ == "__main__":
    draw_camsa_diagram()
    draw_cafa_diagram()
    draw_mask_conditioned_pipeline()
