#!/bin/bash

# Check if Zenity is installed; if not, attempt to install it on macOS via Homebrew.
if ! command -v zenity > /dev/null 2>&1; then
  if [[ "$OSTYPE" == "darwin"* ]]; then
    if ! command -v brew > /dev/null 2>&1; then
      echo "Homebrew is not installed. Please install Homebrew from https://brew.sh/ and then re-run the installer."
      exit 1
    fi
    echo "Zenity not found. Installing Zenity using Homebrew..."
    brew install zenity
    # Verify installation
    if ! command -v zenity > /dev/null 2>&1; then
      echo "Failed to install Zenity. Please install it manually using Homebrew (brew install zenity) and re-run the installer."
      exit 1
    fi
  else
    echo "Zenity is required for this installer. Please install Zenity and try again."
    exit 1
  fi
fi

# Prompt the user for their sudo password using Zenity.
SUDO_PASS=$(zenity --password --title="Sudo Authentication" --text="Enter your sudo password:")
if [ -z "$SUDO_PASS" ]; then
  zenity --error --title="Authentication Error" --text="No password provided. Installation aborted."
  exit 1
fi

# Determine the directory where this installer script is located.
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# UI: Welcome Message
zenity --info --title="Blackjack Installer Wizard" --width=400 --text="Welcome to the Blackjack Installer Wizard!\n\nThis installer creates an executable command 'blackjack' that wraps:\n    python3 blackjack.py [arguments]\nand places it in /usr/local/bin so that you can run it from anywhere."

# UI: Ask user to proceed
if ! zenity --question --title="Proceed?" --text="Do you want to proceed with the installation?" --width=400; then
  zenity --info --title="Installation Aborted" --width=300 --text="Installation aborted by user."
  exit 1
fi

# Check if blackjack.py exists in the build directory.
BLACKJACK_FILE="$SCRIPT_DIR/build/blackjack.py"
if [ ! -f "$BLACKJACK_FILE" ]; then
  zenity --error --title="Error" --width=400 --text="Error: blackjack.py not found in $SCRIPT_DIR/build"
  exit 1
fi

# UI: Inform user about virtual environment and dependencies setup.
zenity --info --title="Step 1 of 2" --width=400 --text="Setting up Python virtual environment and installing dependencies."

# Change into the build directory.
cd "$SCRIPT_DIR/build"

# Create and activate virtual environment.
python3 -m venv venv
source venv/bin/activate

# Upgrade pip and install dependencies; suppressing output.
pip install --upgrade pip > /dev/null 2>&1
pip install -r "$SCRIPT_DIR/build/packages/requirements.txt" > /dev/null 2>&1

# UI: Inform of next step.
zenity --info --title="Step 2 of 2" --width=400 --text="Creating the 'blackjack' command in /usr/local/bin"

# Define the target path for the blackjack command.
TARGET="/usr/local/bin/blackjack"

# Create the wrapper script with sudo privileges using Zenity's progress indication.
{
  echo "10" ; sleep 0.3
  # Write the base content of the wrapper script using sudo with the provided password.
  echo "$SUDO_PASS" | sudo -S tee "$TARGET" > /dev/null << 'EOF'
#!/bin/bash
# blackjack wrapper command: changes to the directory of blackjack.py and passes all arguments to it.
EOF
  echo "40" ; sleep 0.3
  # Determine the absolute directory where blackjack.py is located.
  OPERATOR_DIR="$(dirname "$BLACKJACK_FILE")"
  echo "$SUDO_PASS" | sudo -S sh -c "echo 'cd \"$OPERATOR_DIR\" && python3 \"blackjack.py\" \"\$@\" >> log.txt 2>&1' >> \"$TARGET\""
  echo "70" ; sleep 0.3
  # Make the command executable.
  echo "$SUDO_PASS" | sudo -S chmod +x "$TARGET"
  echo "100" ; sleep 0.3
} | zenity --progress --title="Installing Blackjack Command" --width=400 --text="Installing, please wait..." --percentage=0 --auto-close

# Final message
zenity --info --title="Installation Complete" --width=400 --text="Installation complete!\n\nYou can now use the command 'blackjack' from the terminal.\n\nFor example:\n    blackjack -s\n\nIf you encounter a 'command not found' error, please ensure that /usr/local/bin is in your PATH."
