import os
import requests
from django.conf import settings

    
class OllamaManager:
    """Handles interactions with a local Ollama instance."""
    
    def __init__(self):
        self.base_url = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')
        self.model = os.environ.get('OLLAMA_MODEL', 'phi3')

    def generate_response(self, prompt, system_prompt=None):
        """Generate text response using Ollama."""
        url = f"{self.base_url}/api/chat"
        
        if not system_prompt:
            system_prompt = (
                "You are the user's digital twin. You should respond in a way that sounds like the user reflecting on themselves. "
                "Keep responses concise and empathetic."
            )
            
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 150
            }
        }
        
        try:
            print(f"DEBUG: [Ollama] Requesting response from {url} using {self.model}", flush=True)
            response = requests.post(url, json=data, timeout=120)
            
            if response.status_code != 200:
                print(f"ERROR: Ollama API Error {response.status_code}: {response.text}", flush=True)
                return f"Error: Ollama failed with status {response.status_code}"
                
            result = response.json()
            return result['message']['content']
        except Exception as e:
            print(f"CRITICAL: Exception during Ollama generation: {str(e)}", flush=True)
            return f"Error: {str(e)}"

class CoquiXTTSManager:
    """Handles interactions with a local Coqui XTTS API server."""
    
    def __init__(self):
        self.base_url = os.environ.get('XTTS_BASE_URL', 'http://localhost:8020')

    def synthesize(self, text, reference_audio_content):
        """
        Synthesize speech using zero-shot cloning on XTTS.
        reference_audio_content: Binary content of the user's voice sample.
        """
        url = f"{self.base_url}/tts_to_audio"
        
        # Format for xtts-api-server (common community implementation)
        files = {
            'speaker_wav': ('reference.wav', reference_audio_content, 'audio/wav')
        }
        data = {
            'text': text,
            'language': 'en'
        }
        
        try:
            print(f"DEBUG: [XTTS] Sending synthesis request to {url}", flush=True)
            # Synthesis on CPU takes time, increase timeout
            response = requests.post(url, data=data, files=files, timeout=120)
            
            if response.status_code != 200:
                error_body = response.text
                print(f"ERROR: XTTS API Error {response.status_code}: {error_body}", flush=True)
                return None, f"XTTS failed with status {response.status_code}: {error_body[:100]}"
            
            return response.content, None
        except Exception as e:
            print(f"CRITICAL: Exception during XTTS synthesis: {str(e)}", flush=True)
            return None, str(e)

class VoiceAIManager:
    """Handles interactions with Groq, Ollama, and ElevenLabs."""
    
    GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
    ELEVENLABS_API_URL = "https://api.elevenlabs.io/v1"
    
    def __init__(self):
        self.groq_key = os.environ.get('GROQ_API_KEY')
        self.elevenlabs_key = os.environ.get('ELEVENLABS_API_KEY')
        self.ai_mode = os.environ.get('AI_MODE', 'cloud') # 'cloud' or 'local'

    def generate_response(self, prompt, context=""):
        """Generate text response using the configured engine."""
        if self.ai_mode == 'local' or not self.groq_key:
            return OllamaManager().generate_response(prompt)
            
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
            print(f"DEBUG: [Groq] Requesting response for prompt: {prompt[:50]}...", flush=True)
            response = requests.post(self.GROQ_API_URL, headers=headers, json=data)
            
            if response.status_code != 200:
                error_msg = f"Groq API Error {response.status_code}: {response.text}"
                print(f"ERROR: {error_msg}", flush=True)
                # Fallback to local if cloud fails
                return OllamaManager().generate_response(prompt)
                
            result = response.json()
            content = result['choices'][0]['message']['content']
            print(f"DEBUG: [Groq] Generated response successfully: {content[:50]}...", flush=True)
            return content
        except Exception as e:
            print(f"CRITICAL: Exception during Groq generation: {str(e)}", flush=True)
            return OllamaManager().generate_response(prompt)

    def create_user_voice(self, user_name, audio_files):
        """Create an Instant Voice Clone on ElevenLabs."""
        if not self.elevenlabs_key:
            print("ERROR: ELEVENLABS_API_KEY is missing from environment variables.")
            return None, "Error: ELEVENLABS_API_KEY not found."
            
        url = f"{self.ELEVENLABS_API_URL}/voices/add"
        headers = {"xi-api-key": self.elevenlabs_key}
        
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
                return None, f"ElevenLabs Error: {error_detail}"
                
            voice_id = response.json().get('voice_id')
            return voice_id, None
        except Exception as e:
            return None, str(e)

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
                return None, f"ElevenLabs TTS Error: {response.text}"
            
            return response.content, None
        except Exception as e:
            return None, str(e)

class SiliconFlowManager:
    """Handles interactions with SiliconFlow (CosyVoice) for free-tier cloning."""
    
    API_URL = "https://api.siliconflow.com/v1"
    
    def __init__(self):
        self.api_key = os.environ.get('SILICONFLOW_API_KEY')
        if isinstance(self.api_key, str):
            self.api_key = self.api_key.strip().strip('"').strip("'").strip()
        else:
            self.api_key = None

    def upload_voice(self, audio_content, custom_name, transcription_text):
        if not self.api_key:
            return None, "Error: SILICONFLOW_API_KEY not found."

        url = f"{self.API_URL}/uploads/audio/voice"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        files = {"file": (f"{custom_name}.mp3", audio_content, "audio/mpeg")}
        data = {
            "model": "FunAudioLLM/CosyVoice2-0.5B",
            "customName": custom_name,
            "text": transcription_text
        }
        
        try:
            response = requests.post(url, headers=headers, data=data, files=files)
            if response.status_code != 200:
                return None, response.text
                
            uri = response.json().get("uri")
            return uri, None
        except Exception as e:
            return None, str(e)

    def zero_shot_tts(self, text, voice_identifier):
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
            "voice": voice_identifier,
            "response_format": "mp3"
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            if response.status_code != 200:
                return None, response.text
            return response.content, None
        except Exception as e:
            return None, str(e)

