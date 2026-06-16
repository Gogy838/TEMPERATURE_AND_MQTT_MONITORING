/*
 * Temperature Reading, LCD Display & Serial Transmission
 * Trade Code: SPE — Embedded Systems Software Integration
 *
 * Hardware:
 *   - Arduino Uno
 *   - LM35 temperature sensor  → Analog pin A0
 *   - 16x2 LCD (I2C, addr 0x27) via SDA=A4, SCL=A5
 *
 * Libraries required:
 *   - LiquidCrystal_I2C  (by Frank de Brabander)
 *   Install via: Sketch → Include Library → Manage Libraries
 */

#include <Wire.h>
#include <LiquidCrystal_I2C.h>

// ── Configuration ─────────────────────────────────────────────
#define SENSOR_PIN      A0          // LM35 analog input
#define BAUD_RATE       9600        // Serial communication speed
#define LCD_ADDR        0x27        // I2C address (try 0x3F if 0x27 fails)
#define LCD_COLS        16
#define LCD_ROWS        2
#define SCROLL_DELAY    350         // ms between scroll steps
#define READ_INTERVAL   1000        // ms between temperature readings

// Candidate name — change this to your actual name
const char CANDIDATE_NAME[] = "NIYONKURU Gloria";

// ── Global state ──────────────────────────────────────────────
LiquidCrystal_I2C lcd(LCD_ADDR, LCD_COLS, LCD_ROWS);

int    nameLength    = 0;
bool   nameScrolls   = false;        // true if name > 16 chars
int    scrollPos     = 0;            // current scroll offset
unsigned long lastScroll = 0;
unsigned long lastRead   = 0;
float  currentTemp   = 0.0;

// ── Setup ──────────────────────────────────────────────────────
void setup() {
  Serial.begin(BAUD_RATE);

  lcd.init();
  lcd.backlight();
  lcd.clear();

  nameLength  = strlen(CANDIDATE_NAME);
  nameScrolls = (nameLength > LCD_COLS);

  // Print static name if it fits; scrolling handled in loop()
  if (!nameScrolls) {
    lcd.setCursor(0, 0);
    lcd.print(CANDIDATE_NAME);
  }

  Serial.println("SPE Temperature Monitor started");
  Serial.println("topic: spe/temperature");
}

// ── Helpers ───────────────────────────────────────────────────

/*
 * Read LM35: output is 10 mV/°C.
 * Arduino Uno: 5 V reference, 1024 steps → 5000 mV / 1024 ≈ 4.883 mV/step
 * Temperature (°C) = analogRead × (5000 / 1024) / 10
 *                  = analogRead × 0.48828
 *
 * For DHT11 replace this function with DHT library calls.
 */
float readTemperature() {
  int raw = analogRead(SENSOR_PIN);
  float millivolts = raw * (5000.0 / 1024.0);
  return millivolts / 10.0;          // convert mV to °C
}

/*
 * Display one 16-character window of the candidate name, starting
 * at character index `scrollPos`.  Pads with spaces on the right
 * so leftover characters from a previous position are erased.
 */
void scrollName() {
  char window[LCD_COLS + 1];
  for (int i = 0; i < LCD_COLS; i++) {
    int idx = scrollPos + i;
    window[i] = (idx < nameLength) ? CANDIDATE_NAME[idx] : ' ';
  }
  window[LCD_COLS] = '\0';

  lcd.setCursor(0, 0);
  lcd.print(window);

  // Advance scroll position; wrap back after a full scroll + blank gap
  // Total scroll range: nameLength + LCD_COLS (creates blank-then-reappear effect)
  scrollPos++;
  if (scrollPos > nameLength) scrollPos = 0;
}

// ── Main loop ─────────────────────────────────────────────────
void loop() {
  unsigned long now = millis();

  // ── Scroll name on row 0 (if needed) ──────────────────────
  if (nameScrolls && (now - lastScroll >= SCROLL_DELAY)) {
    scrollName();
    lastScroll = now;
  }

  // ── Read & display temperature on row 1 ───────────────────
  if (now - lastRead >= READ_INTERVAL) {
    lastRead = now;

    currentTemp = readTemperature();

    // Format: "Temp: 25.60 C"
    lcd.setCursor(0, 1);
    lcd.print("Temp: ");
    lcd.print(currentTemp, 2);
    lcd.print(" C  ");           // trailing spaces clear stale digits

    // ── Serial transmission to PC ────────────────────────────
    // Format: plain numeric value, one reading per line
    // PC program reads this line and publishes to MQTT topic spe/temperature
    Serial.println(currentTemp, 2);
  }
}
