Below is an example README you can include with your project. You may save this as `README.md` in the project’s root directory:

---

# Blackjack Automation Tool

This project provides a simple automation tool for playing blackjack. It includes a Bash installer script that sets up a Python virtual environment, installs all necessary dependencies, and creates a global executable command called `blackjack` (placed in `/usr/local/bin`). This command acts as a wrapper for the main Python script (`operator_set.py`) which automates gameplay by reading the game state, determining the best move, and clicking on the corresponding on-screen coordinates.

> **Note:**  
> The installer script and the Python file (`operator_set.py`) should be placed in a parent directory with the following structure:
> 
> ```
> your-project/
> ├── installer.sh         # This Bash installer script
> └── build/
>     ├── operator_set.py  # Main Python automation script
>     └── requirements.txt # List of Python dependencies
> ```

---

## Features

- **Global Command Installation:**  
  The installer creates an executable command `blackjack` available from anywhere in your terminal.

- **Automated Environment Setup:**  
  It creates a Python virtual environment in the `build` directory and installs all required packages (listed in `requirements.txt`).

- **Interactive Configuration:**  
  Use the `--setup` (or `-s`) flag with the `blackjack` command to interactively record on-screen coordinates for various game actions (e.g., Play, Stand, Hit, Double Down).

- **Live Automation:**  
  The main Python script monitors the game state (via an HTML update mechanism and best move logic) and simulates mouse clicks using `pyautogui`. It also listens for key events (using `pynput`) to allow a graceful exit (pressing `ESC` or `CTRL`).

---

## Installation

1. **Prerequisites:**
   - Ensure you have **Python 3** installed.
   - Install `python3-venv` (if not already available) for virtual environment support.
   - You might need administrative privileges (sudo) for writing to `/usr/local/bin`.

2. **Clone or Download the Repository:**

   ```bash
   git clone https://github.com/hosfeldli/stake_engine.git
   cd stake_engine
   ```

3. **Verify the Directory Structure:**

   Make sure the installer script and `operator_set.py` are organized as follows:

   ```
   stake_engine/
   ├── installer.sh         # The Bash installer script
   └── build/
       ├── operator_set.py  # Main Python script
       └── requirements.txt # Python dependencies
   ```

4. **Run the Installer:**

   Make the installer executable (if needed) and run it:

   ```bash
   chmod +x installer.sh
   ./installer.sh
   ```

   The installer will:
   - Determine its own location.
   - Verify that `operator_set.py` exists in the `build` directory.
   - Set up a Python virtual environment and install dependencies.
   - Create a wrapper script at `/usr/local/bin/blackjack` that runs `python3 operator_set.py` with any supplied arguments.
   - Set the appropriate executable permissions.

---

## Usage

### Basic Execution

After installation, you can execute the blackjack automation by simply typing:

```bash
blackjack
```

### Initial Configuration (Setting Up Coordinates)

Before the first run—or if you wish to update your configuration—you need to record the clickable screen coordinates for various game moves. Run:

```bash
blackjack --setup
```
or
```bash
blackjack -s
```

Follow the on-screen prompts:
- You will be notified which move you are configuring (e.g., "Play", "Stand", "Hit", "Double Down", etc.).
- After a short delay, click on the desired position on your screen.
- Your clicks will be recorded and saved to a `coordinates.ini` file in the same directory as `operator_set.py`.

### Running the Automation

Once configured, simply run:

```bash
blackjack
```

The script will:
- Monitor the game state.
- Determine the best move (using logic from the imported `best_move` and `update_html` functions).
- Simulate a mouse click at the configured coordinate for that move.
- Log actions to a file (`log.txt`).

### Exiting the Script

- The script listens for key events. Press `ESC` or `CTRL` to gracefully exit the automation.

---

## Customization

- **Editing Coordinates Manually:**
  The recorded screen coordinates are saved in the `coordinates.ini` file. You can manually edit this file to fine-tune the positions if needed.

- **Dependencies:**
  To add or update dependencies, modify the `build/requirements.txt` file and re-run the installer.

- **Script Logic:**
  The main logic for determining moves is in `operator_set.py`. You can customize the functions (e.g., `best_move`, `update_html`, or `notify`) as necessary for your application.

---

## Troubleshooting

- **Command Not Found:**
  If you receive a `command not found` error when running `blackjack`, ensure that `/usr/local/bin` is included in your system’s PATH.

- **Permission Issues:**
  The installer uses `sudo` to write the `blackjack` command. If you encounter permission issues, check that you have the necessary privileges.

- **Missing Files:**
  The installer verifies that `operator_set.py` exists in the `build` directory. If it’s not found, check your directory structure.

---

## License

This project is open source. You can modify and distribute it under the terms of the [MIT License](LICENSE).

---

## Acknowledgements

- **pyautogui:** For GUI automation.
- **pynput:** For capturing keyboard and mouse events.
- Special thanks to all contributors who helped improve this project.

---

Feel free to modify this README to better suit your project’s needs. Happy automating!