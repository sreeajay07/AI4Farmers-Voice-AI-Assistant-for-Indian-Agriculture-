import streamlit as st
import requests
import speech_recognition as sr
import uuid
from gtts import gTTS
import tempfile
import playsound
import logging
import os
import threading # Import threading

# --- Configuration ---
# Use environment variables for sensitive info and backend URL
OLLAMA_BASE_URL = os.getenv("BACKEND_URL", "http://localhost:5001")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "1e8dcf1c228a42c5a5d172232252805") # IMPORTANT: Set this in your environment

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__) # Use a logger instance

# --- Streamlit Page Setup ---
st.set_page_config(page_title="AI4Farmers - Voice AI 🌾", layout="wide")
st.title("🌾 AI4Farmers - Voice Assistant")

# --- Helper Functions ---

@st.cache_data(show_spinner=False)
def get_location():
    """Fetches user's approximate location based on IP."""
    try:
        resp = requests.get("https://ipinfo.io/json", timeout=5)
        resp.raise_for_status() # Raise an exception for bad status codes
        data = resp.json()
        logger.info("IPInfo Data: %s", data)
        return data.get("city", ""), data.get("region", ""), data.get("country", "")
    except requests.exceptions.RequestException as e:
        logger.error("IPInfo Error: %s", e)
        st.error("Could not auto-detect location. Please enter your city manually.")
    return "", "", ""

@st.cache_data(show_spinner=False)
def get_weather(city):
    """Fetches current weather data for a given city."""
    if not city or city == "Unknown":
        return None, None, None # Return gracefully if city is not set

    try:
        url = f"http://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q={city}&aqi=no"
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        logger.info("Weather Data: %s", data)
        current = data.get("current", {})
        return (
            current.get("condition", {}).get("text", "N/A"),
            current.get("temp_c", "N/A"),
            current.get("humidity", "N/A")
        )
    except requests.exceptions.RequestException as e:
        logger.error("Weather API Error: %s", e)
        st.error(f"Could not fetch weather for {city}. Please check your API key or city name.")
    return None, None, None

def _play_audio_threaded(file_path):
    """Helper function to play audio in a separate thread."""
    try:
        playsound.playsound(file_path)
        logger.info(f"Successfully played audio file: {file_path}")
    except Exception as e:
        logger.error(f"Error playing sound from {file_path}: {e}", exc_info=True)
        # Note: You can't directly update Streamlit UI from a separate thread
        # so we log the error here.
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Cleaned up temporary audio file: {file_path}")

def speak_text(text, lang_code="en-US"):
    """Converts text to speech, saves to temp file, and plays in a separate thread."""
    if not text.strip():
        logger.warning("Attempted to speak empty text.")
        return

    try:
        tts_lang = lang_code.split("-")[0] # Get the 2-letter code for gTTS
        tts = gTTS(text=text, lang=tts_lang, slow=False)

        # Create a temporary file that is NOT deleted immediately by NamedTemporaryFile
        # Ensure suffix is .mp3 for gTTS
        temp_audio_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        temp_audio_file_path = temp_audio_file.name
        temp_audio_file.close() # Important: Close the file handle immediately so gTTS can write

        tts.save(temp_audio_file_path) # Save the audio to the temporary file

        logger.info(f"Generated audio at: {temp_audio_file_path}. Initiating playback thread.")
        # Start playback in a new thread
        threading.Thread(target=_play_audio_threaded, args=(temp_audio_file_path,)).start()

    except Exception as e:
        logger.error(f"Text-to-speech generation or thread creation error for lang '{lang_code}': {e}", exc_info=True)
        st.warning(f"Could not prepare speech for '{text[:20]}...'. Error: {e}")
        # Clean up if file was created but error occurred before playback attempt
        if 'temp_audio_file_path' in locals() and os.path.exists(temp_audio_file_path):
            os.remove(temp_audio_file_path)


def call_backend_api(prompt, session_id, language, location):
    payload = {
        "prompt": prompt,
        "session_id": session_id,
        "language": language, # This is the 2-letter code for the backend
        "location": location
    }
    try:
        url = f"{OLLAMA_BASE_URL}/ask"
        logger.info(f"Sending to backend: Prompt='{prompt[:50]}...', Session='{session_id}', Lang='{language}', Loc='{location}'")
        resp = requests.post(url, json=payload, timeout=180) # Added timeout for frontend call
        resp.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        data = resp.json()
        logger.info(f"Received from backend: {data}")
        return data.get("response", "No response from the backend.")
    except requests.exceptions.Timeout:
        st.error("The backend server timed out while processing the request.")
        return "AI: I'm taking too long to think. Please try again or simplify your query."
    except requests.exceptions.ConnectionError:
        st.error("Could not connect to the backend server. Is it running?")
        return "AI: I can't connect to my services right now. Please ensure the backend is running."
    except requests.exceptions.RequestException as e:
        st.error(f"An error occurred while communicating with the backend: {e}")
        return f"AI: Sorry, an unexpected error occurred: {str(e)}"
    except Exception as e:
        st.error(f"An unexpected error occurred in API call: {e}")
        return f"AI: An unexpected error occurred: {str(e)}"

# --- Session State Initialization ---
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.chat_history = []
    st.session_state.location_city, st.session_state.location_region, st.session_state.location_country = get_location()
    # Initialize default language as English (2-letter code for backend)
    st.session_state.selected_backend_lang = "en"
    # Ensure selected_sr_code is initialized for the first run
    st.session_state.selected_sr_code = "en-US" 
    # Initialize weather info
    st.session_state.weather_info = get_weather(st.session_state.location_city)

