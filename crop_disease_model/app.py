import os
import time
import cv2
import numpy as np
import torch
import streamlit as st
from PIL import Image

from models.yolov13_multitask import YOLOv13MultiTaskNet
from dataset.synthetic_dataset import generate_synthetic_crop_image, CROP_CLASSES, DISEASE_CLASSES, SEVERITY_CLASSES
from evaluate import compute_model_efficiency
from explainability import GradCAM, overlay_gradcam

# Page Config
st.set_page_config(
    page_title="YOLOv13 Multi-Task Crop Disease Diagnosis & Severity System",
    page_icon="🌿",
    layout="wide"
)

# Custom Styling
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-title {
        font-size: 1.1rem;
        text-align: center;
        color: #4B5563;
        margin-bottom: 2rem;
    }
    .metric-box {
        background-color: #F3F4F6;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #3B82F6;
        margin-bottom: 1rem;
    }
    .stAlert {
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🌿 YOLOv13 Multi-Task Attention Network for Agricultural Disease Diagnosis</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Multi-Crop Identification • Lesion Segmentation • Mask-Conditioned Disease Classification • Severity Prediction</div>', unsafe_allow_html=True)

@st.cache_resource
def load_model():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = YOLOv13MultiTaskNet(num_crops=len(CROP_CLASSES), num_diseases=len(DISEASE_CLASSES)).to(device)
    checkpoint_path = "best_model.pth"
    if os.path.exists(checkpoint_path):
        try:
            ckpt = torch.load(checkpoint_path, map_location=device)
            model.load_state_dict(ckpt["model_state"], strict=False)
        except Exception as e:
            st.warning(f"Note: Loaded model with partial checkpoint alignment: {e}")
    model.eval()
    return model, device

model, device = load_model()
eff_metrics = compute_model_efficiency(model, device=device)

# Sidebar Options
st.sidebar.header("⚙️ Control Panel")
input_option = st.sidebar.radio("Select Image Input Source:", ["Generate Sample Crop Image", "Upload Custom Image"])

selected_sample = None
uploaded_file = None

if input_option == "Generate Sample Crop Image":
    sample_seed = st.sidebar.slider("Sample Random Seed:", 0, 100, 42)
    if st.sidebar.button("🎲 Generate New Leaf Sample"):
        st.session_state["sample_seed"] = np.random.randint(0, 1000)

    current_seed = st.session_state.get("sample_seed", sample_seed)
    np.random.seed(current_seed)
    selected_sample = generate_synthetic_crop_image(img_size=256)
    img_pil = Image.fromarray((selected_sample["image"].permute(1, 2, 0).numpy() * 255).astype(np.uint8))
else:
    uploaded_file = st.sidebar.file_uploader("Upload Crop Leaf Image (PNG/JPG):", type=["png", "jpg", "jpeg"])
    if uploaded_file is not None:
        img_pil = Image.open(uploaded_file).convert("RGB").resize((256, 256))
    else:
        st.info("👆 Please upload a crop leaf image from the sidebar.")
        st.stop()

# Layout Columns
col_left, col_right = st.columns([1, 1.2])

with col_left:
    st.subheader("🖼️ Input Crop Image")
    st.image(img_pil, use_container_width=True)

    # Convert Image to Tensor
    img_np = np.array(img_pil).astype(np.float32) / 255.0
    img_tensor = torch.from_numpy(img_np.transpose(2, 0, 1)).float().unsqueeze(0).to(device)

    # Run Multi-Task Inference
    t0 = time.time()
    with torch.no_grad():
        outputs = model(img_tensor)
    latency_ms = (time.time() - t0) * 1000.0

    crop_idx = torch.argmax(outputs["crop_logits"], dim=1).item()
    crop_conf = torch.softmax(outputs["crop_logits"], dim=1)[0, crop_idx].item()
    
    disease_idx = torch.argmax(outputs["disease_logits"], dim=1).item()
    disease_conf = torch.softmax(outputs["disease_logits"], dim=1)[0, disease_idx].item()

    sev_ratio = outputs["severity_ratio"].item() * 100.0
    sev_stage_idx = torch.argmax(outputs["severity_stage"], dim=1).item()

    st.subheader("⚡ Real-Time Efficiency Benchmarks")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Latency", f"{latency_ms:.1f} ms")
    m2.metric("FPS", f"{eff_metrics['fps']:.1f}")
    m3.metric("Params", f"{eff_metrics['params_m']:.2f} M")
    m4.metric("FLOPs", f"{eff_metrics['gflops']:.2f} G")

with col_right:
    st.subheader("📊 Multi-Task Diagnostic Results")

    # Diagnostic Summary Box
    st.success(f"**Crop Species**: {CROP_CLASSES[crop_idx]} (Confidence: {crop_conf*100:.1f}%)")
    
    if disease_idx == 0:
        st.info(f"**Disease Status**: Healthy Leaf (Confidence: {disease_conf*100:.1f}%)")
    else:
        st.error(f"**Diagnosed Disease**: {DISEASE_CLASSES[disease_idx]} (Confidence: {disease_conf*100:.1f}%)")

    # Severity Progress Bar
    st.markdown(f"**Disease Severity Index**: **{sev_ratio:.2f}%** ({SEVERITY_CLASSES[sev_stage_idx]} Infection Stage)")
    st.progress(min(int(sev_ratio), 100))

    # Tabs for Visual Maps & Diagrams
    tab1, tab2, tab3, tab4 = st.tabs(["🧩 Lesion Mask", "📍 Localization Box", "🧠 Grad-CAM", "📐 Architecture Diagrams"])

    with tab1:
        seg_mask_np = outputs["seg_mask"].squeeze().detach().cpu().numpy()
        seg_mask_colored = cv2.applyColorMap(np.uint8(255 * seg_mask_np), cv2.COLORMAP_MAGMA)
        seg_mask_rgb = cv2.cvtColor(seg_mask_colored, cv2.COLOR_BGR2RGB)
        st.image(seg_mask_rgb, caption="Predicted Pixel-Wise Lesion Mask M", use_container_width=True)

    with tab2:
        bbox_img = (img_np * 255).astype(np.uint8).copy()
        if disease_idx != 0:
            contours, _ = cv2.findContours(np.uint8(seg_mask_np > 0.4), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for cnt in contours:
                x, y, w, h = cv2.boundingRect(cnt)
                if w > 10 and h > 10:
                    cv2.rectangle(bbox_img, (x, y), (x + w, y + h), (255, 0, 0), 2)
                    cv2.putText(bbox_img, f"{DISEASE_CLASSES[disease_idx][:15]}", (x, max(y-5, 15)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        st.image(bbox_img, caption="Disease Localization & Bounding Boxes", use_container_width=True)

    with tab3:
        try:
            grad_cam = GradCAM(model, model.disease_head.conv_roi[0])
            cam_heatmap, _ = grad_cam.generate_heatmap(img_tensor, target_class=disease_idx)
            cam_overlay = overlay_gradcam(img_np, cam_heatmap)
            st.image(cam_overlay, caption="Grad-CAM Focus: Symptomatic Lesion Region vs Background Context", use_container_width=True)
        except Exception as e:
            st.warning(f"Grad-CAM visualization: {e}")

    with tab4:
        st.write("**CAMSA Module Architecture Diagram**")
        if os.path.exists("diagrams/camsa_diagram.png"):
            st.image("diagrams/camsa_diagram.png", use_container_width=True)
        st.write("**CAFA Mechanism Architecture Diagram**")
        if os.path.exists("diagrams/cafa_diagram.png"):
            st.image("diagrams/cafa_diagram.png", use_container_width=True)
        st.write("**Mask-Conditioned Pipeline Diagram**")
        if os.path.exists("diagrams/mask_conditioned_pipeline.png"):
            st.image("diagrams/mask_conditioned_pipeline.png", use_container_width=True)

st.markdown("---")
st.markdown("<center><small>Antigravity AI • YOLOv13-based Multi-Task Attention Network with CAMSA & CAFA Modules</small></center>", unsafe_allow_html=True)
