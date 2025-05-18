import sounddevice as sd
import numpy as np
import vosk
import json
import time
import queue
import sys
from pipe import pipe

@pipe
def transcribe_audio():
# Audio Configuration
    SAMPLE_RATE = 16000
    CHANNELS = 1
    DTYPE = 'int16'
    BLOCK_SIZE = 8000  # Process audio in chunks

    # Load Vosk Model
    model = vosk.Model(r"./vosk-model-small-en-in-0.4")
    recognizer = vosk.KaldiRecognizer(model, SAMPLE_RATE)

    # Create a queue to store audio data
    q = queue.Queue()

    # Callback function to process audio data
    def audio_callback(indata, frames, time, status):
        if status:
            print(status)
        q.put(bytes(indata))

    try:
        # Get default device info
        device_info = sd.query_devices(kind='input')
        print(f"Using device: {device_info['name']}")
        print("Recording... Press Ctrl+C to stop")

        # Start recording
        with sd.RawInputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype=DTYPE, callback=audio_callback):
            while True:
                data = q.get()
                if recognizer.AcceptWaveform(data):
                    result = recognizer.Result()
                    text = json.loads(result).get("text", "")
                    if text:
                        return(f"Transcription: {text}")

    except KeyboardInterrupt:
        print("\nRecording stopped.")
    except Exception as e:
        print(f"Error: {str(e)}")
        print("Please check if your microphone is properly connected and enabled.")
