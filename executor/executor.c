// executor.c

// brew install json-c

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ipc.h>
#include <sys/shm.h>
#include <unistd.h>
#include <sys/wait.h>
#include <json-c/json.h>

#define SHM_KEY 1234
#define SHM_SIZE 4096

void execute_command(struct json_object *cmd_array) {
    int len = json_object_array_length(cmd_array);
    char *args[len + 1];

    for (int i = 0; i < len; i++) {
        args[i] = (char *)json_object_get_string(json_object_array_get_idx(cmd_array, i));
    }
    args[len] = NULL;

    pid_t pid = fork();
    if (pid == 0) {
        // Child process
        execvp(args[0], args);
        perror("execvp failed");
        exit(1);
    } else {
        wait(NULL); // Wait for child to finish
    }
}

int main() {
    int shmid = shmget(SHM_KEY, SHM_SIZE, 0666);
    if (shmid == -1) {
        perror("shmget failed");
        return 1;
    }

    char *data = (char *)shmat(shmid, NULL, 0);
    if (data == (char *)-1) {
        perror("shmat failed");
        return 1;
    }

    struct json_object *parsed = json_tokener_parse(data);
    if (json_object_get_type(parsed) == json_type_array) {
        // Check if nested array
        struct json_object *first = json_object_array_get_idx(parsed, 0);
        if (json_object_get_type(first) == json_type_array) {
            // Multiple commands
            for (int i = 0; i < json_object_array_length(parsed); i++) {
                execute_command(json_object_array_get_idx(parsed, i));
            }
        } else {
            // Single command
            execute_command(parsed);
        }
    } else if (json_object_get_type(parsed) == json_type_string) {
        const char *msg = json_object_get_string(parsed);
        printf("LLM Response: %s\n", msg);
    } else {
        printf("Invalid format from shared memory.\n");
    }

    shmdt(data);
    return 0;
}