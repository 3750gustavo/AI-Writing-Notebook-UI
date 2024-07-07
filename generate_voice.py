import asyncio
import json
import pygame
import re
import threading

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
    print(f"VoiceSpeakerV2 List:{enum_to_list(VoiceSpeakerV2)}")
    try:
        voice_gen = VoiceGenerate.build(
            text=text,
            voice_engine=VoiceSpeakerV1.Crina,  # VoiceSpeakerV2.Ligeia,
        )
        result = await voice_gen.request(
            session=credential
        )
    except APIError as e:
        print(f"Error: {e.message}")
        return None
    else:
        print(f"Meta: {result.meta}")
    file = result.audio
    with open("generate_voice.mp3", "wb") as f:
        f.write(file)
    print("Voice generated successfully")


def treat_text(text: str) -> str:
    """
    Removes all asterisks ('*') from the input text.
    """
    treated_text = re.sub(r'\*', '', text)
    return treated_text


async def generate_and_play_voice(text: str):
    await generate_voice_async(text)
    sound = pygame.mixer.Sound("generate_voice.mp3")
    audio_playback_active.set()  # Set the flag when playback starts
    sound.play()
    while pygame.mixer.get_busy() and audio_playback_active.is_set():
        await asyncio.sleep(0.1)
    sound.stop()  # Stop the sound if the loop breaks
    audio_playback_active.clear()  # Clear the flag when playback ends


def generate_voice(text: str):
    treated_text = treat_text(text)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(generate_and_play_voice(treated_text))


def stop_audio():
    audio_playback_active.clear()


# This part is only executed when the script is run directly
if __name__ == "__main__":
    generate_voice("Sweetheart... did you make a mess again?")
