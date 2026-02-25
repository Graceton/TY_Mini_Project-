import argparse
import requests
import base64
import os
from typing import List, Dict, Any


class MultilingualChatbot:
    def __init__(self, api_key: str):
        self.api_key = "sk_abg9n10d_IDjWXi9iDwAMYhS65sWOBWpO"
        self.base_url = "https://api.sarvam.ai/v1/chat/completions"
        self.translate_url = "https://api.sarvam.ai/translate/text"
        self.stt_url = "https://api.sarvam.ai/speech-to-text"  
        self.tts_url = "https://api.sarvam.ai/text-to-speech"  
        
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        self.conversation_history: List[Dict[str, str]] = []
        self.max_history = 5

        # Language mapping for TTS codes
        self.lang_code_map = {
            "english": "en-IN",
            "hindi": "hi-IN",
            "tamil": "ta-IN",
            "telugu": "te-IN",
            "kannada": "kn-IN",
            "malayalam": "ml-IN"
        }

        # Common error messages in different languages
        self.error_messages = {
            "english": "I apologize, but I'm having trouble processing your request. Please try again.",
            "hindi": "मुझे खेद है, लेकिन मैं आपके अनुरोध को संसाधित करने में परेशानी का सामना कर रहा हूं। कृपया पुनः प्रयास करें।",
            "tamil": "மன்னிக்கவும், உங்கள் கோரிக்கையை செயலாக்குவதில் சிக்கல் ஏற்பட்டுள்ளது. மீண்டும் முயற்சிக்கவும்.",
            "telugu": "క్షమించండి, మీ అభ్యర్థనను ప్రాసెస్ చేయడంలో ఇబ్బంది ఎదురవుతోంది. దయచేసి మళ్లీ ప్రయత్నించండి.",
            "kannada": "ಕ್ಷಮಿಸಿ, ನಿಮ್ಮ ವಿನಂತಿಯನ್ನು ಸಂಸ್ಕರಿಸುವಲ್ಲಿ ತೊಂದರೆ ಎದುರಾಗುತ್ತಿದೆ. ದಯವಿಟ್ಟು ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.",
            "malayalam": "ക്ഷമിക്കണം, നിങ്ങളുടെ അഭ്യർത്ഥന സംസ്കരിക്കുന്നതിൽ പ്രശ്നം നേരിടുന്നു. ദയവായി വീണ്ടും ശ്രമിക്കുക.",
        }

    def detect_language(self, text: str) -> str:
        # Enhanced language detection based on character ranges
        devanagari_range = range(0x0900, 0x097F)  # Hindi
        tamil_range = range(0x0B80, 0x0BFF)  # Tamil
        telugu_range = range(0x0C00, 0x0C7F)  # Telugu
        kannada_range = range(0x0C80, 0x0CFF)  # Kannada
        malayalam_range = range(0x0D00, 0x0D7F)  # Malayalam

        for char in text:
            code = ord(char)
            if code in devanagari_range:
                return "hindi"
            elif code in tamil_range:
                return "tamil"
            elif code in telugu_range:
                return "telugu"
            elif code in kannada_range:
                return "kannada"
            elif code in malayalam_range:
                return "malayalam"

        return "english"

    def translate_text(self, text: str, target_lang: str) -> str:
        try:
            if (
                text in self.error_messages.values()
                and target_lang in self.error_messages
            ):
                return self.error_messages[target_lang]

            response = requests.post(
                self.translate_url,
                headers=self.headers,
                json={"text": text, "target_language": target_lang},
            )
            response.raise_for_status()
            return response.json()["translated_text"]
        except Exception as e:
            return self.error_messages.get(target_lang, self.error_messages["english"])

    # New Method: Speech to Text
    def transcribe_audio(self, file_path: str, language_code="hi-IN") -> str:
        headers = {
            "api-subscription-key": self.api_key,
        }
        try:
            with open(file_path, "rb") as f:
                files = {"file": (os.path.basename(file_path), f, "audio/wav")}
                data = {
                    "language_code": language_code,
                    "model": "saarika:v2.5",
                    "with_timestamps": "false"
                }
                response = requests.post(self.stt_url, headers=headers, files=files, data=data)
                response.raise_for_status()
                return response.json().get("transcript", "")
                
        except requests.exceptions.HTTPError as e:
            print(f"Error during transcription: {e}")
            print(f"API Error Details: {e.response.text}")  
            return None
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return None

    def text_to_speech(self, text: str, output_path: str, language_code="en-IN") -> bool:
        headers = {
            "api-subscription-key": self.api_key,
            "Content-Type": "application/json"
        }
        # Sarvam API has a 500 character limit per request. 
        # If the text is too long, we'll only synthesize the first part or chunk it.
        # For simplicity, we truncate it to 500 characters so it doesn't crash the whole UI.
        if len(text) > 490:
            text = text[:490] + "..."

        payload = {
            "inputs": [text],
            "target_language_code": language_code,
            "speaker": "shubh",
            "pace": 1.0,
            "temperature": 0.6,
            "model": "bulbul:v3"
        }
        try:
            response = requests.post(self.tts_url, json=payload, headers=headers)
            
            # Better error reporting
            if response.status_code != 200:
                print(f"TTS API Error Status: {response.status_code}")
                print(f"TTS API Error Body: {response.text}")
                
            response.raise_for_status()
            audio_data = response.json()
            if "audios" in audio_data:
                binary_audio = base64.b64decode(audio_data["audios"][0])
                with open(output_path, 'wb') as f:
                    f.write(binary_audio)
                return True
            return False
        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error during TTS: {e}")
            if e.response is not None:
                print(f"API Error Details: {e.response.text}")
            return False
        except Exception as e:
            print(f"Error during TTS: {e}")
            return False

    def get_chat_response(self, user_input: str) -> Dict[str, Any]:
        detected_lang = self.detect_language(user_input)
        self.conversation_history.append({"role": "user", "content": user_input})

        messages = [
            {
                "role": "system",
                "content": "You are a helpful multilingual voice assistant. Respond in the same language as the user's input. Keep your responses short and conversational, ideally under 3 sentences, as they will be spoken aloud.",
            }
        ]
        messages.extend(self.conversation_history[-self.max_history :])

        try:
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json={"model": "sarvam-m", "messages": messages, "temperature": 0.7},
            )
            response.raise_for_status()
            assistant_response = response.json()["choices"][0]["message"]["content"]
            self.conversation_history.append(
                {"role": "assistant", "content": assistant_response}
            )
            return {"response": assistant_response, "language": detected_lang}

        except requests.exceptions.RequestException as e:
            error_message = self.error_messages.get(
                detected_lang, self.error_messages["english"]
            )
            return {"response": error_message, "language": detected_lang}


