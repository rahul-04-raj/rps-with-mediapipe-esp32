#include <WiFi.h>
#include <Wire.h>
#include <LiquidCrystal_PCF8574.h>

const char* ssid = "ESP32-RPS-Game";
const char* password = "12345678";
WiFiServer server(8080);
WiFiClient client;

// LED Pin Assignments
const int ROCK_PLAYER_LED1 = 16;
const int ROCK_COMPUTER_LED2 = 17;
const int PAPER_PLAYER_LED1 = 18;
const int PAPER_COMPUTER_LED2 = 19;
const int SCISSORS_PLAYER_LED1 = 25;
const int SCISSORS_COMPUTER_LED2 = 26;

// LCD Initialization
LiquidCrystal_PCF8574 lcd(0x27);

// Global variables for tracking scores
int playerScore = 0;
int computerScore = 0;

void setup() {
  Serial.begin(115200);

  lcd.begin(16, 2);
  lcd.setBacklight(255);
  lcd.setCursor(0, 0);
  lcd.print("Rock Paper");
  lcd.setCursor(0, 1);
  lcd.print("Scissors Game");

  // Initialize LED Pins
  pinMode(ROCK_PLAYER_LED1, OUTPUT);
  pinMode(ROCK_COMPUTER_LED2, OUTPUT);
  pinMode(PAPER_PLAYER_LED1, OUTPUT);
  pinMode(PAPER_COMPUTER_LED2, OUTPUT);
  pinMode(SCISSORS_PLAYER_LED1, OUTPUT);
  pinMode(SCISSORS_COMPUTER_LED2, OUTPUT);

  // WiFi Access Point
  WiFi.softAP(ssid, password);
  IPAddress IP = WiFi.softAPIP();
  Serial.print("AP IP address: ");
  Serial.println(IP);

  // Start TCP server
  server.begin();
}

void resetAllLEDs() {
  digitalWrite(ROCK_PLAYER_LED1, LOW);
  digitalWrite(ROCK_COMPUTER_LED2, LOW);
  digitalWrite(PAPER_PLAYER_LED1, LOW);
  digitalWrite(PAPER_COMPUTER_LED2, LOW);
  digitalWrite(SCISSORS_PLAYER_LED1, LOW);
  digitalWrite(SCISSORS_COMPUTER_LED2, LOW);
}

void updateScoreDisplay() {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("P:" + String(playerScore) + " C:" + String(computerScore));
}

void gameOverDisplay(String winner) {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print(winner);
  delay(3000);  // Show winner for 3 seconds
  playerScore = 0;
  computerScore = 0;
  updateScoreDisplay();
}

void loop() {
  if (!client.connected()) {
    client = server.available();
    if (client) {
      Serial.println("New client connected");
    }
  }

  if (client && client.connected()) {
    if (client.available()) {
      String command = client.readStringUntil('\n');
      command.trim();

      Serial.println("Received: " + command);

      // Player Gesture LEDs
      if (command == "PLAYER_ROCK") {
        resetAllLEDs();
        digitalWrite(ROCK_PLAYER_LED1, HIGH);
        client.println("ROCK_ACK");
      }
      else if (command == "PLAYER_PAPER") {
        resetAllLEDs();
        digitalWrite(PAPER_PLAYER_LED1, HIGH);
        client.println("PAPER_ACK");
      }
      else if (command == "PLAYER_SCISSORS") {
        resetAllLEDs();
        digitalWrite(SCISSORS_PLAYER_LED1, HIGH);
        client.println("SCISSORS_ACK");
      }
      else if (command == "COMPUTER_SCISSORS") {
        digitalWrite(SCISSORS_COMPUTER_LED2, HIGH);
        client.println("SCISSORS_ACK");
      }
      else if (command == "COMPUTER_ROCK") {
        digitalWrite(ROCK_COMPUTER_LED2, HIGH);
        client.println("ROCK_ACK");
      }
      else if (command == "COMPUTER_PAPER") {
        digitalWrite(PAPER_COMPUTER_LED2, HIGH);
        client.println("PAPER_ACK");
      }

      // Score Update Commands (Fix applied)
      else if (command.startsWith("UPDATE_PLAYER_SCORE_")) {
        playerScore = command.substring(20).toInt();
        updateScoreDisplay();
        client.println("PLAYER_SCORE_ACK");
      }
      else if (command.startsWith("UPDATE_COMPUTER_SCORE_")) {
        computerScore = command.substring(22).toInt();
        updateScoreDisplay();
        client.println("COMPUTER_SCORE_ACK");
      }

      // Game Over Command
      else if (command.startsWith("GAME_OVER_")) {
        String winner = command.substring(10);
        gameOverDisplay(winner);
        client.println("GAME_OVER_ACK");
      }
    }
  }

  delay(10);
}