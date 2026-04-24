# Kiro AI: The Intelligent Autonomous File Agent 🤖📂

![Kiro AI Hero](kiro_ai_hero.png)

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/)
[![UI/UX](https://img.shields.io/badge/UI-PyQt6-violet)]()
[![AI Powered](https://img.shields.io/badge/AI-SBERT%20%2B%20BLIP-green)]()
[![License](https://img.shields.io/badge/License-MIT-yellow)]()

> **Kiro AI** is a state-of-the-art, context-aware autonomous agent designed to revolutionize personal data management. By moving beyond primitive extension-based sorting, Kiro utilizes **Deep Learning** and **Computer Vision** to understand the "soul" of your files—organizing them based on semantic meaning and visual context.

---

## 🚀 Key Innovation: Semantic vs. Structural Sorting
Traditional file organizers look at *extensions* (.txt, .jpg). **Kiro looks at *intent*.** 
- A PDF about "Machine Learning" and a Word doc about "Neural Networks" are grouped together.
- A photo of a "Mountain" and a caption-less image of a "Valley" are recognized as "Nature" and clustered accordingly.

---

## ✨ Features that Define Kiro AI

### 🧠 Semantic Intelligence (NLP)
- **Content-First Analysis:** Uses **Sentence-BERT (SBERT)** to convert document text into high-dimensional semantic vectors.
- **Contextual Grouping:** Employs **Agglomerative Hierarchical Clustering** to discover natural categories without manual input.
- **Smart Labeling:** Automatically derives cluster names by calculating the **Group Centroid** and identifying the most representative keywords.

### 🖼️ Visual Cognition (Computer Vision)
- **Generative Captioning:** Powered by the **BLIP (Bootstrapping Language-Image Pre-training)** model to generate descriptive text for every image.
- **Image-to-Text Clustering:** Maps visual features into the same semantic space as text, allowing for unified organization.
- **Perceptual Hashing:** Integrated **imagehash** logic to identify and manage near-duplicate images with surgical precision.

### 📊 Modern Neural Dashboard
- **Glassmorphism UI:** Built with **PyQt6**, featuring a premium dark-mode interface with smooth transitions and real-time processing feedback.
- **Live Statistics:** A data-driven dashboard that verifies the physical file system against AI predictions in real-time.
- **Cross-Lingual Support:** Fully optimized for both **Arabic (RTL)** and **English (LTR)** workflows.

---

## 🛠️ Technical Deep Dive (The "Engine Room")

### 1. Vectorization & Dimensionality Reduction
To ensure high performance and accuracy, Kiro applies **PCA (Principal Component Analysis)** on the 768-dimensional SBERT embeddings. This reduces noise and computational cost while preserving semantic variance.

### 2. Optimized Clustering Logic
Kiro doesn't guess how many folders you need. It uses the **Silhouette Score** and **Dendrogram Analysis** to mathematically determine the optimal `distance_threshold`, ensuring clusters are neither too broad nor too specific.

### 3. Performance Metrics
Validated against the **BBC News Dataset**, achieving industry-standard scores:
- **ARI (Adjusted Rand Index):** Measures the similarity between predicted and ground truth clusters.
- **NMI (Normalized Mutual Information):** Evaluates the amount of shared information.
- **Purity:** Measures the extent to which clusters contain a single class.

---

## 💻 Tech Stack

| Domain | Technology |
| :--- | :--- |
| **Language** | Python 3.10+ |
| **Framework** | PyQt6 |
| **AI Models** | SBERT (all-mpnet-base-v2), BLIP |
| **ML Libraries** | Scikit-learn, PyTorch, NumPy, SciPy |
| **Document Processing** | PyMuPDF, python-docx |
| **Image Analysis** | PIL, ImageHash |

---

## 👨‍💻 Developed By
**Kiro AI** was engineered by a specialized team at the **Damascus Training Centre (DTC)** - AI Department.

- **Iyad Muhammad** - *Lead AI Engineer & System Architect*
- **Wasim Mahmoud** - *Backend & Data Pipeline*
- **Lana Al-Sheikh** - *UI/UX Design*
- **Academic Supervisor:** Eng. Nour Al-Hakim
- **Department Head:** Eng. Wasim Al-Madi

---

## 🔧 Getting Started

1. **Clone & Navigate:**
   ```bash
   git clone https://github.com/mohamadeyad932-hue/Kiro-ai_agent-for-windose.git
   cd Kiro-ai_agent-for-windose
   ```
2. **Environment Setup:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Execution:**
   ```bash
   python uiux_kiro_pyqt/main.py
   ```

---
*Kiro AI - Transforming digital chaos into structured intelligence.*
