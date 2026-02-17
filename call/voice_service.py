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
            "model": "llama-3.1-8b-instant",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 150
        }
        
        try:
            response = requests.post(self.GROQ_API_URL, headers=headers, json=data)
            if response.status_code != 200:
                print(f"ERROR: Groq API returned {response.status_code}: {response.text}")
                return f"Error generating text: {response.status_code} - {response.text}"
            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            return f"Error generating text: {str(e)}"

    def create_user_voice(self, user_name, audio_files):
        """Create an Instant Voice Clone on ElevenLabs."""
        if not self.elevenlabs_key:
            print("ERROR: ELEVENLABS_API_KEY is missing from environment variables.")
            return None, "Error: ELEVENLABS_API_KEY not found."
            
        url = f"{self.ELEVENLABS_API_URL}/voices/add"
        headers = {"xi-api-key": self.elevenlabs_key}
        
        # files is a list of (name, (filename, file_handle, content_type))
        # This format ensures ElevenLabs gets the correct metadata for each sample
        # We use None for content_type to let the API or requests guess it
        import os
        files = [
            ('files', (os.path.basename(getattr(f, 'name', f'sample_{i}.m4a')), f, None))
            for i, f in enumerate(audio_files)
        ]
        
        data = {
            'name': f"User_{user_name}",
            'description': f"Cloned voice for {user_name}"
        }
        
        try:
            print(f"DEBUG: Sending {len(files)} samples to ElevenLabs for user {user_name}")
            response = requests.post(url, headers=headers, data=data, files=files)
            
            if response.status_code != 200:
                print(f"ERROR: ElevenLabs API returned {response.status_code}")
                error_detail = response.text
                try:
                    error_json = response.json()
                    error_detail = error_json.get('detail', {}).get('message', response.text)
                except:
                    pass
                print(f"DEBUG: Error detail: {error_detail}")
                return None, f"ElevenLabs Error: {error_detail}"
                
            voice_id = response.json().get('voice_id')
            print(f"DEBUG: Voice created successfully. ID: {voice_id}")
            return voice_id, None
        except Exception as e:
            error_msg = f"Exception during voice creation: {str(e)}"
            print(f"CRITICAL: {error_msg}")
            return None, error_msg

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
            if response.status_code != 200:
                error_detail = response.text
                try:
                    error_detail = response.json().get('detail', {}).get('message', response.text)
                except:
                    pass
                return None, f"ElevenLabs TTS Error: {error_detail}"
            
            return response.content, None
        except Exception as e:
            return None, f"Exception during speech synthesis: {str(e)}"

class SiliconFlowManager:
    """Handles interactions with SiliconFlow (CosyVoice) for free-tier cloning."""
    
    API_URL = "https://api.siliconflow.cn/v1"
    
    def __init__(self):
        self.api_key = os.environ.get('SILICONFLOW_API_KEY')

    def zero_shot_tts(self, text, reference_audio_url):
        """
        Synthesize speech using CosyVoice Zero-Shot cloning.
        reference_audio_url: Cloudinary URL of a recorded sample.
        """
        if not self.api_key:
            return None, "Error: SILICONFLOW_API_KEY not found."

        url = f"{self.API_URL}/audio/speech"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "FunAudioLLM/CosyVoice2-0.5B",
            "input": text,
            "voice": reference_audio_url, # SiliconFlow dynamic voice support
            "response_format": "mp3"
        }
        
        try:
            print(f"DEBUG: Requesting SiliconFlow Zero-Shot TTS for voice: {reference_audio_url}")
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code != 200:
                error_msg = f"SiliconFlow API returned {response.status_code}: {response.text}"
                print(f"ERROR: {error_msg}")
                return None, error_msg
                
            return response.content, None
        except Exception as e:
            error_msg = f"Exception during SiliconFlow TTS: {str(e)}"
            print(f"CRITICAL: {error_msg}")
            return None, error_msg

