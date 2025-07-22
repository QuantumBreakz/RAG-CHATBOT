import requests
import os
import tempfile

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "dimavz/whisper-tiny")

def transcribe_audio_with_ollama(audio_bytes: bytes, audio_format: str = "wav") -> str:
    """
    Transcribe audio using the local Ollama Whisper model.
    audio_bytes: The audio file content as bytes.
    audio_format: The format of the audio file (e.g., 'wav', 'mp3', 'ogg').
    Returns the transcribed text.
    """
    # Save audio to a temporary file
    with tempfile.NamedTemporaryFile(suffix=f'.{audio_format}', delete=False) as tmp_audio:
        tmp_audio.write(audio_bytes)
        tmp_audio.flush()
        tmp_audio_path = tmp_audio.name
    try:
        # Ollama Whisper expects a file path for transcription
        # Use the Ollama API to transcribe
        # (Assume Ollama exposes a /api/generate or /api/transcribe endpoint for Whisper)
        # If not, you may need to use subprocess to call ollama CLI
        # Here, we use subprocess for maximum offline compatibility
        import subprocess
        result = subprocess.run([
            "ollama", "run", WHISPER_MODEL, tmp_audio_path
        ], capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Ollama Whisper failed: {result.stderr}")
        return result.stdout.strip()
    finally:
        os.unlink(tmp_audio_path) 