# shared_memory/writer.py
import sysv_ipc
import json

def write_to_shm(commands):
    SHM_KEY = 1234
    SHM_SIZE = 4096

    memory = sysv_ipc.SharedMemory(SHM_KEY, sysv_ipc.IPC_CREAT, size=SHM_SIZE)
    data = json.dumps(commands)
    memory.write(data.encode('utf-8'))

if __name__ == "__main__":
    with open("command_output.txt") as f:
        commands = json.load(f)
    write_to_shm(commands)
