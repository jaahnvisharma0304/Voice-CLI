from transcripe import transcribe_audio
from llm import llm
from pipe import pipe

result = None | transcribe_audio | llm
print(result)
