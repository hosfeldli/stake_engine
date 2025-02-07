import argparse
from util import best_move, update_html, notify
import pyautogui
import time
import sys
from pynput import keyboard
import configparser
import os
from pynput.mouse import Listener as mouse

prog_state = True
CONFIG_FILE = 'coordinates.ini'

def on_press(key):
    try:
        print(f'Key pressed: {key.char}')
    except AttributeError:
        print(f'Special key pressed: {key}')

def on_release(key):
    global prog_state
    print(f'Key released: {key}')
    if key == keyboard.Key.esc or key == keyboard.Key.ctrl:
        print("Exit key pressed. Stopping listener and exiting.")
        prog_state = False
        listener.stop()
        sys.exit(0)  # Gracefully exit the script

# Create a listener and start listening in a separate thread.
listener = keyboard.Listener(on_press=on_press, on_release=on_release)
listener.start()

def get_mouse_click():
    """
    Wait for a single mouse click and return the (x, y) coordinates.
    """
    coordinate = None

    def on_click(x, y, button, pressed):
        nonlocal coordinate
        if pressed:
            coordinate = (x, y)
            # Stop the listener after the first click
            return False

    with mouse(on_click=on_click) as m_listener:
        m_listener.join()
    return coordinate

def setup_coordinates():
    """
    For each move, wait 5 seconds, notify the user to click the desired
    location on the screen, capture that coordinate, and save it to the
    configuration file.
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
        time.sleep(1)
        coordinate = None
        while not coordinate:
            coordinate = get_mouse_click()
        config.set("Coordinates", move, f"{int(coordinate[0])}, {int(coordinate[1])}")
        notify(f"Coordinate for recorded.")
    
    # Save the coordinates to the configuration file.
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

    if args.setup:
        # Run the configuration setup and exit.
        setup_coordinates()
    main()
