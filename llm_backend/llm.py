#!/usr/bin/env python3
# pip install langchain langchain-google-genai python-dotenv sysv-ipc

from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
import json
import os
import ast
load_dotenv()

def llm(transcribed_text):
    model = ChatGoogleGenerativeAI(model="learnlm-2.0-flash-experimental")

    prompt1 = PromptTemplate(
        input_variables=["user_input"],
        template="""
    You are a terminal command generator designed to assist in safely executing Linux commands based on natural language input from a user.

    Instructions:

    Carefully analyze the user input: {user_input}

    Your goal is to extract executable Linux terminal command(s) from the user's request.

    Response Format:
    - For a single command: Return exactly ["command", "arg1", "arg2", ...] as a Python list of strings.
    - For multiple commands: Return exactly [["command1", "arg1", ...], ["command2", "arg1", ...], ...] as a nested Python list of strings.

    Do NOT add any additional explanation or context.
    Only return valid command(s) that a user could run directly in a bash terminal.

    Rules:

    1. If the user's input does not include any command or action to be executed, respond with: No command found
    2. If the user's request is vague or ambiguous and cannot be safely interpreted into specific command(s), respond with: Command unclear
    3. Do NOT include sudo, rm -rf /, or any dangerous command. Ignore commands that might damage the system.
    4. If the command can be interpreted in multiple ways, prefer the safest and most commonly used interpretation.
    5. For file operations, interpret context correctly (e.g., "create a file inside a folder" should generate commands that create both the folder and the file).
    6. For folder creation, use mkdir.
    7. For file creation, use touch.
    8. For sequential operations that logically require multiple commands, return a nested list of commands.

    Your response should never contain anything except the command list(s) or the phrases mentioned above.

    Examples: 

    Input: "Show me all files including hidden ones" 
    Output: ["ls", "-la"]

    Input: "Clear the screen" 
    Output: ["clear"]

    Input: "Can you launch firefox?" 
    Output: ["firefox"]

    Input: "Create a folder named myfolder" 
    Output: ["mkdir", "myfolder"]

    Input: "Create a folder named myfolder and create a text file inside it called hello.txt" 
    Output: [["mkdir", "myfolder"], ["touch", "myfolder/hello.txt"]]

    Input: "List all processes and save the output to processes.txt" 
    Output: ["ps", "aux", ">", "processes.txt"]

    Input: "Hey, what's up?" 
    Output: No command found

    Input: "Remove everything" 
    Output: Command unclear
    """
    )

    parser = StrOutputParser()
    chain = prompt1 | model | parser
    result = chain.invoke({"user_input": transcribed_text})
    print("Generated response:", result)

    # Handle special responses
    if result.strip() in ["No command found", "Command unclear"]:
        return result.strip()
    
    # Try to parse the result as a Python list
    try:
        # Convert the string representation of a list to an actual Python list
        command_list = ast.literal_eval(result.strip())
        
        # Write result to a temporary file
        with open('command_output.txt', 'w') as f:
            json.dump(command_list, f)
        print("Command written to file.")
        
        return command_list
    except (SyntaxError, ValueError) as e:
        print(f"Error parsing LLM output: {e}")
        print(f"Raw output: {result}")
        return "Command unclear"

if __name__ == "__main__":
    print("Terminal Command Generator")
    user_input = input("How can this terminal assist you? \n")
    result = llm(user_input)
    print("\nFinal result:", result)