import os
import requests
from django.conf import settings

class VoiceAIManager:
    """Handles interactions with Groq (Llama 3) and ElevenLabs."""
    
    GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
    ELEVENLABS_API_URL = "https://api.elevenlabs.io/v1"
    
    def __init__(self):
        self.groq_key = os.environ.get('GROQ_API_KEY')
        self.elevenlabs_key = os.environ.get('ELEVENLABS_API_KEY')

    def generate_response(self, prompt, context=""):
        """Generate text response using Llama 3 via Groq."""
        if not self.groq_key:
            return "Error: GROQ_API_KEY not found."
            
        headers = {
            "Authorization": f"Bearer {self.groq_key}",
            "Content-Type": "application/json"
        }
        
        system_prompt = (
            "You are the user's digital twin. You should respond in a way that sounds like the user reflecting on themselves. "
            "Keep responses concise and empathetic."
        )
        
        data = {
            "model": "llama3-70b-8192",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 150
        }
        
        try:
            response = requests.post(self.GROQ_API_URL, headers=headers, json=data)
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            return f"Error generating text: {str(e)}"

    def create_user_voice(self, user_name, audio_files):
        """Create an Instant Voice Clone on ElevenLabs."""
        if not self.elevenlabs_key:
            return None, "Error: ELEVENLABS_API_KEY not found."
            
        url = f"{self.ELEVENLABS_API_URL}/voices/add"
        headers = {"xi-api-key": self.elevenlabs_key}
        
        # files is a list of (name, file_handle)
        files = [('files', f) for f in audio_files]
        
        data = {
            'name': f"User_{user_name}",
            'description': f"Cloned voice for {user_name}"
        }
        
        try:
            response = requests.post(url, headers=headers, data=data, files=files)
            response.raise_for_status()
            return response.json()['voice_id'], None
        except Exception as e:
            return None, f"Error creating voice: {str(e)}"

    def text_to_speech(self, text, voice_id):
        """Synthesize speech using ElevenLabs."""
        if not self.elevenlabs_key:
            return None, "Error: ELEVENLABS_API_KEY not found."
            
        url = f"{self.ELEVENLABS_API_URL}/text-to-speech/{voice_id}"
        headers = {
            "xi-api-key": self.elevenlabs_key,
            "Content-Type": "application/json"
        }
        
        data = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            # In a real app, you'd save this to storage and return URL
            # For simplicity, we'll assume the view handles saving the content
            return response.content, None
        except Exception as e:
            return None, f"Error synthesizing speech: {str(e)}"
