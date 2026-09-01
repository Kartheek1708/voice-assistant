from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import speech_recognition as sr
from pydub import AudioSegment
import google.generativeai as genai
import edge_tts
import os
import re
from dotenv import load_dotenv
from fastapi.staticfiles import StaticFiles
from uuid import uuid4


load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500", "http://localhost:5500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def transcribe_audio(file_path: Path) -> str:
    wav_path = Path("data") / "converted.wav"
    sound = AudioSegment.from_file(file_path)
    sound.export(wav_path, format="wav")

    recognizer = sr.Recognizer()
    with sr.AudioFile(str(wav_path)) as source:
        audio_data = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio_data)
        except sr.UnknownValueError:
            text = "Sorry, could not understand the audio. Please speak clearly."
        except sr.RequestError:
            text = "Speech recognition service error. Check internet connection."

    wav_path.unlink(missing_ok=True)
    return text


def answer_from_text(user_text: str) -> str:
    """Text ni Gemini AI ki pampi answer techukovadam (LLM)"""
    model = genai.GenerativeModel("gemini-2.5-flash")
    try:
        response = model.generate_content(user_text)
        text = response.text.strip()
    except Exception as e:
        if "429" in str(e) or "quota" in str(e).lower():
            text = "Sorry, too many requests right now. Please wait a minute and try again."
        else:
            text = "Sorry, something went wrong. Please try again."    
    
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  
    text = re.sub(r'\*(.*?)\*', r'\1', text)       
    text = re.sub(r'#+\s*', '', text)               
    return text

async def generate_speech(text: str) -> Path:
    """ Text will be convert into Audio By using edge_tts """
    output_path  = Path("data") / f"response_{uuid4().hex}.mp3"
    communicate = edge_tts.Communicate(text, voice="en-US-AriaNeural")
    await communicate.save(str(output_path))
    return output_path 


@app.post("/api/transcribe")
async def transcribe(audio: UploadFile = File(...)):
    suffix = Path(audio.filename).suffix
    temp = Path("data") / f"input{suffix}"

    try:
        temp.write_bytes(await audio.read())
        transcript = transcribe_audio(temp)
        return {"transcript": transcript}
    finally:
        temp.unlink(missing_ok=True)


@app.post("/api/voice")
async def voice_pipeline(audio: UploadFile = File(...)):
    suffix = Path(audio.filename).suffix
    temp = Path("data") / f"input{suffix}"

    try:
        temp.write_bytes(await audio.read())
        transcript = transcribe_audio(temp)
        answer = answer_from_text(transcript)
        output = await generate_speech(answer)
        return {
            "transcript": transcript,
            "answer": answer,
            "audio_url": f"/api/audio/{output.name}"
        }
    finally:
        temp.unlink(missing_ok=True)


@app.get("/api/audio/{filename}")
async def get_audio(filename: str):
    file_path = Path("data") / filename
    return FileResponse(file_path, media_type="audio/mpeg")


app.mount("/", StaticFiles(directory="static", html=True), name="static")