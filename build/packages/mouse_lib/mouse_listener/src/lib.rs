use rdev::{listen, Event, EventType, Button};
use std::sync::{Arc, Mutex};
use std::thread;
use std::ffi::c_void;
use std::os::raw::c_double;
use std::fs::OpenOptions;
use std::io::Write;
use serde::{Serialize, Deserialize};
use std::ptr;
use std::time::{SystemTime, UNIX_EPOCH};

#[derive(Default, Serialize, Deserialize)]
struct MouseState {
    last_click: (f64, f64),
    last_move: (f64, f64),
}

struct SharedState {
    mouse_state: Mutex<MouseState>,
}

impl SharedState {
    fn new() -> Self {
        SharedState {
            mouse_state: Mutex::new(MouseState::default()),
        }
    }

    fn update_move(&self, x: f64, y: f64) {
        let mut state = self.mouse_state.lock().unwrap();
        state.last_move = (x, y);
    }

    fn update_click(&self, x: f64, y: f64) {
        let mut state = self.mouse_state.lock().unwrap();
        state.last_click = (x, y);
    }

    fn get_last_move(&self) -> (f64, f64) {
        let state = self.mouse_state.lock().unwrap();
        state.last_move
    }

    fn get_last_click(&self) -> (f64, f64) {
        let state = self.mouse_state.lock().unwrap();
        state.last_click
    }
}

// Struct to represent the event to log
#[derive(Serialize, Deserialize)]
struct LoggedEvent {
    event_type: String,
    x: f64,
    y: f64,
    timestamp: f64,
}

static mut LAST_STATE: Option<Arc<SharedState>> = None;

fn save_event_to_file(event: &LoggedEvent) {
    let file_path = "./packages/mouse_lib/mouse_listener/data/movements.json";

    // Open the file and append the event
    let file = OpenOptions::new()
        .create(true)
        .append(true)
        .open(file_path);

    if let Ok(mut file) = file {
        let json_event = serde_json::to_string(event).unwrap();
        if let Err(e) = writeln!(file, "{}", json_event) {
            eprintln!("Failed to write to file: {}", e);
        }
    } else {
        eprintln!("Failed to open file for writing.");
    }
}

#[no_mangle]
pub extern "C" fn get_mouse_position(x: *mut c_double, y: *mut c_double) {
    unsafe {
        if let Some(shared_state) = LAST_STATE.as_ref() {
            let (last_x, last_y) = shared_state.get_last_move();
            *x = last_x;
            *y = last_y;
        } else {
            *x = -1.0;
            *y = -1.0;
        }
    }
}

#[no_mangle]
pub extern "C" fn get_last_click_position(x: *mut c_double, y: *mut c_double) {
    unsafe {
        if let Some(shared_state) = LAST_STATE.as_ref() {
            let (last_x, last_y) = shared_state.get_last_click();
            *x = last_x;
            *y = last_y;
        } else {
            *x = -1.0;
            *y = -1.0;
        }
    }
}

#[no_mangle]
pub extern "C" fn start_mouse_listener() -> *mut c_void {
    unsafe {
        // Initialize shared state
        let shared_state = Arc::new(SharedState::new());
        LAST_STATE = Some(shared_state.clone());

        thread::spawn(move || {
            let callback = move |event: Event| {
                match event.event_type {
                    EventType::MouseMove { x, y } => {
                        // Update the last known mouse position
                        shared_state.update_move(x, y);
                    }
                    EventType::ButtonPress(Button::Left) | EventType::ButtonRelease(Button::Left) => {
                        // Use the last recorded mouse position for the click event
                        let current_position = shared_state.get_last_move();

                        // Capture the timestamp
                        let start = SystemTime::now();
                        let since_the_epoch = start.duration_since(UNIX_EPOCH)
                            .expect("Time went backwards");
                        let timestamp = since_the_epoch.as_secs_f64();

                        let logged_event = LoggedEvent {
                            event_type: "MouseClick".to_string(),
                            x: current_position.0,
                            y: current_position.1,
                            timestamp,
                        };
                        save_event_to_file(&logged_event);
                    }
                    _ => {}
                }

                // Log the event for debugging
                //eprintln!("Event: {:?}", event);
            };

            if let Err(error) = listen(callback) {
                eprintln!("Error listening for mouse events: {:?}", error);
            }
        });

        ptr::null_mut()
    }
}
