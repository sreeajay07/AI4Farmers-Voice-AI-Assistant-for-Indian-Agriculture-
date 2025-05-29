# AI4Farmers: Voice AI Assistant for Indian Agriculture 🌾🇨🇳

## Table of Contents

* [Introduction](#introduction)
* [Features](#features)
* [Core Technologies Used](#core-technologies-used)
* [Architecture](#architecture)
* [Setup and Installation](#setup-and-installation)

  * [Prerequisites](#prerequisites)
  * [Backend Setup](#backend-setup)
  * [Frontend Setup](#frontend-setup)
* [How to Use](#how-to-use)
* [Future Enhancements & Google Cloud Vision](#future-enhancements--google-cloud-vision)
* [Contributing](#contributing)
* [License](#license)

## Introduction

AI4Farmers is an innovative voice-enabled AI assistant designed to empower Indian farmers with timely and accurate agricultural information in their local languages. This project aims to bridge the critical information gap often faced by rural communities, facilitating better decision-making and sustainable farming practices.

Farmers can simply speak their queries in their preferred language, and the AI assistant provides concise, actionable advice on various farming topics. By making vital agricultural knowledge accessible through natural voice interaction, AI4Farmers strives to enhance productivity and improve the livelihoods of farmers across India.

## Features

* **Multilingual Voice Interaction:** Supports voice input and output in multiple Indian languages (English, Hindi, Marathi, Tamil, Telugu, Kannada, Bengali).
* **Intelligent Q\&A:** Provides relevant advice on:

  * Market Prices: General and specific crop prices (e.g., tomato, onion).
  * Local Weather Conditions: Real-time weather data based on the farmer's location.
  * Crop Management: Advice on planting, irrigation, harvesting.
  * Pest and Disease Control: Information and recommendations.
  * General Farming Queries: Broad agricultural guidance.
* **Context-Aware Conversations:** Maintains chat history to provide more relevant follow-up responses.
* **User-Friendly Interface:** Built with Streamlit for a simple and accessible web application.

## Core Technologies Used

Our AI4Farmers prototype is built with a vision for future scalability on Google Cloud. Currently, we leverage open-source components alongside crucial Google AI capabilities:

### Frontend:

* **Streamlit:** For creating the interactive web user interface.
* **Speech Recognition Library:** Utilizes Google's Speech-to-Text (S2T) capabilities to convert spoken farmer queries into text.
* **gTTS (Google Text-to-Speech):** Leverages Google's T2S capabilities to convert the AI's responses back into natural-sounding speech.
* **Playsound:** For local audio playback of the TTS output.

### Backend (Flask API):

* **Flask:** A lightweight Python web framework for handling API requests.
* **Ollama:** Hosts and serves our open-source LLM (e.g., Llama3).
* **Requests:** For communicating with external APIs (Ollama, WeatherAPI) and internal services.
* **WeatherAPI.com:** A third-party API for fetching real-time weather data.
* **IPinfo.io:** A third-party API for IP-based location detection.

### Planned/Conceptual Google AI Integrations (Future Vision):

* **Gemini via Vertex AI:** As the core conversational AI model.
* **Google AI Studio:** For advanced prompt engineering.
* **Google Cloud Speech-to-Text & Text-to-Speech APIs:** For improved S2T and T2S.
* **Google Maps Platform:** For precise location services.
* **Vertex AI:** For deploying and managing models.
* **TensorFlow / TFX:** For custom model development (e.g., crop disease image analysis).
* **BigQuery ML:** For predictive modeling and large-scale analytics.

## Architecture

The project follows a client-server architecture:

```
+---------------+      +-----------------+      +------------------+
|   Farmer      |      |   Streamlit     |      |   Flask Backend  |
| (Voice/Text)  |<---->|   Frontend      |<---->|  (backend_app.py) |
+---------------+      |  (app.py)       |      |                  |
                       | - S2T (Google SR)|      | - Session Mgmt   |
                       | - T2S (gTTS)     |      | - WeatherAPI     |
                       | - Chat UI       |      | - LLM Prompts    |
                       +-----------------+      +------------------+
                                                          |
                                                          |
                                                    +------------------+
                                                    |  Ollama Server   |
                                                    | (Llama3 LLM)     |
                                                    +------------------+
```

## Setup and Installation

### Prerequisites

* Python 3.8+
* pip
* Ollama ([https://ollama.com](https://ollama.com))

Pull the Llama3 model:

```bash
ollama run llama3
```

### Backend Setup

```bash
git clone <your_repo_url>
cd <your_repo_name>/backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file:

```env
OLLAMA_URL=http://localhost:11434
WEATHER_API_KEY=YOUR_WEATHER_API_KEY_HERE
```

Run the Flask app:

```bash
python backend_app.py
```

### Frontend Setup

```bash
cd ../frontend
source ../backend/venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file:

```env
BACKEND_URL=http://localhost:5001
WEATHER_API_KEY=YOUR_WEATHER_API_KEY_HERE
```

Run the Streamlit frontend:

```bash
streamlit run app.py
```

## How to Use

1. Start all services: Ollama, Flask, Streamlit.
2. Open Streamlit UI ([http://localhost:8501](http://localhost:8501)).
3. Select preferred language.
4. Allow or input location manually.
5. Use voice or text to ask farming queries.
6. Get AI response via text and speech.
7. Use reset button to clear chat.

## Future Enhancements & Google Cloud Vision

* **LLM Upgrade:** Migrate to Gemini 1.5 Pro on Vertex AI.
* **Enhanced Voice Tech:** Use Google Cloud Speech-to-Text and Text-to-Speech APIs.
* **Satellite Intelligence:** Integrate Agricultural Landscape Understanding (ALU) API.
* **Deployment:** Use GKE or Cloud Run with full MLOps via Vertex AI.
* **Data & Analytics:** BigQuery ML + Cloud Storage.
* **Location Intelligence:** Use Maps APIs for hyper-local context.

## Contributing

We welcome contributions! Please fork the repository and submit a pull request.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.git init

