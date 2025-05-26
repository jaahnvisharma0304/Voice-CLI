import sysv_ipc
import json
import sys
import os

def write_to_shm(commands):
    SHM_KEY = 1234
    SHM_SIZE = 4096

    try:
        memory = sysv_ipc.SharedMemory(SHM_KEY, sysv_ipc.IPC_CREAT, size=SHM_SIZE)
    except Exception as e:
        print(f"Error creating shared memory: {e}")
        sys.exit(1)

    data = json.dumps(commands)
    
    # Check if data fits in shared memory
    if len(data.encode('utf-8')) >= SHM_SIZE:
        print(f"Error: Data too large for shared memory ({len(data)} bytes, max {SHM_SIZE})")
        sys.exit(1)

    # Clear the shared memory area before writing
    memory.write(b'\0' * SHM_SIZE)
    memory.write(data.encode('utf-8'))
    
    print(f"Data written to shared memory: {len(data)} bytes")

if __name__ == "__main__":
    # Check if the command output file exists
    if not os.path.exists("shared_memory/command_output.txt"):
        print("Error: command_output.txt not found in shared_memory directory")
        sys.exit(1)
    
    try:
        with open("shared_memory/command_output.txt") as f:
            commands = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON from command_output.txt: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading command_output.txt: {e}")
        sys.exit(1)

    write_to_shm(commands)
    print("Commands written to shared memory successfully.")