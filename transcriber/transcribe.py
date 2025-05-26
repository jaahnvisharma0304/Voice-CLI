import sounddevice as sd
import numpy as np
import whisper
import time
import queue
import sys
import os
import wave
import threading
from pynput import keyboard

def transcribe_audio():
    """
    Records audio from the microphone and transcribes it using Whisper.
    Returns the full transcribed text and handles speech detection more robustly.
    """
    # Audio Configuration
    SAMPLE_RATE = 16000
    CHANNELS = 1
    DTYPE = 'int16'
    BLOCK_SIZE = 8000  # Process audio in chunks
    RECORDING_TIMEOUT = 15  # Maximum recording time in seconds
    MIN_SILENCE_DURATION = 2.5  # Duration of silence to detect end of speech
    SILENCE_THRESHOLD = 0.01  # Threshold to detect silence (adjust as needed)
    
    # Load Whisper Model
    try:
        print("Loading Whisper model...")
        model = whisper.load_model("small.en")
        print("Model loaded successfully!")
    except Exception as e:
        print(f"Error loading Whisper model: {str(e)}")
        return ""

    # Create a queue to store audio data
    q = queue.Queue()
    audio_data = []
    
    # Track silence for auto-stop
    last_speech_time = time.time()
    recording_start_time = time.time()
    has_speech = False
    silence_started = None
    manual_stop = False

    # Callback function to process audio data
    def audio_callback(indata, frames, time_info, status):
        if status:
            print(f"Status: {status}")
        q.put(indata.copy())

    # Keyboard listener for manual stop
    def on_press(key):
        nonlocal manual_stop
        try:
            if key.char == 's':  # Press 's' to stop
                manual_stop = True
                print("\nManual stop triggered...")
        except AttributeError:
            if key == keyboard.Key.space:  # Press spacebar to stop
                manual_stop = True
                print("\nManual stop triggered...")

    # Start keyboard listener
    listener = keyboard.Listener(on_press=on_press)
    listener.start()

    try:
        # Get default device info
        device_info = sd.query_devices(kind='input')
        print(f"Using device: {device_info['name']}")
        print("Recording... Speak now")
        print("Press SPACEBAR or 's' to stop recording manually")
        print("Or wait for auto-stop after silence, or press Ctrl+C to stop")
        
        # Start recording
        with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype=DTYPE, callback=audio_callback):
            print("Listening...")
            
            while True:
                # Check for manual stop
                if manual_stop:
                    print("Manual stop requested. Processing...")
                    break
                    
                # Check if we've reached the maximum recording time
                if time.time() - recording_start_time > RECORDING_TIMEOUT:
                    print("\nMaximum recording time reached.")
                    break
                
                # Process audio data
                if not q.empty():
                    data = q.get()
                    audio_data.append(data)
                    
                    # Simple voice activity detection based on volume
                    volume = np.sqrt(np.mean(data**2))
                    
                    if volume > SILENCE_THRESHOLD:
                        if not has_speech:
                            has_speech = True
                            print("Speech detected...")
                        last_speech_time = time.time()
                        silence_started = None
                    elif has_speech:
                        # Track silence after speech
                        current_time = time.time()
                        if silence_started is None:
                            silence_started = current_time
                        elif current_time - silence_started > MIN_SILENCE_DURATION:
                            print("\nDetected end of speech. Processing...")
                            break
                else:
                    # Short sleep to prevent CPU hogging
                    time.sleep(0.01)
            
            # Convert audio data to numpy array
            if audio_data:
                audio_array = np.concatenate(audio_data, axis=0)
                audio_float32 = audio_array.astype(np.float32) / 32768.0  # Convert to float32
                
                # Save temporary audio file for Whisper
                temp_filename = "temp_recording.wav"
                with wave.open(temp_filename, 'wb') as wf:
                    wf.setnchannels(CHANNELS)
                    wf.setsampwidth(2)  # 16-bit
                    wf.setframerate(SAMPLE_RATE)
                    wf.writeframes((audio_float32 * 32768).astype(np.int16).tobytes())
                
                print("Transcribing with Whisper...")
                
                # Transcribe with Whisper
                result = model.transcribe(temp_filename)
                transcribed_text = result["text"].strip()
                
                # Clean up temporary file
                os.remove(temp_filename)
                
                # Stop keyboard listener
                listener.stop()
                
                if not transcribed_text:
                    print("No speech detected.")
                    return ""
                
                print(f"Final transcription: {transcribed_text}")
                return transcribed_text
            else:
                print("No audio data recorded.")
                listener.stop()
                return ""

    except KeyboardInterrupt:
        print("\nRecording stopped by user.")
        # Process what we have so far
        if audio_data:
            audio_array = np.concatenate(audio_data, axis=0)
            audio_float32 = audio_array.astype(np.float32) / 32768.0
            
            temp_filename = "temp_recording.wav"
            with wave.open(temp_filename, 'wb') as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(2)
                wf.setframerate(SAMPLE_RATE)
                wf.writeframes((audio_float32 * 32768).astype(np.int16).tobytes())
            
            print("Transcribing with Whisper...")
            result = model.transcribe(temp_filename)
            transcribed_text = result["text"].strip()
            os.remove(temp_filename)
            
            listener.stop()
            return transcribed_text
        listener.stop()
        return ""
    except Exception as e:
        print(f"Error during recording: {str(e)}")
        print("Please check if your microphone is properly connected and enabled.")
        listener.stop()
        return ""


if __name__ == "__main__":
    text = transcribe_audio()
    if text:
        # Save the transcription to transcription.txt in the same directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        output_file = os.path.join(script_dir, "transcription.txt")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(text)
    else:
        print("No transcription to save.")