# Optivox Project: Technical Knowledge Base

This document provides a comprehensive overview of the **Optivox** project, an advanced accessibility suite designed to empower users with visual impairments through magnification, OCR, and AI voice assistance.

## 🛠️ Tools & Tech Stack

| Category | Technology | Purpose |
| :--- | :--- | :--- |
| **Language** | Python 3.10+ | Core application logic and scripting. |
| **UI Framework** | PyQt5 | Main dashboard and feature windows; handles system-wide events. |
| **OCR Engine** | Tesseract OCR | Text extraction from images and screen regions. |
| **Vision/Image** | OpenCV (cv2) & NumPy | Image preprocessing (grayscaling, thresholding) for high OCR accuracy. |
| **Vision/Capture** | mss & PyAutoGUI | High-performance screen capture and system interaction. |
| **Speech (TTS)** | pyttsx3 & edge-tts | Multi-tier TTS (offline fallback + high-quality neural voices). |
| **Speech (STT)** | SpeechRecognition | Voice-to-text for commands and AI interaction. |
| **System APIs** | Windows Mag API | Hardware-accelerated system-wide zooming via `ctypes`. |
| **Audio** | Pygame (Mixer) | Low-latency audio playback and management. |
| **AI Backend** | Sarvam AI / Custom API | Powering the Multilingual Voice Assistant. |

---

## 🏗️ System Architecture & Design

### **1. Process-Based Dashboard Architecture**
Optivox uses a **Hub-and-Spoke** model. The main `GUI.py` acts as a central hub that launches separate Python processes for each feature (Magnifier, Reader, Assistant).
*   **Resilience**: A crash in one feature (e.g., the Voice Assistant) does not affect the main GUI or other tools.
*   **Concurrency**: Features can run simultaneously without blocking the main event loop.

### **2. Centralized Settings Management**
A unified `SettingsManager` handles persistent configuration (stored in JSON).
*   **Live Updates**: All child processes poll or receive signals when settings (like zoom level or theme) change, ensuring system-wide consistency.

### **3. Native Hardware Integration**
Instead of software-only zoom, Optivox hooks into the **Windows Magnification API (`Magnification.dll`)**. This provides fluid, 60 FPS magnification that is much faster than traditional screenshot-based zooming.

---

## 🧩 Key Modules

### **🔍 Magnifier Suite**
*   **Full Screen**: System-wide high-speed zoom with global hotkey support.
*   **Hover/Lens**: A magnifying glass that follows the cursor for focused reading.
*   **Fixed Window**: Magnifies a specific portion of the screen (e.g., the top) while leaving the rest normal.

### **🔊 Reader Suite**
*   **OCR Overlay**: Allows users to select any region of the screen (even images/PDFs) to have the text read aloud.
*   **Interactive Readers**: Hover-to-read and paragraph-wise reading modes for efficient content consumption.

### **🎙️ Voice Assistant**
*   **Wake Word Detection**: Listens for "Hey Optivox" to activate.
*   **Multilingual Support**: Can communicate in multiple languages (English, Hindi, etc.).
*   **Local Processing**: Uses local TTS for basic alerts to minimize API costs/latency.

---

## 🌍 Real-Life Problems & Impact

1.  **Visual Accessibility**: Directly solves the problem of navigating complex digital environments for individuals with low vision.
2.  **Dyslexia & Literacy Support**: The OCR/TTS combination allows users who struggle with reading to "hear" anything on their screen.
3.  **Hands-Free Interaction**: Enables users with physical disabilities to interact with their computer via voice commands.
4.  **Digital Inclusion**: Provides a high-premium, accessible UI that encourages elderly users to use modern technology comfortably.

---

## 🚀 Future Scope

*   **WCAG 2.1 Compliance**: Fully auditing the UI to meet international accessibility standards.
*   **Deep AI Integration**: Implementing offline LLMs for the voice assistant to provide privacy-first, zero-latency interactions.
*   **Packaging**: Creating a one-click installer (.exe) for non-technical users.
*   **Cloud Sync**: Allowing users to carry their accessibility settings across different devices.
