from flask import Flask, request, jsonify
import requests
import uuid
import logging
import os
import sys
import json

app = Flask(__name__)

# --- Configuration ---
OLLAMA_BASE_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3") # <<--- Ensure this is llama3 for better conversational capabilities
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "1e8dcf1c228a42c5a5d172232252805") # Replace with your actual key
WEATHER_API_URL = "http://api.weatherapi.com/v1/current.json"

# --- Logging Setup ---
# Set to DEBUG to see full message payloads sent to Ollama, crucial for debugging history issues
logging.basicConfig(
    level=logging.DEBUG, # Set to DEBUG for now to catch all logs
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

session_histories = {}

# --- Farming Keywords for Intent Detection ---
# These keywords are still useful for the LLM's context if you decide to tell it about specific topics.
# But for the initial filtering logic, we're removing the immediate refusal based on them.
FARMING_KEYWORDS = [
    'market', 'price', 'rate', 'sell', 'buy', 'cost', 'value', 'demand', 'supply',
    'tomato', 'onion', 'potato', 'rice', 'wheat', 'corn', 'maize', 'beans', 'lentils', 'pulses', 'vegetable', 'fruit', 'crop',
    'weather', 'climate', 'soil', 'fertilizer', 'pest', 'disease', 'farm', 'agriculture',
    'seed', 'harvest', 'yield', 'irrigation', 'tractor', 'cultivation', 'farming', 'farmer',
    'equipment', 'maintenance', 'machine', 'tools', 'ploughing', 'sowing', 'harvester',
    'grapes', 'bad smell', 'rot', 'spoiled', 'smelly', 'दुर्गन्धी', 'अंगुर', 'अंगूर',
    'சந்தை', 'விலை', 'தாமம்', 'மண்டி', 'பசார்', 'பாவ்', 'பொருள்', 'பொருள் விலை', 'தேவை', 'அளவு',
    'தக்காளி', 'வெங்காயம்', 'உருளைக்கிழங்கு', 'அரிசி', 'கோதுமை', 'மக்காச்சோளம்', 'பீன்ஸ்', 'பயறு', 'காய்கறி', 'பழம்', 'பயிர்',
    'வானிலை', 'கிளைமேட்', 'மழை', 'சூழ்நிலை', 'நிலம்', 'உரம்', 'பூச்சி', 'நோய்', 'நீர்', 'களையெடுப்பு', 'கடன்',
    'விவசாயி', 'பண்ணை', 'உற்பத்தி', 'நடவு', 'சாகுபடி', 'வறட்சி', 'வெப்பநிலை', 'ஈரப்பதம்', 'ஈரத்தன்மை',
    'मौसम', 'फसल', 'कृषि', 'बाजार', 'दाम', 'मंडी', 'खाद', 'मिट्टी', 'बीज', 'सिंचाई',
    'कीट', 'रोग', 'खेती', 'लागत', 'उत्पादन', 'किसान', 'खेत', 'बुवाई', 'कटाई', 'सूखा', 'तापमान', 'आर्द्रता',
    'टमाटर', 'प्याज', 'आलू', 'चावल', 'गेहूं', 'मक्का', 'सेम', 'दालें', 'सब्जी', 'फल',
    'వాతావరణం', 'పంట', 'రైతు', 'వ్యవసాయం', 'ధర', 'మార్కెట్', 'విత్తనం', 'నేల', 'తెగులు',
    'నీటిపారుదల', 'ఎరువు', 'దిగుబడి', 'సేద్యం', 'కొనుగోలు', 'అమ్మకం', 'వర్షం', 'ఎండ',
    'టమాటా', 'ఉల్లిపాయ', 'బంగాళాదుంప', 'వరి', 'గోధుమ', 'మొక్కజొన్న', 'చిక్కుడు', 'పప్పుధాన్యాలు', 'కూరగాయలు', 'పండ్లు',
    'हवामान', 'पिक', 'शेती', 'खते', 'बाजारभाव', 'माती', 'बियाणे', 'कीटकनाशके', 'सिंचन',
    'पीकपाणी', 'रोगराई', 'शेतकरी', 'मशागत', 'पेरणी', 'काढणी', 'पाऊस', 'ऊन',
    'टोमॅटो', 'कांदा', 'बटाटा', 'तांदूळ', 'गहू', 'मका', 'शेंगा', 'डाळी', 'भाजी', 'फळ'
]

def contains_farming_keywords(text):
    # Added .strip() for robustness against leading/trailing whitespace
    text_lower = text.lower().strip()
    found = any(keyword.lower() in text_lower for keyword in FARMING_KEYWORDS)
    logger.debug(f"Keyword check for '{text_lower[:50]}...': {found}")
    return found

def get_market_prices(lang="en", product=None):
    general_prices = {
        "en": "Current market prices are dynamic. Generally, wheat is around ₹2100/quintal, rice ₹2600/quintal, and common vegetables like tomatoes ₹30/kg. Prices vary daily and by location. Please check local mandi for exact rates.",
        "hi": "वर्तमान बाजार भाव अस्थिर हैं। सामान्यतः, गेहूं ₹2100/क्विंटल, चावल ₹2600/क्विंटल और टमाटर जैसे आम सब्जियां ₹30/किलोग्राम के आसपास हैं। दरें दैनिक और स्थान के अनुसार बदलती रहती हैं। सटीक दरों के लिए स्थानीय मंडी में जांच करें।",
        "ta": "தற்போதைய சந்தை விலைகள் மாறும் தன்மை கொண்டவை. பொதுவாக, கோதுமை ₹2100/குவின்டால், அரிசி ₹2600/குவின்டால் மற்றும் தக்காளி போன்ற பொதுவான காய்கறிகள் ₹30/கிலோ அளவில் உள்ளன. விலைகள் தினசரி மற்றும் இடத்திற்கு ஏற்ப மாறுபடும். துல்லியமான கட்டணங்களுக்கு உள்ளூர் சந்தையை சரிபார்க்கவும்.",
        "te": "ప్రస్తుత మార్కెట్ ధరలు మారుతూ ఉంటాయి. సాధారణంగా, గోధుమ క్వింటాల్‌కు ₹2100, బియ్యం క్వింటాల్‌కు ₹2600, మరియు టమాటాలు వంటి సాధారణ కూరగాయలు కిలోకు ₹30 చుట్టూ ఉన్నాయి. ధరలు రోజువారీ మరియు ప్రాంతాన్ని బట్టి మారుతూ ఉంటాయి. ఖచ్చితమైన రేట్ల కోసం స్థానిక మార్కెట్‌ను తనిఖీ చేయండి.",
        "mr": "सध्याचे बाजारभाव अस्थिर आहेत. साधारणपणे, गहू ₹2100/क्विंटल, तांदूळ ₹2600/क्विंटल, आणि टोमॅटोसारख्या सामान्य भाज्या ₹30/किलोग्रामच्या आसपास आहेत. दर दररोज आणि ठिकाणानुसार बदलतात. अचूक दरांसाठी स्थानिक मंडईत तपासणी करा."
    }

    specific_prices = {
        "tomato": {
            "en": "Tomato price is currently around ₹30-35 per kilogram. Prices can vary.",
            "hi": "टमाटर का भाव अभी ₹30-35 प्रति किलोग्राम है। कीमतें बदल सकती हैं।",
            "ta": "தக்காளி விலை தற்போது ஒரு கிலோவுக்கு ₹30-35 ஆக உள்ளது. விலைகள் மாறுபடலாம்.",
            "te": "టమాటా ధర ప్రస్తుతం కిలోకు ₹30-35 మధ్య ఉంది. ధరలు మారవచ్చు.",
            "mr": "टोमॅटोचा भाव सध्या ₹30-35 प्रति किलो आहे. किमती बदलू शकतात."
        },
        "onion": {
            "en": "Onion price is typically around ₹25-30 per kilogram today.",
            "hi": "प्याज का भाव आमतौर पर आज ₹25-30 प्रति किलोग्राम के आसपास है।",
            "ta": "வெங்காயத்தின் விலை இன்று பொதுவாக ஒரு கிலோவுக்கு ₹25-30 ஆக இருக்கும்.",
            "te": "ఉల్లిపాయ ధర సాధారణంగా ఈరోజు కిలోకు ₹25-30 మధ్య ఉంటుంది.",
            "mr": "कांद्याचा भाव आज साधारणपणे ₹25-30 प्रति किलो आहे."
        }
    }

    if product and product.lower() in specific_prices:
        return specific_prices[product.lower()].get(lang, specific_prices[product.lower()]["en"])
    else:
        return general_prices.get(lang, general_prices["en"])

def get_weather(location, lang="en"):
    if not WEATHER_API_KEY or WEATHER_API_KEY == "YOUR_ACTUAL_WEATHER_API_KEY":
        logger.warning("Weather API key not set or is default value. Cannot fetch live weather.")
        return "WEATHER_API_DATA_ERROR: Weather info unavailable: API key missing or invalid."
    try:
        params = {"key": WEATHER_API_KEY, "q": location, "aqi": "no", "lang": lang}
        resp = requests.get(WEATHER_API_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        logger.info(f"Weather API response for {location}: {data}")

        current = data.get("current", {})
        cond_text = current.get("condition", {}).get("text", "N/A")
        temp_c = current.get("temp_c", "N/A")
        humidity = current.get("humidity", "N/A")

        return f"WEATHER_API_DATA: Location: {location}, Condition: {cond_text}, Temperature: {temp_c}°C, Humidity: {humidity}%."

    except requests.exceptions.Timeout:
        logger.error(f"Weather API call timed out for {location}.")
        return f"WEATHER_API_DATA_ERROR: Sorry, weather information for {location} could not be retrieved in time."
    except requests.exceptions.ConnectionError:
        logger.error(f"Could not connect to Weather API for {location}.")
        return f"WEATHER_API_DATA_ERROR: Sorry, I'm unable to connect to the weather service for {location}."
    except requests.exceptions.RequestException as e:
        error_info = f"HTTP Status: {e.response.status_code}, Response: {getattr(e.response, 'text', 'N/A')}" if e.response else str(e)
        logger.error(f"Weather API call failed for {location} (Error: {error_info}).")
        return f"WEATHER_API_DATA_ERROR: Sorry, weather information for {location} is currently unavailable. (Error: {error_info})"
    except Exception as e:
        logger.error(f"An unexpected error occurred in get_weather for {location}: {e}", exc_info=True)
        return f"WEATHER_API_DATA_ERROR: Sorry, weather information is currently unavailable due to an unexpected error: {e}"

def get_refusal_message(language):
    # This message is now primarily for the LLM's system prompt,
    # not for direct filtering in the backend code.
    messages = {
        "ta": "நான் விவசாயம் தொடர்பான கேள்விகளுக்கு மட்டுமே பதிலளிக்க முடியும்.",
        "hi": "मैं केवल कृषि से संबंधित प्रश्नों के उत्तर दे सकता हूँ।",
        "te": "నేను వ్యవసాయ సంబంధిత ప్రశ్నలకు మాత్రమే సమాధానం ఇవ్వగలను.",
        "mr": "मी फक्त शेतीसंबंधित प्रश्नांची उत्तरे देऊ शकतो。",
        "en": "I can only answer farming-related questions."
    }
    return messages.get(language, messages["en"])

@app.route('/ask', methods=['POST'])
def ask():
    data = request.json
    if not data:
        logger.error("Received non-JSON request or empty request.")
        return jsonify({"error": "Request must be JSON"}), 400

    session_id = data.get("session_id", str(uuid.uuid4()))
    language = data.get("language", "en").lower()
    location = data.get("location", "Unknown")
    prompt = data.get("prompt", "").strip()

    if not prompt:
        logger.warning("Received empty prompt.")
        return jsonify({"error": "Prompt is required"}), 400

    logger.info(f"Processing request: Session ID='{session_id}', Language='{language}', Location='{location}', Prompt='{prompt[:100]}...'")

    if session_id not in session_histories:
        session_histories[session_id] = []
        logger.info(f"Initialized new session history for {session_id}")
    else:
        logger.info(f"Using existing session history for {session_id}. Current length: {len(session_histories[session_id])}")
        logger.debug(f"Current history for {session_id}: {json.dumps(session_histories[session_id], indent=2)}")

    # --- CRUCIAL CHANGE: THIS BLOCK IS COMMENTED OUT ---
    # We are removing the explicit backend filter and relying on the LLM's system prompt
    # to handle non-farming questions.
    # if not contains_farming_keywords(prompt):
    #     refusal = get_refusal_message(language)
    #     logger.info(f"Non-farming query detected for session {session_id}. Responding with refusal: '{refusal[:50]}...'")
    #     return jsonify({
    #         "session_id": session_id,
    #         "response": refusal
    #     })
    # --- END OF CRUCIAL CHANGE ---

    extra_info_messages = []
    prompt_lower = prompt.lower()

    # Define keywords for specific products (can be expanded)
    product_keywords = {
        "tomato": ['tomato', 'தக்காளி', 'टमाटर', 'టమాటా', 'टोमॅटो'],
        "onion": ['onion', 'வெங்காயம்', 'प्याज', 'ఉల్లిపాయ', 'కాंदा']
    }

    # --- Market Price Check ---
    is_market_query = False
    requested_product = None
    market_check_keywords = ['market', 'price', 'rate', 'சந்தை', 'விலை', 'தாமம்', 'மண்டி', 'भाव', 'commodities', 'आज का भाव', 'current rate', 'कीमत']

    if any(keyword in prompt_lower for keyword in market_check_keywords):
        is_market_query = True
        for product, keywords in product_keywords.items():
            if any(p_keyword in prompt_lower for p_keyword in keywords):
                requested_product = product
                break # Found a specific product

    if is_market_query:
        market_data = get_market_prices(lang=language, product=requested_product)
        extra_info_messages.append({"role": "system", "content": f"MARKET_INFO: {market_data}"})
        logger.info(f"Added market info to context for session {session_id}. Product: {requested_product}")

    # --- Weather Check ---
    weather_check_keywords = ['weather', 'climate', 'வானிலை', 'கிளைமேட்', 'मौसम', 'हवामान', 'तापमान', 'மழை', 'வெப்பநிலை', 'humidity', 'temperature', 'conditions', 'rain', 'sunny', 'cloudy', 'cold', 'hot', 'बारिश', 'धूप', 'ठंड', 'गर्म']

    if any(keyword in prompt_lower for keyword in weather_check_keywords):
        weather_data = get_weather(location, lang=language)
        extra_info_messages.append({"role": "system", "content": f"WEATHER_INFO: {weather_data}"})
        logger.info(f"Added weather info to context for session {session_id}.")

    # Append user's current prompt to history *before* sending to Ollama*
    session_histories[session_id].append({"role": "user", "content": prompt})

    # --- Helper function for dynamic weather advice examples ---
    def get_weather_example(lang, condition):
        examples = {
            "Sunny/Clear": {
                "ta": "தெளிவான வானிலை. அறுவடைக்கு நல்லது. நீர்ப்பாசனத்திற்கு திட்டமிடுங்கள்.",
                "hi": "साफ मौसम है। कटाई के लिए अच्छा है। सिंचाई की योजना बनाएं।",
                "en": "Clear weather. Good for harvesting. Plan for irrigation."
            },
            "Rainy/Drizzle": {
                "ta": "மழை தூறல் உள்ளது. நீர் வடிகால் சரிபார்த்து, அறுவடையை ஒத்திவைக்கலாம்.",
                "hi": "बारिश की बूंदाबांदी है। जल निकासी जांचें, कटाई स्थगित कर सकते हैं।",
                "en": "There is a drizzle. Check drainage; you might postpone harvest."
            },
            "Hot": {
                "ta": "வெப்பநிலை அதிகம். நீர்ப்பாசனம் செய்யவும், நிழல் வலைகளை பயன்படுத்தவும்.",
                "hi": "तापमान अधिक है। सिंचाई करें, शेड नेट का प्रयोग करें।",
                "en": "High temperature. Irrigate, use shade nets."
            },
            "Cold": {
                "ta": "குளிர்ச்சியான வானிலை. பயிர்களை பாதுகாக்கவும்.",
                "hi": "ठंडा मौसम है। फसलों को सुरक्षित रखें।",
                "en": "Cold weather. Protect crops."
            }
        }
        return examples.get(condition, {}).get(lang, examples[condition]["en"])

    # Construct messages for Ollama: System Instruction + Extra Info + Session History
    # --- SLIGHTLY REFINED SYSTEM INSTRUCTION ---
    system_instruction = (
        f"You are an AI assistant providing **ONLY concise, direct, and actionable agricultural advice** "
        f"to farmers in India. Your responses MUST adhere to these strict rules: "
        f"1.  **Language:** Respond **ENTIRELY in {language}.** NEVER mix languages or provide translations. "
        f"    If the user asks in a different language than {language}, translate it internally and respond ENTIRELY in {language}."
        f"2.  **Length:** Keep responses to a **maximum of 3 sentences**. Be as brief and direct as possible. "
        f"    Ensure the advice is easy to understand and complete within the length constraint. "
        f"    Do NOT add extra greetings, intros, or outros. Get straight to the point."
        f"3.  **Content:** ONLY discuss agriculture, farming, crops, weather impacting farming, or market prices. "
        f"    **ABSOLUTELY NO philosophical, religious, personal opinions, or irrelevant remarks.** "
        f"    If the question is not about farming, respond briefly: '{get_refusal_message(language)}'" # LLM will use this
        f"4.  **Actionable Advice:** Use any provided 'WEATHER_INFO' or 'MARKET_INFO' to give practical farming advice directly related to the user's query."
        f"    **If 'MARKET_INFO' is present, prioritize answering the market query first and concisely.**"
        f"    **Always consider the previous conversation history to maintain context and continuity.**" # <--- ADDED EMPHASIS
        f"    **Example Weather Advice (translate to {language} internally, keep it ultra-short):**\n"
        f"    - **Sunny/Clear:** {get_weather_example(language, 'Sunny/Clear')}\n"
        f"    - **Rainy/Drizzle:** {get_weather_example(language, 'Rainy/Drizzle')}\n"
        f"    - **Hot:** {get_weather_example(language, 'Hot')}\n"
        f"    - **Cold:** {get_weather_example(language, 'Cold')}\n"
        f"Focus ONLY on the current query and relevant past context. Do not add preamble or postamble. Be very brief."
    )

    messages_for_ollama = []
    messages_for_ollama.append({"role": "system", "content": system_instruction})
    messages_for_ollama.extend(extra_info_messages)
    messages_for_ollama.extend(session_histories[session_id]) # THIS IS WHERE THE HISTORY IS ADDED

    # Log the full messages payload about to be sent to Ollama
    logger.debug(f"Full payload sent to Ollama for session {session_id}:\n{json.dumps(messages_for_ollama, indent=2)}")

    model_payload = {
        "model": OLLAMA_MODEL,
        "messages": messages_for_ollama,
        "temperature": 0.5,
        "top_k": 40,
        "top_p": 0.9,
        "stream": True
    }

    ai_response = "AI: Error: Could not get a response from the AI model."
    try:
        ollama_url = f"{OLLAMA_BASE_URL}/api/chat"
        logger.info(f"Attempting to call Ollama at {ollama_url} with model {OLLAMA_MODEL} for session {session_id}.")

        full_response_content = []
        with requests.post(ollama_url, json=model_payload, stream=True, timeout=180) as model_resp:
            model_resp.raise_for_status()

            for line in model_resp.iter_lines():
                if line:
                    try:
                        json_data = json.loads(line.decode('utf-8'))

                        if "message" in json_data and "content" in json_data["message"]:
                            full_response_content.append(json_data["message"]["content"])

                        if json_data.get("done"):
                            logger.info(f"Ollama stream finished for session {session_id}.")
                            break

                    except json.JSONDecodeError as e:
                        logger.error(f"JSON decode error in stream for session {session_id}: {e}. Problematic line: {line.decode('utf-8')}")
                        ai_response = f"AI: Error processing stream: Invalid JSON from Ollama. {e}"
                        break
                    except Exception as e:
                        logger.error(f"Unexpected error processing stream for session {session_id}: {e}", exc_info=True)
                        ai_response = f"AI: Unexpected error in stream: {e}"
                        break

        ai_response = "".join(full_response_content).strip()
        if not ai_response:
            ai_response = "AI: Received an empty or unparseable response from Ollama."
        logger.info(f"Final assembled Ollama response for session {session_id}: {ai_response[:200]}...")

    except requests.exceptions.Timeout:
        logger.error(f"Ollama API call timed out after 180 seconds for session {session_id}. "
                     f"This usually means the model is taking too long to generate a response.")
        ai_response = "AI: मैं सोचने में थोड़ा समय ले रहा हूँ। शायद प्रश्न बड़ा है या सिस्टम संसाधन कम हैं। कृपया पुनः प्रयास करें।"
    except requests.exceptions.ConnectionError as e:
        logger.critical(f"Ollama सर्वर से कनेक्ट नहीं हो सका ({OLLAMA_BASE_URL}) for session {session_id}. कृपया जांचें कि Ollama चल रहा है या नहीं। त्रुटि: {e}")
        ai_response = "AI: मैं अपनी सेवाओं से कनेक्ट नहीं हो पा रहा हूँ। कृपया सुनिश्चित करें कि Ollama सर्वर चल रहा है।"
    except requests.exceptions.RequestException as e:
        error_details = f"HTTP Status: {getattr(e.response, 'status_code', 'N/A')}, Response: {getattr(e.response, 'text', 'N/A')}" if e.response else str(e)
        logger.error(f"Ollama API call failed for session {session_id}. RequestException: {error_details}")
        ai_response = f"AI: मेरी प्रतिक्रिया प्राप्त करने में त्रुटि हुई। विवरण: {error_details[:100]}..."
    except Exception as e:
        logger.critical(f"Ollama कॉल के दौरान एक अप्रत्याशित त्रुटि हुई for session {session_id}: {e}", exc_info=True)
        ai_response = f"AI: एक महत्वपूर्ण अप्रत्याशित त्रुटि हुई: {str(e)[:100]}..."

    # Store the AI's response in history (for future turns)
    session_histories[session_id].append({"role": "assistant", "content": ai_response})
    logger.info(f"Appended AI response to history for session {session_id}. New history length: {len(session_histories[session_id])}")

    return jsonify({
        "session_id": session_id,
        "response": ai_response
    })

if __name__ == '__main__':
    logger.info("Starting Flask backend server...")
    app.run(host='0.0.0.0', port=5001, debug=True)