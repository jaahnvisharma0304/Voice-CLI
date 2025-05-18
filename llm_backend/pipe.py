# llm_backend/pipe.py
def pipe(func):
    def wrapper(input=None):
        return func(input)
    return wrapper
