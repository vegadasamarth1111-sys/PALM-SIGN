# PALM-SIGN

Real-Time Palm & Hand Sign Language Recognition and Translation Workbench.

## Overview

**PALM-SIGN** is a computer vision and machine learning system that recognizes palm and hand sign gestures in real time using a standard webcam. It features a complete modular pipeline including face suppression, adaptive skin color segmentation, contour and Fourier shape feature extraction, classification, and an interactive Flask web dashboard for real-time inference and dataset collection.

---

## Features

- **Live Vision Engine**: Real-time video capture and gesture tracking with OpenCV.
- **Robust Segmentation**:
  - HSV/YCrCb skin segmentation with presets (Daylight, Room Light, Low Light).
  - Whole-frame Haar Cascade face detection to suppress facial false positives.
  - Region-of-Interest (ROI) cropping with convex hull and contour analysis.
- **Multi-Descriptor Feature Extraction**:
  - Normalized geometric moments and Hu moments.
  - Elliptic Fourier descriptors (frequency domain contour analysis).
  - Radial distance signatures and convexity defect features.
- **Classification Engine**:
  - Machine learning classification using scikit-learn models (SVM / Random Forest / Ensemble).
  - Confidence scoring, exponential smoothing, and temporal gesture commitment hold.
- **Web Application & Workbench**:
  - Flask web app with interactive UI (`templates/index.html`, `static/app.js`, `static/style.css`).
  - Live video feed, real-time prediction overlays, and customizable skin mask tuning.
  - Built-in dataset collector and model retrainer from the browser.
- **Comprehensive Project Documentation**:
  - Automated project report generator, presentation deck generator, UML diagrams, and performance metrics in `docs/report`.

---

## Project Structure

```text
PALM-SIGN/
├── dataset/                  # Sign gesture dataset (Alphabet A-Z)
├── docs/                     # Project report, presentations, diagrams & metrics
├── models/                   # Pretrained models and settings
│   ├── settings.json
│   └── sign_model.joblib
├── src/                      # Core computer vision pipeline
│   ├── classifier.py         # Classifier training and inference
│   ├── config.py             # Global configuration, presets, and constants
│   ├── dataset.py            # Dataset loader and validation
│   ├── engine.py             # Multithreaded VisionEngine for video capture & pipeline
│   ├── features.py           # Contour, geometric & Fourier feature extractors
│   ├── motion.py             # Temporal smoothing and motion tracking
│   ├── preprocess.py         # Frame normalization and color conversions
│   └── segment.py            # Skin segmentation and contour isolation
├── static/                   # Frontend assets (CSS, JS)
├── templates/                # Frontend HTML templates
├── app.py                    # Flask web application server
├── haarcascade_frontalface_default.xml  # Haar cascade for face suppression
├── smoke_seg.py              # Segmentation smoke test utility
└── README.md                 # Project documentation
```

---

## Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/vegadasamarth1111-sys/PALM-SIGN.git
   cd PALM-SIGN
   ```

2. **Create and activate a virtual environment** (recommended):
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Linux / macOS:
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install flask opencv-python numpy scikit-learn joblib
   ```

---

## Usage

### Run Web Application
Launch the Flask development server:
```bash
python app.py
```
Open your browser and navigate to `http://localhost:5000` to interact with the workbench.

### Run Segmentation Smoke Test
Test the segmentation and feature extraction pipeline on sample frames:
```bash
python smoke_seg.py
```

---

## Dataset

The `dataset/` directory contains sample gesture images categorized by alphabet classes (`A` through `Z`). New gestures can be collected directly through the web UI's data collection tool.

---

## License

This project is open-source and available for educational and research purposes.
