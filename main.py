from dotenv import load_dotenv
from typing import Callable
import os
import openai

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def get_wav_file(file_ogg: str) -> str:
  from pydub import AudioSegment
  file_wav = file_ogg.replace('.ogg','.wav')
  x = AudioSegment.from_file(file_ogg)
  x.export(file_wav, format='wav')
  return file_wav

def recognize(file_wav: str) -> str:
  return openai.Audio.transcribe("whisper-1", open(file_wav, 'rb'), response_format= 'text')

def sanitize(text: str) -> str:
  completion = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
      {'role': 'system',  'content': 'Remove parasite words from next message, do not change other words. Answer me just with santizied text.'},
      {'role': 'user', 'content': text},
    ]
  )
  return completion.choices[0].message.content

async def handle(file_ogg: str, log: Callable[[str], None]) -> str:
  try:
    await log("Downloading and converting...")
    file_wav = get_wav_file(file_ogg)

    await log("Text recognizing...")
    text = recognize(file_wav)

    await log("Text sanitizing...")
    sanitized = sanitize(text)

    return sanitized
  finally:
    os.remove(file_wav)

def start_bot():
  from pyrogram import Client, filters
  from pyrogram.handlers import MessageHandler

  async def handle_voice(client, message):
    try:
      file_ogg = await client.download_media(message.voice)
      response = await message.reply("...")
      async def log(message: str):
        await response.edit_text("__" + message + "__")
      await response.edit_text(await handle(file_ogg, log))
    finally:
      os.remove(file_ogg)

  app = Client("text", os.getenv("TELEGRAM_API_ID"), os.getenv("TELEGRAM_API_HASH"))
  app.add_handler(MessageHandler(handle_voice, filters.voice))
  app.run()

start_bot()
