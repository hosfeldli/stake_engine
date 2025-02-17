import argparse
from packages.util import best_move, update_html, notify
import pyautogui
import time
import sys
from pynput import keyboard
import configparser
import os
import threading
from pynput import mouse
from packages.mouse_lib.mouse_listener.listener import start_listener  # Import from the installed package

prog_state = True
CONFIG_FILE = 'coordinates.ini'

def get_mouse_click(timeout=30):
    """
    Wait for a single mouse click and return the (x, y) coordinates.
    Adds a timeout to prevent indefinite blocking.
    :param timeout: Maximum time to wait for a mouse click in seconds.
    :return: Tuple (x, y) representing the coordinates of the mouse click, or None if timeout occurs.
    """
    return start_listener()

def setup_coordinates():
    """
    Captures screen coordinates for different moves with a single-threaded approach
    and timeout handling.
    """
    moves = ["None", "Insurance", "Stand", "Hit", "Double Down"]
    config = configparser.ConfigParser()
    config.add_section("Coordinates")
    
    notify("Setting up coordinates for each move.")
    time.sleep(1)

    for move in moves:
        if move == "Insurance":
            notify("\nSet the coordinate for 'Split'")
        elif move == "None":
            notify("\nSet the coordinate for 'Play'")
        else:
            notify(f"\nSet the coordinate for '{move}'.")
        
        coordinate = None
        while coordinate is None:
            notify("Click within 30 seconds...")
            coordinate = get_mouse_click()
            if coordinate:
                config.set("Coordinates", move, f"{int(coordinate[0])}, {int(coordinate[1])}")
                notify(f"Coordinate recorded for {move}.")
            else:
                notify("No valid click detected. Please try again.")

    with open(CONFIG_FILE, "w") as configfile:
        config.write(configfile)
    notify(f"\nConfiguration saved to '{CONFIG_FILE}'.")

def load_coordinates(config_file):
    """
    Load the coordinate values from the given configuration file.
    Expects the file to have a [Coordinates] section with keys mapping
    to x,y coordinate pairs (comma-separated).
    """
    config = configparser.ConfigParser()
    config.read(config_file)
    coords = {}
    
    if 'Coordinates' not in config:
        raise ValueError("Config file is missing the 'Coordinates' section.")
    
    for move, value in config['Coordinates'].items():
        try:
            x_str, y_str = value.split(',')
            coords[move.strip()] = (int(x_str.strip()), int(y_str.strip()))
        except Exception as e:
            print(f"Error parsing coordinate for '{move}': {e}")
    return coords

def main():
    global prog_state  # Use the global prog_state to control loop termination
    notify("Starting...")

    # Ensure the configuration file exists, and create a default one if not.
    # Load coordinates from the config file.
    coordinates = load_coordinates(CONFIG_FILE)
    
    # Main loop of the program
    prog_state = True  # Reset prog_state before entering loop.
    while prog_state:
        print("Running...")
        time.sleep(0.8)
        
        # Update game state and determine the best move
        update_html()   # Update HTML or game state.
        move = str(best_move()).lower()  # Determine the best move.
        print("Determined move:", move)
        
        # Look up the coordinates for the move from the config.
        if move in coordinates:
            x, y = coordinates[str(move).lower()]
            pyautogui.click(x, y)
            print(f"Clicked at: ({x}, {y}) for move '{move}'")
        else:
            # Fallback action if move isn't defined in the config.
            print(f"Move '{move}' not found in config. Executing default action.")
            default_coords = coordinates.get("None", (255, 414))
            pyautogui.click(*default_coords)

    print("Exiting...")
    sys.exit(0)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Game automation script with configurable click coordinates."
    )
    parser.add_argument(
        "-s", "--setup",
        action="store_true",
        help="Set up the coordinates.ini configuration file."
    )
    args = parser.parse_args()

    if args.setup or not os.path.exists(CONFIG_FILE):
        # Run the configuration setup and exit if setup flag is provided
        # or if the coordinates.ini file doesn't exist.
        setup_coordinates()
    main()
