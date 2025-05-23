# Rock-Paper-Scissors with ESP32 and MediaPipe

This project allows you to play Rock-Paper-Scissors using hand gestures detected via a webcam (MediaPipe in Python) and shows the result on LEDs connected to an ESP32 board.

## Components

- ESP32 Microcontroller
- 6 LEDs (for Player and Computer moves)
- USB Cable (for power and programming)
- Wi-Fi (for communication)
- Laptop/PC with a webcam

## Files

- `rps.py`: Python script using MediaPipe and OpenCV to detect hand gestures and send the result to ESP32 over Wi-Fi.
- `rps_esp32.ino`: Arduino sketch that receives the gesture and lights up LEDs accordingly.

## ESP32 Pin Configuration

| Gesture       | Player LED Pin | Computer LED Pin |
|---------------|----------------|------------------|
| Rock          | 16             | 17               |
| Paper         | 18             | 19               |
| Scissors      | 25             | 26               |

Each gesture is represented by lighting up the corresponding LED for the player and the computer.

## How to Run

### 1. Upload Arduino Code to ESP32

- Open `rps_esp32.ino` in Arduino IDE
- Connect your ESP32 and upload the code
- Make sure Wi-Fi credentials match between Python and Arduino code

### 2. Run Python Script

- Install dependencies:
  ```bash
  pip install mediapipe opencv-python requests
  python rps.py
