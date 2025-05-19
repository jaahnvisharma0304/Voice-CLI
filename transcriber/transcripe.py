#!/usr/bin/env python3
import sounddevice as sd
import numpy as np
import vosk
import json
import time
import queue
import sys
import os

def transcribe_audio():
    print("transcription called")
    """
    Records audio from the microphone and transcribes it using Vosk.
    Returns only the transcribed text without any prefix.
    """
    # Audio Configuration
    SAMPLE_RATE = 16000
    CHANNELS = 1
    DTYPE = 'int16'
    BLOCK_SIZE = 8000  # Process audio in chunks
    RECORDING_TIMEOUT = 10  # Maximum recording time in seconds
    MIN_SILENCE_DURATION = 2.0  # Duration of silence to detect end of speech

    # Check if Vosk model exists
    model_path = os.path.abspath("../os projecy/vosk-model-small-en-in-0.4")
    if not os.path.exists(model_path):
        print(f"Error: Vosk model not found at {model_path}")
        print("Please download the model from https://alphacephei.com/vosk/models")
        return ""

    # Load Vosk Model
    try:
        model = vosk.Model(model_path)
        recognizer = vosk.KaldiRecognizer(model, SAMPLE_RATE)
    except Exception as e:
        print(f"Error loading Vosk model: {str(e)}")
        return ""

    # Create a queue to store audio data
    q = queue.Queue()
    
    # Track silence for auto-stop
    last_speech_time = time.time()
    recording_start_time = time.time()
    has_speech = False

    # Callback function to process audio data
    def audio_callback(indata, frames, time_info, status):
        if status:
            print(f"Status: {status}")
        q.put(bytes(indata))

    try:
        # Get default device info
        device_info = sd.query_devices(kind='input')
        print(f"Using device: {device_info['name']}")
        print("Recording... Speak now (will auto-stop after silence or press Ctrl+C to stop)")
        
        # Start recording
        with sd.RawInputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype=DTYPE, callback=audio_callback):
            print("Listening...")
            
            while True:
                # Check if we've reached the maximum recording time
                if time.time() - recording_start_time > RECORDING_TIMEOUT:
                    print("\nMaximum recording time reached.")
                    break
                
                # Check if there's been silence after speech
                current_time = time.time()
                if has_speech and (current_time - last_speech_time > MIN_SILENCE_DURATION):
                    print("\nDetected end of speech. Processing...")
                    break
                
                # Process audio data
                if not q.empty():
                    data = q.get()
                    if recognizer.AcceptWaveform(data):
                        result_json = recognizer.Result()
                        result_dict = json.loads(result_json)
                        text = result_dict.get("text", "")
                        if text:
                            print(f"Recognized: {text}")
                            has_speech = True
                            last_speech_time = current_time
                    else:
                        # Check partial results for speech activity
                        partial = json.loads(recognizer.PartialResult())
                        if partial.get("partial", ""):
                            has_speech = True
                            last_speech_time = current_time
                else:
                    # Short sleep to prevent CPU hogging
                    time.sleep(0.01)
            
            # Get final result
            final_result = json.loads(recognizer.FinalResult())
            transcribed_text = final_result.get("text", "")
            
            if not transcribed_text:
                print("No speech detected.")
                return ""
            
            print(f"Final transcription: {transcribed_text}")
            return transcribed_text  # Return only the text without prefix

    except KeyboardInterrupt:
        print("\nRecording stopped by user.")
        # Get what we have so far
        final_result = json.loads(recognizer.FinalResult())
        return final_result.get("text", "")
    except Exception as e:
        print(f"Error during recording: {str(e)}")
        print("Please check if your microphone is properly connected and enabled.")
        return ""



