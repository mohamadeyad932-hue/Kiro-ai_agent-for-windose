# Kiro: Intelligent Windows File Organizer Agent 🤖📂

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/)
[![AI Powered](https://img.shields.io/badge/AI-Powered-green)]()
[![Status](https://img.shields.io/badge/Status-Prototype-orange)]()

> **Kiro** is not just a file sorter; it's a context-aware intelligent agent that lives in your Windows background, understanding your documents, images, and audio files to eliminate digital clutter automatically.

---

## 📖 Overview

In the modern digital workspace, "Digital Clutter" is a productivity killer. Traditional organizers rely on file extensions (.pdf, .jpg), which is primitive. **Kiro** leverages **Large Language Models (LLMs)** and **Computer Vision** to understand the *semantic content* of your files.

Whether it's a financial report, a university lecture, or a personal photo, Kiro analyzes the content and moves it to the right place—or creates a new category for it—without you lifting a finger.

## 🚀 Key Features

* **⚡ Real-Time Monitoring:** Continuously watches Desktop, Downloads, and Documents using `watchdog` events.
* **🧠 Semantic Understanding:**
    * **Text:** Uses **BERT** models to understand the context of PDFs and Word docs.
    * **Audio:** Transcribes audio (MP3/WAV) using **OpenAI Whisper** to classify content (e.g., "Lecture" vs. "Music").
    * **Vision:** Analyzes image content using Vision Models to tag and sort photos based on visual elements.
* **✨ Magical Clustering:** Utilizes **K-Means clustering** to group uncategorized files based on similarity.
* **🛡️ Smart Deduplication:**
    * Uses **Perceptual Hashing** for images (detects duplicates even if resized).
    * Uses **Cosine Similarity** for text documents to find content overlaps.
* **🖥️ User Control:** Simple GUI to toggle the agent on/off.

---

## 🛠️ Technical Architecture & Tech Stack

The project is built using a modular pipeline approach:

| Component | Technology / Library | Description |
| :--- | :--- | :--- |
| **Core Language** | Python 🐍 | The backbone of the agent. |
| **File Operations** | `watchdog`, `shutil` | Event-driven file system monitoring and manipulation. |
| **NLP & Embeddings** | `sentence-transformers` (BERT) | Converting text to vector embeddings for understanding context. |
| **Audio Processing** | `openai-whisper` | State-of-the-art speech-to-text transcription. |
| **Clustering** | `scikit-learn` (K-Means) | Unsupervised learning to group similar documents. |
| **Image Processing** | `imagehash`, `GPT-4V` (Concept) | Perceptual hashing for deduplication and VLM for understanding. |
| **Text Extraction** | `pdfplumber`, `python-docx` | Extracting raw text from various document formats. |

### How It Works (The Pipeline)
1.  **Monitor:** The agent detects a `FileCreated` event in target directories.
2.  **Extract:** Depending on file type, text is extracted or audio is transcribed.
3.  **Embed:** The content is passed through a Transformer model to generate a numerical vector (Embedding).
4.  **Classify/Cluster:** The vector is compared against existing cluster centers (using K-Means) to determine the category.
5.  **Action:** The file is moved to the appropriate folder. If it's a duplicate (checked via Hashing), it is flagged or removed.

---

## 📊 Comparison: Kiro vs. Traditional Assistants

| Feature | Kiro 🤖 | Siri / Cortana 🗣️ | Traditional Scripts 📜 |
| :--- | :---: | :---: | :---: |
| **Focus** | File Organization & Management | General Voice Commands | Basic Extension Sorting |
| **Content Awareness** | ✅ Deep (Semantic) | ❌ None | ❌ None |
| **Automation** | ✅ Proactive (Background) | ❌ Reactive (Waiting for command) | ✅ Reactive |
| **Image Understanding** | ✅ Yes | ❌ No | ❌ No |

---

## 👨‍💻 Team

This project was developed as a graduation project at **Damascus Training Centre (DTC)** - AI Department.

* **Developers:**
    * Iyad Muhammad
    * Wasim Mahmoud
    * Lana Al-Sheikh
* **Supervisor:** Eng. Nour Al-Hakim
* **Head of Department:** Eng. Wasim Al-Madi

---

## 🔮 Future Roadmap
* [ ] Integration with Cloud Services (Google Drive / OneDrive).
* [ ] Cross-platform support (Linux/macOS).
* [ ] Advanced dashboard for viewing file statistics.

---