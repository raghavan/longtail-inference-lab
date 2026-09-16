// AtomS3-Lite: USB button and status LED only. No Wi-Fi/Bluetooth initialization.
// Pin reference: https://docs.m5stack.com/en/core/AtomS3%20Lite
#include <Arduino.h>
#include <Adafruit_NeoPixel.h>

constexpr uint8_t BUTTON_PIN = 41;
constexpr uint8_t RGB_PIN = 35;
Adafruit_NeoPixel pixel(1, RGB_PIN, NEO_GRB + NEO_KHZ800);
bool previousSample = HIGH;
bool stable = HIGH;
unsigned long changedAt = 0;
unsigned long lastStateAt = 0;
String input;

void color(uint8_t r, uint8_t g, uint8_t b) {
  pixel.setPixelColor(0, pixel.Color(r, g, b));
  pixel.show();
}

void showState(const String &state) {
  if (state == "ready") color(0, 32, 0);
  else if (state == "recording") color(40, 0, 0);
  else if (state == "speaking") color(0, 24, 32);
  else if (state == "error") color(40, 0, 40);
  else color(32, 20, 0);
}

void setup() {
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  pixel.begin();
  color(8, 8, 8); // Connected to power; waiting for the Linux application.
  Serial.begin(115200);
  input.reserve(80);
}

void loop() {
  const unsigned long now = millis();
  bool sample = digitalRead(BUTTON_PIN);
  if (sample != previousSample) {
    changedAt = now;
    previousSample = sample;
  }
  if (now - changedAt >= 35 && sample != stable) {
    stable = sample;
    if (stable == LOW && Serial) Serial.println("PRESS");
  }
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n') {
      input.trim();
      if (input.startsWith("STATE ")) {
        showState(input.substring(6));
        lastStateAt = now;
      }
      input = "";
    } else if (input.length() < 79) {
      input += c;
    } else {
      input = "";
    }
  }
  // Linux sends a heartbeat. A stale LED must not imply active recording.
  if (now - lastStateAt > 5000) color(8, 8, 8);
  delay(2);
}
