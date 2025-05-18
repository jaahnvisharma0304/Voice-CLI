# main.py
from transcriber.transcribe import transcribe_audio
from llm_backend.llm import llm
from shared_memory.writer import write_to_shm

# Pipeline Execution
result = None | transcribe_audio | llm
if result not in ["No command found", "Command unclear"]:
    write_to_shm(result)
    print("Now run ./executor to execute the command.")
