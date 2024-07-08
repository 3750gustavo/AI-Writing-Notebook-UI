import asyncio,threading
import json,re
import pygame

from novelai_python import VoiceGenerate, JwtCredential, APIError
from novelai_python.sdk.ai.generate_voice import VoiceSpeakerV2, VoiceSpeakerV1
from novelai_python.utils.useful import enum_to_list
from pydantic import SecretStr

# Initialize Pygame mixer
pygame.mixer.init()

# Global flag to control audio playback
audio_playback_active = threading.Event()

# Load the JWT token from config.json
with open("config.json", "r") as f:
    config = json.load(f)
    jwt = config.get("NOVELAI_API_KEY")

async def generate_voice_async(text: str):
    credential = JwtCredential(jwt_token=SecretStr(jwt))
    try:
        voice_gen = VoiceGenerate.build(
            text=text,
            voice_engine=VoiceSpeakerV1.Crina,
        )
        result = await voice_gen.request(
            session=credential
        )
    except APIError as e:
        print(f"Error: {e.message}")
        return None
    else:
        file = result.audio
        with open("generate_voice.mp3", "wb") as f:
            f.write(file)
    return "generate_voice.mp3"

def treat_text(text: str) -> str:
    """
    Removes all asterisks ('*') from the input text.
    """
    treated_text = re.sub(r'\*', '', text)
    return treated_text

def split_text(text: str, max_length: int = 1000) -> list:
    """
    Splits the text into chunks of a specified maximum length.
    """
    return [text[i:i + max_length] for i in range(0, len(text), max_length)]

async def generate_and_play_voice(text: str):
    chunks = split_text(treat_text(text))
    for chunk in chunks:
        if not audio_playback_active.is_set():
            break
        audio_file = await generate_voice_async(chunk)
        if audio_file:
            sound = pygame.mixer.Sound(audio_file)
            sound.play()
            while pygame.mixer.get_busy() and audio_playback_active.is_set():
                await asyncio.sleep(0.1)
            sound.stop()

def generate_voice(text: str):
    audio_playback_active.set()  # Set the flag when playback starts
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(generate_and_play_voice(text))

def stop_audio():
    audio_playback_active.clear()

# This part is only executed when the script is run directly
if __name__ == "__main__":
    generate_voice("Sweetheart...")