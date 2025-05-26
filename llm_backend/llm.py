#!/usr/bin/env python3
# pip install langchain langchain-google-genai python-dotenv sysv-ipc

from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
import json
import os
import ast
import re
load_dotenv()

def llm(transcribed_text):
    model = ChatGoogleGenerativeAI(model="learnlm-2.0-flash-experimental")

    prompt1 = PromptTemplate(
        input_variables=["user_input"],
        template="""
    You are a terminal command generator that converts natural language instructions into safe and visible Linux bash commands, primarily for use in WSL (Windows Subsystem for Linux) or Linux environments.

Your job is to generate commands that not only execute the user's request but also open relevant folders and files so the user can **visibly confirm the action**.

Instructions:

1. Carefully analyze the user input: {user_input}

2. If the command involves a folder:
   - Open the folder **first** using `explorer.exe <folder>` (Windows) or `xdg-open <folder>` (Linux).
   - If **no folder is specified**, default to opening the current folder using:
     - `explorer.exe .` (Windows)
     - or `xdg-open .` (Linux)

3. For each action (create file, write text, open file), generate safe sequential commands with `sleep 1` in between for visibility.

4. Use the following tools:
   - `mkdir -p` for creating folders
   - `touch` or `echo` for creating/writing files
   - `code`, `notepad.exe`, or `xdg-open` to open files
   - `explorer.exe` to open folders in Windows
   - `sleep 1` between steps

5. Output format - ONLY return the raw JSON array, no markdown formatting:
   - For a single command: ["command", "arg1", "arg2", ...]
   - For multiple sequential commands: [["cmd1", ...], ["cmd2", ...], ...]

6. Response Rules:
   - If there's no actionable command, respond ONLY: No command found
   - If the input is vague or risky (like "delete everything"), respond ONLY: Command unclear
   - NEVER use sudo or destructive commands like `rm -rf`
   - DO NOT wrap your response in markdown code blocks or any other formatting

Examples:

Input: "Create a folder in C drive called testfolder2, then create text.txt inside it with the content 'hello' and open it"
Output:
[["explorer.exe", "C:\\\\"], ["sleep", "1"], ["mkdir", "-p", "/mnt/c/testfolder2"], ["sleep", "1"], ["explorer.exe", "C:\\\\testfolder2"], ["sleep", "1"], ["echo", "hello", ">", "/mnt/c/testfolder2/text.txt"], ["sleep", "1"], ["code", "/mnt/c/testfolder2/text.txt"]]

Input: "Create a file called notes.txt in the current folder and open it"
Output:
[["explorer.exe", "."], ["sleep", "1"], ["touch", "notes.txt"], ["sleep", "1"], ["code", "notes.txt"]]

Input: "What's up?"
Output: No command found

Input: "Remove everything"
Output: Command unclear

CRITICAL: Return ONLY the JSON array or special response. No markdown, no extra text, no formatting.

    """
    )

    parser = StrOutputParser()
    chain = prompt1 | model | parser
    result = chain.invoke({"user_input": transcribed_text})
    print("Generated response:", result)

    # Handle special responses
    if result.strip() in ["No command found", "Command unclear"]:
        return result.strip()
    
    # Clean markdown formatting if present
    cleaned_result = result.strip()
    if cleaned_result.startswith('```'):
        # Remove markdown code blocks
        lines = cleaned_result.split('\n')
        # Find the actual JSON content between ```
        json_lines = []
        in_code_block = False
        for line in lines:
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                continue
            if in_code_block:
                json_lines.append(line)
        cleaned_result = '\n'.join(json_lines).strip()
    
    # Try to extract command array from response
    try:
        # First, try to parse the result directly
        command_list = ast.literal_eval(cleaned_result)
    except (SyntaxError, ValueError):
        # If direct parsing fails, try to extract the array from formatted response
        try:
            # Look for array pattern in the response
            array_pattern = r'\[\s*\[.*?\]\s*(?:,\s*\[.*?\]\s*)*\]|\[.*?\]'
            matches = re.findall(array_pattern, cleaned_result, re.DOTALL)
            
            if matches:
                # Take the largest match (most likely the complete command array)
                array_str = max(matches, key=len)
                command_list = ast.literal_eval(array_str)
            else:
                raise ValueError("No valid array found in response")
                
        except (SyntaxError, ValueError) as e:
            print(f"Error parsing LLM output: {e}")
            print(f"Raw output: {result}")
            print(f"Cleaned output: {cleaned_result}")
            return "Command unclear"
    
    try:
        # Ensure the shared_memory directory exists
        os.makedirs('shared_memory', exist_ok=True)
        
        # Write the command list as JSON for the writer to read
        with open('shared_memory/command_output.txt', 'w') as f:
            json.dump(command_list, f, indent=2)

        print("Commands written to JSON file.")
        
        # Also generate the bash command string for display
        if isinstance(command_list[0], list):
            # Multiple commands, join with &&
            command_str = ' && '.join([' '.join(cmd) for cmd in command_list])
        else:
            # Single command, just join the list
            command_str = ' '.join(command_list)
            
        print(f"Command string: {command_str}")
        return command_list  # Return the list for JSON serialization

    except (IndexError, TypeError) as e:
        print(f"Error processing command list: {e}")
        print(f"Parsed command_list: {command_list}")
        return "Command unclear"