# Set target name and paths
TARGET = libmouse_listener
BUILD_DIR = target/release
LIB_NAME = $(BUILD_DIR)/$(TARGET).dylib

# Default target: build Rust shared library
all: build

# Build the Rust shared library
build:
	cargo build --release

# Install the shared library (copy it to the working directory for Python)
install: build
	cp $(LIB_NAME) .

# Clean the build directory
clean:
	cargo clean

# Run the Python script using the built Rust library
run: install
	python3 py_mouse.py

# Grant macOS Accessibility permissions (manual step)
permissions:
	echo "Please ensure Terminal/iTerm has Accessibility permissions in System Settings -> Privacy & Security -> Accessibility"

# Full setup: build, install, and notify about permissions
setup: install permissions
	@echo "Setup complete. Run 'make run' to start."
