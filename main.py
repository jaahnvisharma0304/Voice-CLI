from transcriber.transcripe import transcribe_audio
from llm_backend.llm import llm
from shared_memory.writer import write_to_shm

def main():
    # Call transcription function directly
    transcription_result = transcribe_audio()

    # Optionally print or log transcription result
    print(f"[Transcription] {transcription_result}")

    # Pass the transcription output directly to the LLM function
    llm_result = llm(transcription_result.strip())

    # Print or use the LLM result
    print(f"[Pipeline] Result: {llm_result}")

    # Optionally write to shared memory or do further processing
    write_to_shm(llm_result)

if __name__ == "__main__":
    main()
