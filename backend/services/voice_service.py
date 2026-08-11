import os
import io
import base64
import httpx
from loguru import logger

# Try to get API key from env
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

async def transcribe_audio(base64_audio: str) -> str:
    """
    Transcribe a base64 encoded audio string using Groq Whisper API.
    Since Groq is very fast and free, it's perfect for this.
    Returns the transcribed text in Hindi/Hinglish/English.
    """
    if not GROQ_API_KEY:
        logger.warning("GROQ_API_KEY not found in environment. Returning fallback transcription.")
        # Fallback to returning a static string or throw error if needed
        return "Voice message received. (Groq API key missing for transcription)"
    
    try:
        # Decode base64 to raw bytes
        audio_bytes = base64.b64decode(base64_audio)
        
        # Prepare the multipart payload
        files = {
            'file': ('audio.ogg', audio_bytes, 'audio/ogg')
        }
        data = {
            'model': 'whisper-large-v3',
            'prompt': 'Translate and transcribe the audio into Hindi or English or Hinglish text accurately.',
            'response_format': 'json'
        }
        
        headers = {
            'Authorization': f'Bearer {GROQ_API_KEY}'
        }
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                headers=headers,
                data=data,
                files=files
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('text', '')
            else:
                logger.error(f"Groq Whisper API error {response.status_code}: {response.text}")
                return "Maaf kijiye, main aapki aawaz samajh nahi paya. Kripya type karke bataiye."
                
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        return "Maaf kijiye, main aapki aawaz samajh nahi paya. Kripya type karke bataiye."
