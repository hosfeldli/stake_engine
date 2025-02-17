import ctypes
import os
import time
import json

# Load the compiled Rust shared library
print("Current working directory:", os.getcwd())
lib_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "target/release/libmouse_listener.dylib"))  # Adjust path as needed
mouse_lib = ctypes.CDLL(lib_path)

# Define function signatures
mouse_lib.get_last_click_position.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double)]
mouse_lib.get_last_click_position.restype = None

mouse_lib.start_mouse_listener.argtypes = []
mouse_lib.start_mouse_listener.restype = None


def get_last_click_position():
    """Get the last recorded click position."""
    x, y = ctypes.c_double(), ctypes.c_double()
    mouse_lib.get_last_click_position(ctypes.byref(x), ctypes.byref(y))
    return x.value, y.value


def start_mouse_listener():
    """Start the mouse listener."""
    mouse_lib.start_mouse_listener()


def read_last_click_from_file(file_path='./data/movements.json'):
    """Read the last click position from the JSON file."""
    try:
        with open(file_path, 'r') as f:
            events = f.readlines()
            if events:
                # The most recent event will be the last one in the list
                last_event = json.loads(events[-1].strip())

                if last_event['event_type'] == 'MouseClick':
                    return last_event['x'], last_event['y'], last_event['timestamp']
    except FileNotFoundError:
        return None  # No file yet, so no clicks
    except Exception as e:
        print(f"Error reading file: {e}")
        return None


def start_listener():
    """Start listener and block until a new click event is recorded in the movements.json."""
    # Start the listener
    start_mouse_listener()

    last_click_position = (-1.0, -1.0)  # Initial dummy value
    movements_file = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data/movements.json'))  # Adjust path as needed
    print(movements_file)

    start = time.time()

    while True:
        # Check the file for the latest click position
        click_position = read_last_click_from_file(movements_file)
        if click_position and click_position != last_click_position and click_position[2] > start:
            click_position = click_position[:2]
            last_click_position = click_position  # Update to new click position
            return click_position  # Return the new click position and exit the loop
        time.sleep(0.5)  # Small delay before checking the file again
