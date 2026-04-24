# Kiro AI: The Intelligent Autonomous File Agent 🤖📂

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/)
[![UI/UX](https://img.shields.io/badge/UI-PyQt6-violet)]()
[![AI Powered](https://img.shields.io/badge/AI-SBERT%20%2B%20BLIP-green)]()
[![Status](https://img.shields.io/badge/Status-Beta-orange)]()
[![License](https://img.shields.io/badge/License-MIT-lightgrey)]() > **Kiro AI** is an advanced, context-aware autonomous agent designed to eliminate digital chaos. Unlike traditional organizers that rely on extensions, Kiro understands your documents' meaning and your images' visual content using state-of-the-art **Deep Learning** models.

---

## 📸 Sneak Peek
![Kiro AI Interface](https://via.placeholder.com/800x450.png?text=Add+a+Screenshot+or+GIF+of+Kiro+AI+Here)

---

## 🌟 What's New? (Recent Updates)
* **✨ Modern PyQt6 Interface:** A premium, glassmorphism-inspired UI with smooth animations and dark mode support.
* **📊 Live Neural Dashboard:** Real-time visualization of your file ecosystem, showing exactly how many files were organized and where they moved.
* **🧠 Advanced Clustering Engine:** Switched to **Agglomerative Clustering** with **PCA** dimensionality reduction and **Silhouette Score** for automated, high-precision threshold detection.
* **🌐 Fully Bilingual:** Native support for Arabic and English with seamless RTL/LTR switching.

---

## 🚀 Core Features
* **🔍 Semantic Document Analysis:** Uses **SBERT (Sentence-BERT)** to read and understand the actual content of PDFs, Word docs, and text files.
* **🖼️ Visual Intelligence:** Leverages the **BLIP** model to "see" images, generate captions, and group them by semantic topics.
* **🏷️ Intelligent Naming:** Automatically generates human-readable folder names based on the most dominant semantic themes found in the clusters.
* **⚡ Real-Time Pipeline:** High-performance execution via `QProcess` with live terminal feedback.
* **🛡️ Verification Logic:** Live file-system verification to ensure statistics match the actual files on your disk.

---

## 🛠️ Technical Architecture

| Component | Technology | Role |
| :--- | :--- | :--- |
| **GUI Framework** | PyQt6 | Premium user interface and navigation. |
| **NLP Engine** | SBERT (sbert_high_res) | Generating high-dimensional text embeddings. |
| **Vision Engine** | BLIP Model | Image captioning and visual semantic analysis. |
| **Clustering** | Scikit-learn | Grouping files without predefined categories. |
| **Auto-Threshold** | Scipy (Dendrogram) | Finding the mathematical "sweet spot" for clustering. |
| **Data Bridge** | JSON Metadata | Real-time synchronization between AI backend and UI. |

---

## 👨‍💻 The Team
Developed as a breakthrough project at **Damascus Training Centre (DTC)** - AI Department.

* **Lead Developers:** Iyad Muhammad, Wasim Mahmoud, Lana Al-Sheikh.
* **Academic Supervisor:** Eng. Nour Al-Hakim.
* **Department Head:** Eng. Wasim Al-Madi.

---

## 🔧 Installation & Setup

**1. Clone the Repo:**
```bash
git clone [https://github.com/mohamadeyad932-hue/Kiro-ai_agent-for-windows.git](https://github.com/mohamadeyad932-hue/Kiro-ai_agent-for-windows.git)
cd Kiro-ai_agent
