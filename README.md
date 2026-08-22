# 🎙️ Voice Assistant

A full-stack AI voice assistant built with Python, FastAPI, and free APIs.

## Features
- **Speech-to-Text (STT):** Converts voice input to text using Google Speech Recognition
- **AI Reasoning (LLM):** Generates intelligent responses using Google Gemini
- **Text-to-Speech (TTS):** Converts AI responses back to natural voice using gTTS
- **Web Interface:** Simple browser-based UI to record and interact with the assistant

## Tech Stack
- **Backend:** FastAPI, Python
- **STT:** SpeechRecognition (Google)
- **LLM:** Google Gemini API
- **TTS:** gTTS (Google Text-to-Speech)
- **Frontend:** HTML, CSS, JavaScript

## How It Works
1. User records voice in the browser
2. Audio is sent to the backend and transcribed to text
3. Transcript is sent to Gemini AI for a response
4. Response is converted to speech and played back

## Setup
1. Clone the repo
2. Create a virtual environment and install dependencies
3. Add your Gemini API key to a `.env` file
4. Run `uvicorn app.main:app --reload`
5. Open `http://127.0.0.1:8000/`