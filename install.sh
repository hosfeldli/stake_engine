#!/bin/bash
# -----------------------------------------------------------------------------
# Blackjack Installer Wizard with a Single Progress Bar (macOS Version)
# -----------------------------------------------------------------------------

# Function to show an error message and exit.
error_exit() {
  zenity --error --title="Installation Error" --width=400 --text="$1"
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
    # Verify installation
    if ! command -v zenity > /dev/null 2>&1; then
      echo "Failed to install Zenity using Homebrew. Please install it manually (brew install zenity) and re-run the installer."
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
  error_exit "No password provided. Installation aborted."
fi

# Determine the directory where this installer script is located.
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check if blackjack.py exists in the build directory BEFORE starting the progress bar.
if [ ! -f "$SCRIPT_DIR/build/blackjack.py" ]; then
  error_exit "Error: blackjack.py not found in $SCRIPT_DIR/build"
fi

# Start the progress bar and execute all installation steps in one continuous flow.
{
  echo "0"
  echo "# Starting Blackjack Installer Wizard..."
  sleep 1

  echo "5"
  echo "# Creating Python virtual environment..."
  cd "$SCRIPT_DIR/build" || exit 1
  python3 -m venv venv
  source venv/bin/activate
  sleep 1

  echo "25"
  echo "# Upgrading pip and installing dependencies..."
  pip install --upgrade pip > /dev/null 2>&1
  pip install -r "$SCRIPT_DIR/build/packages/requirements.txt" > /dev/null 2>&1
  sleep 1

  echo "50"
  echo "# Creating 'blackjack' command in /usr/local/bin..."
  TARGET="/usr/local/bin/blackjack"
  # Write the base content to $TARGET using sudo
  echo "$SUDO_PASS" | sudo -S tee "$TARGET" > /dev/null << 'EOF'
#!/bin/bash
# blackjack wrapper command: changes to the directory of blackjack.py and passes all arguments to it.
EOF
  sleep 1

  echo "70"
  echo "# Configuring the blackjack command..."
  # Determine the absolute directory where blackjack.py is located.
  OPERATOR_DIR="$(dirname "$SCRIPT_DIR/build/blackjack.py")"
  echo "$SUDO_PASS" | sudo -S sh -c "echo 'cd \"$OPERATOR_DIR\" && python3 \"blackjack.py\" \"\$@\" >> log.txt 2>&1' >> \"$TARGET\""
  sleep 1

  echo "85"
  echo "# Setting executable permissions..."
  echo "$SUDO_PASS" | sudo -S chmod +x "$TARGET"
  sleep 1

  echo "100"
  echo "# Installation Complete!"
  sleep 1
} | zenity --progress --title="Installing Blackjack" --width=400 --no-cancel --text="Installing, please wait..."

# Check if the progress command exited successfully.
if [ $? -ne 0 ]; then
  error_exit "Installation encountered an error. Please check the logs for more details."
fi