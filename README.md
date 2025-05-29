# AI4Farmers: Voice AI Assistant for Indian Agriculture 🌾🇮🇳

## Table of Contents
- [Introduction](#introduction)
- [Features](#features)
- [Core Technologies Used](#core-technologies-used)
- [Architecture](#architecture)
- [Setup and Installation](#setup-and-installation)
  - [Prerequisites](#prerequisites)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
- [How to Use](#how-to-use)
- [Future Enhancements & Google Cloud Vision](#future-enhancements--google-cloud-vision)
- [Contributing](#contributing)
- [License](#license)

---

## Introduction

**AI4Farmers** is an innovative voice-enabled AI assistant designed to empower Indian farmers with timely and accurate agricultural information in their local languages. This project aims to bridge the critical information gap often faced by rural communities, facilitating better decision-making and sustainable farming practices.

Farmers can simply speak their queries in their preferred language, and the AI assistant provides concise, actionable advice on various farming topics. By making vital agricultural knowledge accessible through natural voice interaction, AI4Farmers strives to enhance productivity and improve the livelihoods of farmers across India.

---

## Features

- **Multilingual Voice Interaction**: Supports voice input and output in multiple Indian languages (English, Hindi, Marathi, Tamil, Telugu, Kannada, Bengali).
- **Intelligent Q&A** on:
  - Market Prices (e.g., tomato, onion)
  - Local Weather Conditions (real-time, location-based)
  - Crop Management (planting, irrigation, harvesting)
  - Pest and Disease Control
  - General Farming Queries
- **Context-Aware Conversations**: Maintains session history for personalized responses.
- **User-Friendly Interface**: Built using Streamlit for easy access.

---

## Core Technologies Used

### Frontend
- **Streamlit**: Interactive UI for farmers.
- **SpeechRecognition (Google S2T)**: Converts speech to text.
- **gTTS (Google T2S)**: Converts AI replies to speech.
- **Playsound**: Plays back audio locally.

### Backend (Flask API)
- **Flask**: Handles requests and API logic.
- **Ollama**: Serves open-source LLMs (e.g., LLaMA3) locally.
- **WeatherAPI.com**: Provides real-time weather data.
- **IPinfo.io**: Auto-detects user location.

### Planned (Future Google Cloud Integrations)
- Gemini (via Vertex AI)
- Google AI Studio
- Google Speech-to-Text & Text-to-Speech APIs
- Google Maps Platform
- Vertex AI for MLOps
- TensorFlow / TFX
- BigQuery ML for analytics

---

## Architecture

```text
+---------------+      +-----------------+      +-----------------+
|   Farmer      |      |   Streamlit     |      |    Flask Backend|
| (Voice/Text)  |<---->|   Frontend      |<---->| (backend_app.py)|
+---------------+      |  (app.py)       |      |                 |
                       | - S2T (Google SR)|      | - Session Mgmt  |
                       | - T2S (gTTS)    |      | - WeatherAPI    |
                       | - Displays Chat |      | - LLM Prompts   |
                       +-----------------+      +-----------------+
                                                     |
                                                     | HTTP Request
                                                     V
                                             +-----------------+
                                             |   Ollama Server |
                                             | (Llama3 LLM)     |
                                             +-----------------+
