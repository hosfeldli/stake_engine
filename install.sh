#!/bin/bash
# This installer creates an executable command "blackjack" that wraps the command:
#    python3 operator_set.py [arguments]
# and places it in /usr/local/bin so that you can run it from anywhere.
#
# The script assumes that it and operator_set.py (inside the "build" directory) are in the same parent directory.

# Determine the directory where this installer script is located.
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Define the full path to operator_set.py in the build directory.
OPERATOR_SET="$SCRIPT_DIR/build/operator_set.py"

# Check if operator_set.py exists.
if [ ! -f "$OPERATOR_SET" ]; then
    echo "Error: operator_set.py not found in $SCRIPT_DIR/build"
    exit 1
fi

# Define the target path for the blackjack command.
TARGET="/usr/local/bin/blackjack"

# Install the required Python packages.
echo "Setting up Python virtual environment and installing dependencies..."
cd "$SCRIPT_DIR"/build
python3 -m venv venv > /dev/null 2>&1 && source venv/bin/activate > /dev/null 2>&1
pip install --upgrade pip > /dev/null 2>&1 && pip install -r "$SCRIPT_DIR/build/requirements.txt" > /dev/null 2>&1

echo "Creating blackjack command at $TARGET ..."

# Use sudo to write the wrapper script into /usr/local/bin.
# The script will change directory to the operator_set.py location (i.e. the build directory)
# and then execute operator_set.py with any parameters passed to blackjack.
sudo tee "$TARGET" > /dev/null << 'EOF'
#!/bin/bash
# blackjack wrapper command: changes to the directory of operator_set.py and passes all arguments to it.
EOF

# Append the command that changes directory and calls operator_set.py.
# This uses the absolute path to operator_set.py's directory.
OPERATOR_DIR="$(dirname "$OPERATOR_SET")"
sudo sh -c "echo 'cd \"$OPERATOR_DIR\" && python3 \"operator_set.py\" \"\$@\" >> log.txt 2>&1' >> \"$TARGET\""

# Make the new blackjack command executable.
sudo chmod +x "$TARGET"

echo "Installation complete!"
echo "You can now use 'blackjack' from the command line. For example:"
echo "    blackjack -s"
echo ""
echo "If you get a 'command not found' error, ensure that /usr/local/bin is in your PATH."
