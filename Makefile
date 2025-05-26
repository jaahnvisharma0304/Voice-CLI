# Makefile for Voice-Controlled CLI Pipeline

CC = gcc
CFLAGS = -Wall -Wextra -std=c99
LIBS = -ljson-c
EXECUTOR_DIR = executor
EXECUTOR_SRC = $(EXECUTOR_DIR)/executor.c
EXECUTOR_OUT = $(EXECUTOR_DIR)/executor.out

# Default target
all: $(EXECUTOR_OUT)

# Compile the C executor
$(EXECUTOR_OUT): $(EXECUTOR_SRC)
	@echo "Compiling C executor..."
	$(CC) $(CFLAGS) -o $(EXECUTOR_OUT) $(EXECUTOR_SRC) $(LIBS)
	@echo "Executor compiled successfully."

# Clean build artifacts
clean:
	@echo "Cleaning up..."
	rm -f $(EXECUTOR_OUT)
	rm -f shared_memory/command_output.txt
	rm -f command_output.sh
	@echo "Clean complete."

# Install dependencies
install-deps:
	@echo "Installing Python dependencies..."
	pip install langchain langchain-google-genai python-dotenv sysv-ipc
	@echo "Make sure to install json-c library for C compilation:"
	@echo "  Ubuntu/Debian: sudo apt-get install libjson-c-dev"
	@echo "  CentOS/RHEL: sudo yum install json-c-devel"
	@echo "  macOS: brew install json-c"

# Setup project structure
setup:
	@echo "Setting up project structure..."
	mkdir -p llm_backend
	mkdir -p shared_memory
	mkdir -p executor
	mkdir -p transcriber
	@echo "Project structure created."

# Run the pipeline
run: $(EXECUTOR_OUT)
	@echo "Running voice-controlled CLI pipeline..."
	python3 runner.py

# Test with sample input
test: $(EXECUTOR_OUT)
	@echo "Testing pipeline with sample input..."
	python3 runner.py

# Check shared memory status
check-shm:
	@echo "Checking shared memory segments..."
	ipcs -m

# Clean shared memory (if needed)
clean-shm:
	@echo "Cleaning shared memory segments..."
	ipcrm -M 1234 2>/dev/null || true

# Help target
help:
	@echo "Available targets:"
	@echo "  all          - Compile the C executor (default)"
	@echo "  clean        - Remove build artifacts"
	@echo "  install-deps - Install Python dependencies"
	@echo "  setup        - Create project directory structure"
	@echo "  run          - Run the complete pipeline"
	@echo "  test         - Test the pipeline with sample input"
	@echo "  check-shm    - Check shared memory status"
	@echo "  clean-shm    - Clean shared memory segments"
	@echo "  help         - Show this help message"

.PHONY: all clean install-deps setup run test check-shm clean-shm help