import cv2
import mediapipe as mp
import socket
import time
import sys
import random
import threading

# ESP32 connection settings
ESP32_IP = '192.168.4.1'  # Default IP when ESP32 is in Access Point mode
ESP32_PORT = 8080

# Initialize MediaPipe Hand Detection
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# Global socket and connection management
sock = None
is_connected = False

def connect_to_esp32():
    global sock, is_connected
    try:
        if sock:
            try:
                sock.close()
            except:
                pass
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)  # 5-second timeout for connection
        sock.connect((ESP32_IP, ESP32_PORT))
        sock.settimeout(None)  # Remove timeout after connection
        is_connected = True
        print(f"Connected to ESP32 at {ESP32_IP}:{ESP32_PORT}")
        return sock
    except Exception as e:
        print(f"Failed to connect to ESP32: {e}")
        is_connected = False
        return None

def send_command(command):
    global sock, is_connected
    if not is_connected or not sock:
        reconnect_result = connect_to_esp32()
        if not reconnect_result:
            print("Unable to reconnect to ESP32")
            return None
    
    try:
        sock.sendall(f"{command}\n".encode())
        # Non-blocking receive with timeout
        sock.settimeout(2)
        try:
            response = sock.recv(1024).decode().strip()
            sock.settimeout(None)
            print(f"ESP32 response: {response}")
            return response
        except socket.timeout:
            print("Receive timeout")
            return None
    except (socket.error, BrokenPipeError) as e:
        print(f"Communication error: {e}")
        is_connected = False
        return None

# Detect hand gestures
def detect_gesture(hand_landmarks):
    # Detect palm (paper)
    if is_palm_open(hand_landmarks):
        return "PAPER"
    
    # Detect fist (rock)
    if is_fist(hand_landmarks):
        return "ROCK"
    
    # Detect victory sign (scissors)
    if is_victory_sign(hand_landmarks):
        return "SCISSORS"
    
    return None

# Detect if palm is open (paper)
def is_palm_open(hand_landmarks):
    finger_tips = [
        hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP],
        hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP],
        hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_TIP],
        hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_TIP]
    ]
    
    finger_pips = [
        hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_PIP],
        hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_PIP],
        hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_PIP],
        hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_PIP]
    ]
    
    extended_fingers = 0
    for tip, pip in zip(finger_tips, finger_pips):
        if tip.y < pip.y:
            extended_fingers += 1
    
    return extended_fingers >= 3

# Detect if hand is making a fist (rock)
def is_fist(hand_landmarks):
    finger_tips = [
        hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP],
        hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP],
        hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_TIP],
        hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_TIP]
    ]
    
    finger_mcps = [
        hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_MCP],
        hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_MCP],
        hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_MCP],
        hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_MCP]
    ]
    
    folded_fingers = 0
    for tip, mcp in zip(finger_tips, finger_mcps):
        if tip.y > mcp.y - 0.05:
            folded_fingers += 1
    
    return folded_fingers >= 3

# Detect victory sign (scissors)
def is_victory_sign(hand_landmarks):
    # Check if only index and middle fingers are extended
    index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
    index_pip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_PIP]
    
    middle_tip = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
    middle_pip = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_PIP]
    
    if index_tip.y < index_pip.y and middle_tip.y < middle_pip.y:
        return True
    
    return False

# Game logic
def determine_winner(player_choice, computer_choice):
    if player_choice == computer_choice:
        return "TIE"
    elif (
        (player_choice == "ROCK" and computer_choice == "SCISSORS") or
        (player_choice == "PAPER" and computer_choice == "ROCK") or
        (player_choice == "SCISSORS" and computer_choice == "PAPER")
    ):
        return "PLAYER"
    else:
        return "COMPUTER"

def main():
    global sock, is_connected
    
    print("Connecting to ESP32...")
    sock = connect_to_esp32()
    if not sock:
        print("Failed to establish initial connection")
        return
    
    # Open webcam
    cap = cv2.VideoCapture(0)
    
    # Game variables
    player_score = 0
    computer_score = 0
    
    last_gesture_time = time.time()
    debounce_time = 2.0  # Time between valid game rounds

    while cap.isOpened():
        try:
            success, image = cap.read()
            if not success:
                print("Failed to capture image")
                break

            image = cv2.flip(image, 1)
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            results = hands.process(image_rgb)
            
            current_time = time.time()
            
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    mp_drawing.draw_landmarks(
                        image, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                    
                    # Game logic with debounce
                    if current_time - last_gesture_time > debounce_time:
                        player_gesture = detect_gesture(hand_landmarks)
                        
                        if player_gesture:
                            # Computer chooses randomly
                            computer_gesture = random.choice(["ROCK", "PAPER", "SCISSORS"])
                            
                            # Determine winner
                            winner = determine_winner(player_gesture, computer_gesture)
                            
                            # Send LED commands with error handling
                            try:
                                send_command(f"PLAYER_{player_gesture}")
                                send_command(f"COMPUTER_{computer_gesture}")
                                
                                # Update scores
                                if winner == "PLAYER":
                                    player_score += 1
                                    send_command(f"UPDATE_PLAYER_SCORE_{player_score}")
                                elif winner == "COMPUTER":
                                    computer_score += 1
                                    send_command(f"UPDATE_COMPUTER_SCORE_{computer_score}")
                                
                                # Check if game is over
                                if player_score == 3 or computer_score == 3:
                                    winner_text = "PLAYER WINS!" if player_score == 3 else "COMPUTER WINS!"
                                    send_command(f"GAME_OVER_{winner_text}")
                                    player_score = 0
                                    computer_score = 0
                                
                                last_gesture_time = current_time
                            
                            except Exception as e:
                                print(f"Error sending commands: {e}")
                                # Attempt to reconnect
                                sock = connect_to_esp32()
            
            # Display game state
            cv2.putText(image, f"Player: {player_score} | Computer: {computer_score}", 
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            cv2.imshow('Rock Paper Scissors', image)
            
            if cv2.waitKey(5) & 0xFF == ord('q'):
                break
        
        except Exception as e:
            print(f"Unexpected error: {e}")
            # Attempt to reconnect
            sock = connect_to_esp32()
            time.sleep(1)  # Brief pause to prevent rapid reconnection attempts

    # Clean up
    if sock:
        sock.close()
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()