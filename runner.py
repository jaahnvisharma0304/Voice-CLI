import subprocess
import json
import sys
import os

# Step 1: Run the transcriber
def run_transcriber():
    print("[*] Running transcriber...")
    try:
        subprocess.run(["python3", "transcriber/transcribe.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"[!] Error running transcriber: {e}")
        sys.exit(1)

    # Read the transcription output
    try:
        with open("transcriber/transcription.txt", "r") as f:
            transcription = f.read().strip()
            print("[+] Transcription:", transcription)
            return transcription
    except Exception as e:
        print(f"[!] Error reading transcription.txt: {e}")
        sys.exit(1)

def run_llm(transcription):
    print("[*] Running LLM backend...")
    try:
        # Import the LLM module
        sys.path.append('llm_backend')
        import llm as llm_module
        
        result = llm_module.llm(transcription)
        print("[+] LLM result:", result)
        
        # Check if result is a special response (string)
        if isinstance(result, str) and result in ["No command found", "Command unclear"]:
            print(f"[!] LLM returned: {result}")
            return False
        
        return True
        
    except Exception as e:
        print(f"[!] Error running LLM: {e}")
        sys.exit(1)

def run_writer():
    print("[*] Writing to shared memory...")
    try:
        subprocess.run(["python3", "shared_memory/writer.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"[!] Error running writer: {e}")
        sys.exit(1)

def run_executor():
    print("[*] Running C executor...")
    try:
        # Check if the executor exists
        if not os.path.exists("./executor/executor.out"):
            print("[!] Executor not found. Compiling...")
            subprocess.run(["gcc", "-o", "executor/executor.out", "executor/executor.c", "-ljson-c"], check=True)
        
        subprocess.run(["./executor/executor.out"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"[!] Error running executor: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("🔁 Voice-Controlled CLI Pipeline Starting...\n")
    
    # Option 1: Use transcriber
    transcription = run_transcriber()
    success = run_llm(transcription)
    
    # # Option 2: Use test input (current setup)
    # success = run_llm("make a text file meow.txt in a folder big")
    
    if success:
        run_writer()
        run_executor()
        print("\n✅ Pipeline execution completed successfully.")
    else:
        print("\n❌ Pipeline stopped due to LLM response.")