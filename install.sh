#!/bin/bash
export LC_ALL=C
export PYTHONWARNINGS="ignore"  # Suppress GIL warnings

# Function to display an error message and exit.
error_exit() {
  zenity --error --title="Installation Error" --width=400 --text="$1" 2>/dev/null
  exit 1
}

# Check if Zenity is installed; if not, attempt to install it on macOS via Homebrew.
if ! command -v zenity > /dev/null 2>&1; then
  if [[ "$OSTYPE" == "darwin"* ]]; then
    if ! command -v brew > /dev/null 2>&1; then
      echo "Homebrew is not installed. Please install Homebrew from https://brew.sh/ and then re-run the installer."
      exit 1
    fi
    echo "Zenity not found. Installing Zenity using Homebrew..."
    brew install zenity
    if ! command -v zenity > /dev/null 2>&1; then
      echo "Failed to install Zenity using Homebrew. Please install it manually (brew install zenity) and re-run the installer."
      exit 1
    fi
  else
    echo "Zenity is required for this installer. Please install Zenity and try again."
    exit 1
  fi
fi

# Scan /Applications for available AppleScript-enabled browsers.
AVAILABLE_APPS=()
if [ -d "/Applications/Safari.app" ]; then
  AVAILABLE_APPS+=("Safari")
fi
if [ -d "/Applications/Google Chrome.app" ]; then
  AVAILABLE_APPS+=("Google Chrome")
fi
# Add additional checks here if you know other browsers that support AppleScript.
if [ ${#AVAILABLE_APPS[@]} -eq 0 ]; then
  error_exit "No supported browser applications were found in the /Applications folder."
fi

# Use Zenity to let the user pick their desired application for the HTML extraction
BROWSER_APP=$(zenity --list --title="Select Browser for HTML Extraction" \
  --text="Choose application for interfance... (must be run again to change):" \
  --column="Browser" "${AVAILABLE_APPS[@]}")
  
if [ -z "$BROWSER_APP" ]; then
  error_exit "No application selected. Installation aborted."
fi

# Export the chosen browser so that your Python function can later pull it from the environment.
export BROWSER_APP

# Prompt the user for their sudo password using Zenity.
while true; do
  SUDO_PASS=$(zenity --password --title="Sudo Authentication" --text="Enter your sudo password:" 2>/dev/null)
  if [ -z "$SUDO_PASS" ]; then
    error_exit "No password provided. Installation aborted."
  fi

  # Test the sudo password
  echo "$SUDO_PASS" | sudo -S true 2>/dev/null
  if [ $? -eq 0 ]; then
    break
  else
    zenity --error --title="Incorrect Password" --width=400 --text="Incorrect sudo password. Please try again." 2>/dev/null
  fi
done

# Determine the directory where this installer script is located.
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Pre-flight check: Ensure blackjack.py exists.
BLACKJACK_FILE="$SCRIPT_DIR/build/blackjack.py"
if [ ! -f "$BLACKJACK_FILE" ]; then
  error_exit "Error: blackjack.py not found in $SCRIPT_DIR/build"
fi

# Ask user to proceed using a Zenity question.
if ! zenity --question --title="Blackjack Installer Wizard" --width=400 --text="Welcome to the Blackjack Installer Wizard!\n\nThis installer creates an executable command 'blackjack' that wraps:\n    python3 blackjack.py [arguments]\nand places it in /usr/local/bin so that you can run it from anywhere.\n\nDo you want to proceed with the installation?" 2>/dev/null; then
  zenity --info --title="Installation Aborted" --width=300 --text="Installation aborted by user." 2>/dev/null
  exit 1
fi

# Run the rest of your installation steps within a Zenity progress bar.
{
  echo "0"
  echo "# Starting Blackjack Installer Wizard..."
  sleep 1

  echo "5"
  echo "# Creating Python virtual environment (.venv)..."
  cd "$SCRIPT_DIR/build" || exit 1
  python3 -m venv .venv
  source .venv/bin/activate
  sleep 1

  echo "25"
  echo "# Upgrading pip and installing dependencies..."
  pip3 install --upgrade pip > /dev/null 2>&1
  pip3 install -r "$SCRIPT_DIR/build/packages/requirements.txt" > /dev/null 2>&1
  sleep 1

  # Installing your mouse_listener package
  echo "30"
  echo "# Installing mouse_listener Python package..."
  pip3 install "$SCRIPT_DIR/build/packages/mouse_listener" > /dev/null 2>&1  # Update with actual path or package name
  sleep 1

  echo "50"
  echo "# Creating 'blackjack' command in /usr/local/bin..."
  TARGET="/usr/local/bin/blackjack"
  # Create the wrapper script using sudo.
  echo "$SUDO_PASS" | sudo -S tee "$TARGET" > /dev/null << 'EOF'
#!/bin/bash
# blackjack wrapper command: sets up the environment, runs blackjack.py, then deactivates.
EOF
  sleep 1

  echo "70"
  echo "# Configuring the wrapper to activate .venv and run blackjack.py..."
  # Generate the command so that it changes into the build directory,
  # activates the .venv virtual environment, runs blackjack.py with arguments, and then deactivates.
  echo "$SUDO_PASS" | sudo -S sh -c "echo 'cd \"${SCRIPT_DIR}/build\" && source .venv/bin/activate && python3 \"blackjack.py\" \"\$@\" && deactivate' >> \"$TARGET\""
  sleep 1

  echo "85"
  echo "# Setting executable permissions on the blackjack command..."
  echo "$SUDO_PASS" | sudo -S chmod +x "$TARGET"
  sleep 1

  echo "100"
  echo "# Installation Complete!"
  sleep 1
} | zenity --progress --title="Installing Blackjack" --width=400 --auto-close --no-cancel --text="Installing, please wait..." 2>/dev/null

# If the progress dialog exits with an error, display an error message.
if [ $? -ne 0 ]; then
  error_exit "Installation encountered an error. Please check the logs for more details."
fi