def main():
    chatbot = MultilingualChatbot("sk_abg9n10d_IDjWXi9iDwAMYhS65sWOBWpO")

    print("Chatbot initialized. Type 'quit' to exit.")
    print("You can chat in English or regional language.")
    print("To use voice input, provide the path to a .wav file.")

    while True:
        user_input = input("\nYou (Text or .wav path): ").strip()

        if user_input.lower() == "quit":
            break

        if user_input.endswith(".wav") and os.path.exists(user_input):
            print(f"🎤 Reading audio file: {user_input}...")
            # Defaulting to Hindi model for mixed input capability as per example
            transcribed_text = chatbot.transcribe_audio(user_input)
            if transcribed_text:
                print(f"📝 Transcribed: {transcribed_text}")
                user_input = transcribed_text
            else:
                print("Transcription failed.")
                continue

        # Get Chat Response
        response = chatbot.get_chat_response(user_input)
        print(f"\nBot ({response['language']}): {response['response']}")

        # Generate Audio Output (TTS)
        output_file = "bot_reply.wav"
        lang_code = chatbot.lang_code_map.get(response['language'], "en-IN")
        
        print(f"🔊 Generating audio response in {lang_code}...")
        if chatbot.text_to_speech(response['response'], output_file, lang_code):
            print(f"Audio saved to: {output_file}")


if __name__ == "__main__":
    main()