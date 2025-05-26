// executor.c
// Compile with: gcc -o executor.out executor.c -ljson-c

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
#define MAX_ARGS 100

void execute_command(struct json_object *cmd_array) {
    if (!cmd_array || json_object_get_type(cmd_array) != json_type_array) {
        fprintf(stderr, "Invalid command array\n");
        return;
    }

    int len = json_object_array_length(cmd_array);
    if (len == 0) {
        fprintf(stderr, "Empty command array\n");
        return;
    }
    if (len > MAX_ARGS) {
        fprintf(stderr, "Too many arguments (%d, max %d)\n", len, MAX_ARGS);
        return;
    }

    char *args[MAX_ARGS + 1];
    printf("Executing command: ");
    
    for (int i = 0; i < len; i++) {
        struct json_object *arg_obj = json_object_array_get_idx(cmd_array, i);
        if (!arg_obj || json_object_get_type(arg_obj) != json_type_string) {
            fprintf(stderr, "Invalid argument type at index %d\n", i);
            return;
        }
        args[i] = (char *)json_object_get_string(arg_obj);
        printf("%s ", args[i]);
    }
    printf("\n");
    
    args[len] = NULL;

    pid_t pid = fork();
    if (pid == 0) {
        // Child process
        execvp(args[0], args);
        perror("execvp failed");
        exit(1);
    } else if (pid > 0) {
        // Parent process - wait for child to complete
        int status;
        wait(&status);
        if (WIFEXITED(status)) {
            int exit_code = WEXITSTATUS(status);
            if (exit_code != 0) {
                printf("Command exited with code: %d\n", exit_code);
            }
        }
    } else {
        perror("fork failed");
    }
}

int main() {
    printf("Starting executor...\n");
    
    int shmid = shmget(SHM_KEY, SHM_SIZE, 0666);
    if (shmid == -1) {
        perror("shmget failed - make sure writer.py has run first");
        return 1;
    }

    char *data = (char *)shmat(shmid, NULL, 0);
    if (data == (char *)-1) {
        perror("shmat failed");
        return 1;
    }

    printf("Reading data from shared memory...\n");
    printf("Raw data: %.100s%s\n", data, strlen(data) > 100 ? "..." : "");

    struct json_object *parsed = json_tokener_parse(data);
    if (!parsed) {
        fprintf(stderr, "Failed to parse JSON from shared memory\n");
        fprintf(stderr, "Data was: %s\n", data);
        shmdt(data);
        return 1;
    }

    if (json_object_get_type(parsed) == json_type_array) {
        struct json_object *first = json_object_array_get_idx(parsed, 0);
        if (first && json_object_get_type(first) == json_type_array) {
            // Nested array (multiple commands)
            printf("Executing %d commands sequentially...\n", json_object_array_length(parsed));
            for (int i = 0; i < json_object_array_length(parsed); i++) {
                struct json_object *cmd = json_object_array_get_idx(parsed, i);
                printf("\n--- Command %d ---\n", i + 1);
                execute_command(cmd);
            }
        } else {
            // Single command array
            printf("Executing single command...\n");
            execute_command(parsed);
        }
    } else if (json_object_get_type(parsed) == json_type_string) {
        printf("LLM Response: %s\n", json_object_get_string(parsed));
    } else {
        fprintf(stderr, "Unexpected JSON format from shared memory.\n");
        fprintf(stderr, "Type was: %d\n", json_object_get_type(parsed));
    }

    // Cleanup
    json_object_put(parsed);
    shmdt(data);
    
    printf("Executor finished.\n");
    return 0;
}