# Manual city input if auto-detection failed
if st.session_state.location_city in ["", "Unknown"]:
    manual_city_input = st.text_input("⚠️ Could not auto-detect your city. Enter it manually:", "", key="manual_city_input")
    if manual_city_input and manual_city_input != st.session_state.location_city: # Only update if changed
        st.session_state.location_city = manual_city_input
        # Re-fetch weather immediately if city is manually set
        st.session_state.weather_info = get_weather(st.session_state.location_city)
        st.experimental_rerun() # Rerun to display updated weather in sidebar

# --- Sidebar Display ---
with st.sidebar:
    st.header("📍 Your Location & Weather")
    st.markdown(f"**City:** {st.session_state.get('location_city', 'Unknown')}")
    if st.session_state.location_region:
        st.markdown(f"**Region:** {st.session_state.location_region}")
    if st.session_state.location_country:
        st.markdown(f"**Country:** {st.session_state.location_country}")

    cond, temp, hum = st.session_state.get("weather_info", (None, None, None))
    if cond and temp and hum:
        st.markdown(f"**Condition:** {cond}")
        st.markdown(f"**Temperature:** {temp} °C")
        st.markdown(f"**Humidity:** {hum}%")
    else:
        st.markdown("⚠️ Weather info not available. Ensure API key is valid and city is correct.")

# --- Language Selection ---
# Map display names to Google Speech Recognition codes and backend 2-letter codes
LANGUAGES = {
    "English": {"sr_code": "en-US", "backend_code": "en"},
    "Hindi": {"sr_code": "hi-IN", "backend_code": "hi"},
    "Marathi": {"sr_code": "mr-IN", "backend_code": "mr"},
    "Tamil": {"sr_code": "ta-IN", "backend_code": "ta"},
    "Telugu": {"sr_code": "te-IN", "backend_code": "te"},
    "Kannada": {"sr_code": "kn-IN", "backend_code": "kn"},
    "Bengali": {"sr_code": "bn-IN", "backend_code": "bn"}
}

# Find the default selected language name if it exists in session state, else English
# This uses the backend_code to find the display name
default_lang_name = next((name for name, codes in LANGUAGES.items() if codes["backend_code"] == st.session_state.selected_backend_lang), "English")

selected_lang_name = st.selectbox(
    "Select your language:",
    list(LANGUAGES.keys()),
    index=list(LANGUAGES.keys()).index(default_lang_name), # Set default selection
    key="language_selector"
)

# Update session state with the new backend language code when selection changes
st.session_state.selected_backend_lang = LANGUAGES[selected_lang_name]["backend_code"]
# Also store the SR code for speech recognition/TTS
st.session_state.selected_sr_code = LANGUAGES[selected_lang_name]["sr_code"]


# --- Main Chat Interface ---
r = sr.Recognizer() # Initialize Speech Recognizer once

# Voice Input
st.markdown("---")
st.subheader("Speak your farming question:")
if st.button("🎤 Start Listening"):
    st.info("🎤 Listening... Speak clearly now.")
    try:
        with sr.Microphone() as source:
            # Adjust for noise once per listening session
            r.adjust_for_ambient_noise(source, duration=0.5) 
            audio = r.listen(source, timeout=8, phrase_time_limit=8) # Shorter timeout/limit
            with st.spinner("Processing speech..."):
                recognized_text = r.recognize_google(audio, language=st.session_state.selected_sr_code) # Use SR code
            st.success(f"**You said:** \"{recognized_text}\"")

            # Validate recognized text (simple check)
            if not recognized_text.strip():
                st.warning("No speech detected or could not understand. Please try again.")
            else:
                st.session_state.chat_history.append({"role": "user", "content": recognized_text})
                # Call backend and get reply
                with st.spinner("AI is thinking..."):
                    reply = call_backend_api(
                        prompt=recognized_text,
                        session_id=st.session_state.session_id,
                        language=st.session_state.selected_backend_lang, # Use the selected 2-letter backend language code
                        location=st.session_state.location_city
                    )
                st.session_state.chat_history.append({"role": "assistant", "content": reply})
                speak_text(reply, st.session_state.selected_sr_code) # Use SR code for TTS

    except sr.WaitTimeoutError:
        st.warning("No speech detected. You waited too long.")
    except sr.UnknownValueError:
        st.warning("Sorry, I could not understand the audio.")
    except sr.RequestError as e:
        st.error(f"Could not request results from Google Speech Recognition service; {e}")
    except Exception as e:
        st.error(f"An unexpected error occurred during listening: {e}")

# Text Input
st.subheader("Or type your farming question:")
user_input_text = st.text_input("Type here and press Enter:", key="text_input_box")

if user_input_text:
    st.session_state.chat_history.append({"role": "user", "content": user_input_text})
    with st.spinner("AI is thinking..."):
        reply = call_backend_api(
            prompt=user_input_text,
            session_id=st.session_state.session_id,
            language=st.session_state.selected_backend_lang, # Use the selected 2-letter backend language code
            location=st.session_state.location_city
        )
    st.session_state.chat_history.append({"role": "assistant", "content": reply})
    speak_text(reply, st.session_state.selected_sr_code) # Use SR code for TTS
    st.experimental_rerun() # Rerun to clear text input and show new message

# --- Chat History & Reset ---
st.markdown("---")
st.subheader("Chat History")
for chat_message in reversed(st.session_state.chat_history): # Display most recent at top
    if chat_message["role"] == "user":
        st.markdown(f"**You:** {chat_message['content']}")
    else:
        st.markdown(f"**AI:** {chat_message['content']}")

# Reset chat button
if st.button("🔄 Reset Chat"):
    st.session_state.chat_history = []
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.pop('weather_info', None) # Clear cached weather to re-fetch on reset
    st.experimental_rerun() # Force rerun to clear all display