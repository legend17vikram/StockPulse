import os
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

def create_presentation():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # Color Palette
    PRIMARY_COLOR = RGBColor(30, 58, 138)     # Navy Blue
    SECONDARY_COLOR = RGBColor(16, 185, 129)  # Emerald Green
    DARK_TEXT = RGBColor(31, 41, 55)         # Charcoal Dark
    LIGHT_BG = RGBColor(248, 250, 252)       # Soft Off-white
    WHITE = RGBColor(255, 255, 255)
    ACCENT_BLUE = RGBColor(59, 130, 246)
    GRAY_TEXT = RGBColor(107, 114, 128)

    def set_slide_background(slide, color):
        background = slide.background
        fill = background.fill
        fill.solid()
        fill.fore_color.rgb = color

    def add_header(slide, title_text, subtitle_text):
        # Header text frame
        tx_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(1.0))
        tf = tx_box.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

        p1 = tf.paragraphs[0]
        p1.text = title_text
        p1.font.bold = True
        p1.font.size = Pt(26)
        p1.font.color.rgb = PRIMARY_COLOR

        p2 = tf.add_paragraph()
        p2.text = subtitle_text
        p2.font.size = Pt(14)
        p2.font.color.rgb = GRAY_TEXT
        p2.space_before = Pt(4)

    # ==========================================
    # SLIDE 1: Title Slide
    # ==========================================
    slide1 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide1, PRIMARY_COLOR)

    # Decorative Card
    shape = slide1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.0), Inches(1.2), Inches(11.333), Inches(5.1))
    shape.fill.solid()
    shape.fill.fore_color.rgb = WHITE
    shape.line.color.rgb = SECONDARY_COLOR
    shape.line.width = Pt(2)

    tf1 = shape.text_frame
    tf1.word_wrap = True
    tf1.margin_left = Inches(0.6)
    tf1.margin_right = Inches(0.6)
    tf1.margin_top = Inches(0.6)

    p = tf1.paragraphs[0]
    p.text = "MINOR PROJECT PRESENTATION"
    p.font.bold = True
    p.font.size = Pt(16)
    p.font.color.rgb = SECONDARY_COLOR

    p = tf1.add_paragraph()
    p.text = "A YOLOv13-based Multi-Task Attention Network with Cross-Scale Feature Fusion for Multi-Crop Disease Localization, Classification and Severity Prediction"
    p.font.bold = True
    p.font.size = Pt(24)
    p.font.color.rgb = PRIMARY_COLOR
    p.space_before = Pt(14)

    p = tf1.add_paragraph()
    p.text = "Crop-Aware Multi-Scale Attention (CAMSA) • Feature Adaptation (CAFA) • Mask-Conditioned MTL"
    p.font.size = Pt(14)
    p.font.color.rgb = GRAY_TEXT
    p.space_before = Pt(14)

    p = tf1.add_paragraph()
    p.text = "\nPresenter / Author: Raj Vikram\nDomain: Agricultural Computer Vision & Deep Learning"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = DARK_TEXT

    # ==========================================
    # SLIDE 2: Problem Statement & Motivation
    # ==========================================
    slide2 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide2, LIGHT_BG)
    add_header(slide2, "1. Problem Statement & Motivation", "Agricultural Vision Challenges in Plant Disease Diagnosis")

    problems = [
        ("Small Lesions", "Early-stage disease spots occupy less than 1-2% of total leaf pixel area."),
        ("Irregular Boundaries", "Lesions have ambiguous, complex, non-geometrical shape contours."),
        ("Multi-Scale Variations", "Varying lesion scales from tiny rust specks to massive late blight areas."),
        ("Confusing Symptoms", "High inter-class visual similarity between different fungal and bacterial diseases."),
        ("Cross-Crop Variations", "Plant species (Tomato, Potato, Grape, Maize, Pepper) exhibit distinct visual backgrounds.")
    ]

    for idx, (title, desc) in enumerate(problems):
        top_pos = Inches(1.6 + idx * 1.0)
        card = slide2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), top_pos, Inches(11.733), Inches(0.85))
        card.fill.solid()
        card.fill.fore_color.rgb = WHITE
        card.line.color.rgb = ACCENT_BLUE

        tf = card.text_frame
        tf.word_wrap = True
        tf.margin_left = Inches(0.3)
        tf.margin_top = Inches(0.15)
        
        p = tf.paragraphs[0]
        p.text = f"• {title}: "
        p.font.bold = True
        p.font.size = Pt(15)
        p.font.color.rgb = PRIMARY_COLOR
        
        run = p.add_run()
        run.text = desc
        run.font.bold = False
        run.font.size = Pt(14)
        run.font.color.rgb = DARK_TEXT

    # ==========================================
    # SLIDE 3: Proposed Multi-Task Objectives
    # ==========================================
    slide3 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide3, LIGHT_BG)
    add_header(slide3, "2. Proposed Multi-Task Objectives", "Integrated End-to-End Deep Learning Pipeline")

    tasks = [
        ("Task 1: Crop Identification", "Identify crop species (Tomato, Potato, Grape, Maize, Pepper) and generate crop embedding vector C."),
        ("Task 2: Disease Localization", "YOLO-based bounding box detection predicting location (cx, cy, w, h) of diseased leaf regions."),
        ("Task 3: Disease Segmentation", "Pixel-wise spatial segmentation generating exact disease lesion mask M."),
        ("Task 4: Mask-Conditioned Classification", "Classify disease category using lesion ROI features P(D | I, M) to ignore background context."),
        ("Task 5: Severity Prediction Engine", "Quantify % surface area infected and assign clinical severity stage (Healthy, Mild, Moderate, Severe).")
    ]

    for idx, (title, desc) in enumerate(tasks):
        top_pos = Inches(1.6 + idx * 1.0)
        card = slide3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), top_pos, Inches(11.733), Inches(0.85))
        card.fill.solid()
        card.fill.fore_color.rgb = WHITE
        card.line.color.rgb = SECONDARY_COLOR

        tf = card.text_frame
        tf.word_wrap = True
        tf.margin_left = Inches(0.3)
        tf.margin_top = Inches(0.15)

        p = tf.paragraphs[0]
        p.text = f"{title}\n"
        p.font.bold = True
        p.font.size = Pt(15)
        p.font.color.rgb = SECONDARY_COLOR

        p2 = tf.add_paragraph()
        p2.text = desc
        p2.font.size = Pt(13)
        p2.font.color.rgb = DARK_TEXT

    # ==========================================
    # SLIDE 4: Architectural Novelty 1: CAMSA Module
    # ==========================================
    slide4 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide4, LIGHT_BG)
    add_header(slide4, "3. Novelty 1: CAMSA Module", "Crop-Aware Multi-Scale Attention Module with Cross-Scale Fusion")

    camsa_points = [
        ("Local Spatial Branch", "Captures high-resolution spatial details to preserve fine lesion boundaries."),
        ("ECA Channel Attention", "Efficient channel attention capturing cross-channel interdependencies without dimension reduction."),
        ("Multi-Scale Convolutions", "Parallel 3x3, 5x5, and dilated 3x3 (rate=2) convolutions to handle varying lesion scales."),
        ("Cross-Scale Fusion", "Aggregates multi-receptive field representations with a residual skip connection.")
    ]

    for idx, (title, desc) in enumerate(camsa_points):
        left_pos = Inches(0.8 + (idx % 2) * 5.9)
        top_pos = Inches(1.6 + (idx // 2) * 2.6)

        card = slide4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left_pos, top_pos, Inches(5.6), Inches(2.3))
        card.fill.solid()
        card.fill.fore_color.rgb = WHITE
        card.line.color.rgb = PRIMARY_COLOR
        card.line.width = Pt(1.5)

        tf = card.text_frame
        tf.word_wrap = True
        tf.margin_left = Inches(0.3)
        tf.margin_top = Inches(0.3)

        p = tf.paragraphs[0]
        p.text = title
        p.font.bold = True
        p.font.size = Pt(18)
        p.font.color.rgb = PRIMARY_COLOR

        p2 = tf.add_paragraph()
        p2.text = desc
        p2.font.size = Pt(14)
        p2.font.color.rgb = DARK_TEXT
        p2.space_before = Pt(10)

    # ==========================================
    # SLIDE 5: Architectural Novelty 2: CAFA Mechanism
    # ==========================================
    slide5 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide5, LIGHT_BG)
    add_header(slide5, "4. Novelty 2: CAFA Mechanism", "Crop-Aware Feature Adaptation Mechanism")

    card5 = slide5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.6), Inches(11.733), Inches(5.1))
    card5.fill.solid()
    card5.fill.fore_color.rgb = WHITE
    card5.line.color.rgb = SECONDARY_COLOR
    card5.line.width = Pt(2)

    tf5 = card5.text_frame
    tf5.word_wrap = True
    tf5.margin_left = Inches(0.5)
    tf5.margin_top = Inches(0.4)

    p = tf5.paragraphs[0]
    p.text = "Mathematical Formulation:"
    p.font.bold = True
    p.font.size = Pt(18)
    p.font.color.rgb = SECONDARY_COLOR

    p = tf5.add_paragraph()
    p.text = "F_adapted = F ⊙ A(F, C)"
    p.font.bold = True
    p.font.size = Pt(24)
    p.font.color.rgb = PRIMARY_COLOR
    p.space_before = Pt(10)

    cafa_desc = [
        "F = Visual feature representation extracted from YOLO multi-scale backbone",
        "C = Crop species embedding vector derived from Crop Classification Head",
        "A(F, C) = Crop-aware cross-attention map gating visual features spatially and channel-wise",
        "F_adapted = Crop-conditioned feature map",
        "\nCore Insight: Allows the network to learn that the visual meaning of a lesion depends partly on the crop species (e.g. early blight looks different on Tomato vs Potato)."
    ]

    for line in cafa_desc:
        p = tf5.add_paragraph()
        p.text = "• " + line if not line.startswith("\nCore") else line
        p.font.size = Pt(15)
        p.font.color.rgb = DARK_TEXT
        p.space_before = Pt(6)

    # ==========================================
    # SLIDE 6: Multi-Task Architecture & Uncertainty Loss
    # ==========================================
    slide6 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide6, LIGHT_BG)
    add_header(slide6, "5. Multi-Task Loss Formulation", "Adaptive Uncertainty-Based Loss Weighting")

    card6 = slide6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.6), Inches(11.733), Inches(5.1))
    card6.fill.solid()
    card6.fill.fore_color.rgb = WHITE
    card6.line.color.rgb = ACCENT_BLUE
    card6.line.width = Pt(2)

    tf6 = card6.text_frame
    tf6.word_wrap = True
    tf6.margin_left = Inches(0.5)
    tf6.margin_top = Inches(0.4)

    p = tf6.paragraphs[0]
    p.text = "Total Loss Equation:"
    p.font.bold = True
    p.font.size = Pt(18)
    p.font.color.rgb = PRIMARY_COLOR

    p = tf6.add_paragraph()
    p.text = "L_total = λ_c L_crop + λ_d L_disease + λ_s L_seg + λ_det L_det + λ_sev L_sev"
    p.font.bold = True
    p.font.size = Pt(22)
    p.font.color.rgb = SECONDARY_COLOR
    p.space_before = Pt(10)

    p = tf6.add_paragraph()
    p.text = "Homoscedastic Uncertainty Parameterization:"
    p.font.bold = True
    p.font.size = Pt(18)
    p.font.color.rgb = PRIMARY_COLOR
    p.space_before = Pt(14)

    p = tf6.add_paragraph()
    p.text = "L_total = Σ_i [ (1 / 2σ_i²) L_i + log σ_i ]"
    p.font.bold = True
    p.font.size = Pt(22)
    p.font.color.rgb = ACCENT_BLUE
    p.space_before = Pt(8)

    p = tf6.add_paragraph()
    p.text = "• Dynamically learns task precisions during training without manual hyperparameter tuning."
    p.font.size = Pt(15)
    p.font.color.rgb = DARK_TEXT
    p.space_before = Pt(12)

    # ==========================================
    # SLIDE 7: Systematic Ablation Study Results
    # ==========================================
    slide7 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide7, LIGHT_BG)
    add_header(slide7, "6. Systematic Ablation Benchmark", "Empirical Evaluation Across Architecture Components")

    rows = 6
    cols = 6
    table_shape = slide7.shapes.add_table(rows, cols, Inches(0.8), Inches(1.6), Inches(11.733), Inches(5.0))
    table = table_shape.table

    headers = ["Model Variant", "mAP@0.50", "Dice Score", "F1-Score", "Params (M)", "FPS"]
    for col_idx, h in enumerate(headers):
        cell = table.cell(0, col_idx)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = PRIMARY_COLOR
        for paragraph in cell.text_frame.paragraphs:
            paragraph.font.bold = True
            paragraph.font.size = Pt(14)
            paragraph.font.color.rgb = WHITE
            paragraph.alignment = PP_ALIGN.CENTER

    ablation_data = [
        ["YOLOv13 baseline", "0.2726", "0.2275", "0.0094", "18.06 M", "17.0"],
        ["+ ECA", "0.2859", "0.2520", "0.1696", "18.06 M", "15.6"],
        ["+ MS feature module (CAMSA)", "0.2992", "0.2835", "0.0528", "18.06 M", "16.3"],
        ["+ segmentation branch", "0.0250", "0.0475", "0.0335", "18.06 M", "11.0"],
        ["Proposed (CAMSA + CAFA + MTL)", "0.3325", "0.3500", "0.3325", "18.06 M", "9.6"]
    ]

    for row_idx, row_data in enumerate(ablation_data):
        for col_idx, val in enumerate(row_data):
            cell = table.cell(row_idx + 1, col_idx)
            cell.text = val
            cell.fill.solid()
            cell.fill.fore_color.rgb = WHITE if row_idx % 2 == 0 else RGBColor(241, 245, 249)
            for paragraph in cell.text_frame.paragraphs:
                if row_idx == 4:
                    paragraph.font.bold = True
                    paragraph.font.color.rgb = SECONDARY_COLOR
                else:
                    paragraph.font.color.rgb = DARK_TEXT
                paragraph.font.size = Pt(13)
                paragraph.alignment = PP_ALIGN.CENTER if col_idx > 0 else PP_ALIGN.LEFT

    # ==========================================
    # SLIDE 8: Multi-Task Evaluation & Real-Time Metrics
    # ==========================================
    slide8 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide8, LIGHT_BG)
    add_header(slide8, "7. Evaluation & Real-Time Performance", "Comprehensive Metrics Across All Task Heads")

    metrics_list = [
        ("Parameter Count", "18.06 M"),
        ("Model Size (Disk)", "68.97 MB"),
        ("Inference Latency", "106.33 ms"),
        ("Inference Speed", "9.4 FPS"),
        ("FLOPs", "147.94 GFLOPs"),
        ("Crop Classification Acc", "19.00%"),
        ("Disease Classification Acc", "34.00%"),
        ("Dice Segmentation Score", "0.3400"),
        ("mIoU Score", "0.3400")
    ]

    for idx, (name, val) in enumerate(metrics_list):
        left_pos = Inches(0.8 + (idx % 3) * 3.9)
        top_pos = Inches(1.6 + (idx // 3) * 1.7)

        card = slide8.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left_pos, top_pos, Inches(3.7), Inches(1.5))
        card.fill.solid()
        card.fill.fore_color.rgb = WHITE
        card.line.color.rgb = ACCENT_BLUE

        tf = card.text_frame
        tf.word_wrap = True
        tf.margin_left = Inches(0.2)
        tf.margin_top = Inches(0.2)

        p = tf.paragraphs[0]
        p.text = name
        p.font.size = Pt(13)
        p.font.color.rgb = GRAY_TEXT

        p2 = tf.add_paragraph()
        p2.text = val
        p2.font.bold = True
        p2.font.size = Pt(22)
        p2.font.color.rgb = PRIMARY_COLOR
        p2.space_before = Pt(6)

    # ==========================================
    # SLIDE 9: Explainability & Diagnostic Interpretability
    # ==========================================
    slide9 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide9, LIGHT_BG)
    add_header(slide9, "8. Explainability & Grad-CAM Analysis", "Demonstrating Symptomatic Region Focus vs Background Context")

    card9 = slide9.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.6), Inches(11.733), Inches(5.1))
    card9.fill.solid()
    card9.fill.fore_color.rgb = WHITE
    card9.line.color.rgb = PRIMARY_COLOR
    card9.line.width = Pt(2)

    tf9 = card9.text_frame
    tf9.word_wrap = True
    tf9.margin_left = Inches(0.5)
    tf9.margin_top = Inches(0.4)

    p = tf9.paragraphs[0]
    p.text = "Explainable Artificial Intelligence (XAI) Highlights:"
    p.font.bold = True
    p.font.size = Pt(18)
    p.font.color.rgb = PRIMARY_COLOR

    points = [
        "Grad-CAM Heatmap Generation: Implemented Grad-CAM on mask-conditioned disease classification head.",
        "Symptomatic ROI Verification: Confirms high activation maps align directly with disease lesion spots.",
        "Background Context Rejection: Verifies model ignores soil, non-diseased leaf areas, and field backgrounds.",
        "Agricultural Credibility: Increases trustworthiness and transparency for real-world farmer deployment."
    ]

    for pt in points:
        p = tf9.add_paragraph()
        p.text = "• " + pt
        p.font.size = Pt(15)
        p.font.color.rgb = DARK_TEXT
        p.space_before = Pt(14)

    # ==========================================
    # SLIDE 10: Streamlit Interactive Web Application
    # ==========================================
    slide10 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide10, LIGHT_BG)
    add_header(slide10, "9. Interactive Streamlit Web Dashboard", "Real-Time Multi-Task GUI Deployment")

    card10 = slide10.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.6), Inches(11.733), Inches(5.1))
    card10.fill.solid()
    card10.fill.fore_color.rgb = WHITE
    card10.line.color.rgb = SECONDARY_COLOR
    card10.line.width = Pt(2)

    tf10 = card10.text_frame
    tf10.word_wrap = True
    tf10.margin_left = Inches(0.5)
    tf10.margin_top = Inches(0.4)

    p = tf10.paragraphs[0]
    p.text = "Streamlit Web App Features (app.py):"
    p.font.bold = True
    p.font.size = Pt(18)
    p.font.color.rgb = SECONDARY_COLOR

    gui_features = [
        "Multi-Crop File Uploader & Random Synthetic Sample Generator.",
        "Real-Time Diagnostic Cards: Crop class confidence & disease diagnosis status.",
        "Disease Severity Meter: Percentage leaf area infected with progress bar.",
        "Interactive Result Tabs: Pixel-wise segmentation mask, Bounding Box localization, and Grad-CAM explainability overlay.",
        "Efficiency Monitor: Real-time latency (ms), FPS counter, Parameter count (M), and FLOPs."
    ]

    for feat in gui_features:
        p = tf10.add_paragraph()
        p.text = "• " + feat
        p.font.size = Pt(15)
        p.font.color.rgb = DARK_TEXT
        p.space_before = Pt(12)

    # ==========================================
    # SLIDE 11: Conclusion & Future Work
    # ==========================================
    slide11 = prs.slides.add_slide(blank_layout)
    set_slide_background(slide11, PRIMARY_COLOR)

    card11 = slide11.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.0), Inches(1.2), Inches(11.333), Inches(5.1))
    card11.fill.solid()
    card11.fill.fore_color.rgb = WHITE
    card11.line.color.rgb = SECONDARY_COLOR
    card11.line.width = Pt(2)

    tf11 = card11.text_frame
    tf11.word_wrap = True
    tf11.margin_left = Inches(0.6)
    tf11.margin_top = Inches(0.5)

    p = tf11.paragraphs[0]
    p.text = "10. Conclusion & Future Scope"
    p.font.bold = True
    p.font.size = Pt(22)
    p.font.color.rgb = PRIMARY_COLOR

    concl_points = [
        "Summary: Developed a novel YOLOv13 multi-task attention network uniting crop identification, disease localization, lesion segmentation, and severity prediction.",
        "Novelty: Introduced CAMSA (cross-scale attention) and CAFA (crop-aware feature adaptation) to solve agricultural vision challenges.",
        "Future Scope 1: Deploy on edge devices (Nvidia Jetson Nano, Raspberry Pi) using TensorRT optimization.",
        "Future Scope 2: Extend cross-crop domain generalization to unseen tropical crop species.",
        "\nThank You! Questions & Discussion."
    ]

    for pt in concl_points:
        p = tf11.add_paragraph()
        p.text = "• " + pt if not pt.startswith("\nThank") else pt
        p.font.bold = True if pt.startswith("\nThank") else False
        p.font.size = Pt(18) if pt.startswith("\nThank") else Pt(15)
        p.font.color.rgb = SECONDARY_COLOR if pt.startswith("\nThank") else DARK_TEXT
        p.space_before = Pt(12)

    output_ppt_path = "Minor_Project_Presentation.pptx"
    prs.save(output_ppt_path)
    print(f"[OK] PowerPoint presentation saved successfully to '{output_ppt_path}'")

if __name__ == "__main__":
    create_presentation()
