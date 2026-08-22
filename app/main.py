from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import speech_recognition as sr
from pydub import AudioSegment
import google.generativeai as genai
from gtts import gTTS
import os
import re
from dotenv import load_dotenv
from fastapi.staticfiles import StaticFiles


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
    response = model.generate_content(user_text)
    text = response.text.strip()
    
    
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  
    text = re.sub(r'\*(.*?)\*', r'\1', text)       
    text = re.sub(r'#+\s*', '', text)               
    
    return text

def generate_speech(text: str) -> Path:
    """Text ni audio ga convert cheyadam (TTS)"""
    output_path = Path("data") / "output.mp3"
    tts = gTTS(text=text, lang="en")
    tts.save(str(output_path))
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
        output = generate_speech(answer)
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