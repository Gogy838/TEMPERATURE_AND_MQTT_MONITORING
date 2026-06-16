# Wiring reference

## LM35 temperature sensor → Arduino Uno

```
LM35 (flat side facing you)
 ┌─────────────┐
 │ VCC  OUT GND│
 └──┬────┬───┬─┘
    │    │   │
   5V   A0  GND
```

| LM35 | Arduino Uno |
|------|-------------|
| VCC  | 5V          |
| OUT  | A0          |
| GND  | GND         |

> The LM35 outputs 10 mV per °C. At 25 °C it outputs 250 mV.
> Do NOT use 3.3V — the LM35 needs 5V for accurate readings.

---

## 16×2 LCD with I2C backpack → Arduino Uno

```
I2C backpack pins
┌──────────────────┐
│ GND VCC SDA SCL  │
└──┬────┬───┬───┬──┘
   │    │   │   │
  GND  5V  A4  A5
```

| LCD I2C | Arduino Uno |
|---------|-------------|
| GND     | GND         |
| VCC     | 5V          |
| SDA     | A4          |
| SCL     | A5          |

> If the display is blank (backlight on, no characters), adjust
> the contrast potentiometer on the back of the I2C backpack
> with a small screwdriver.

> If you get compile errors, the I2C address may be 0x3F instead
> of 0x27. Change LCD_ADDR in the sketch and re-upload.

---

## Finding your LCD I2C address

Upload the I2C scanner sketch below to detect the address:

```cpp
#include <Wire.h>
void setup() {
  Wire.begin();
  Serial.begin(9600);
  Serial.println("I2C scanner");
  for (byte addr = 1; addr < 127; addr++) {
    Wire.beginTransmission(addr);
    if (Wire.endTransmission() == 0) {
      Serial.print("Found device at 0x");
      Serial.println(addr, HEX);
    }
  }
}
void loop() {}
```

---

## Full wiring diagram (text)

```
Arduino Uno
 ┌──────────────────────────────┐
 │                          5V  ├──┬──────────────────── LM35 VCC
 │                              │  └──────────────────── LCD VCC
 │                         GND  ├──┬──────────────────── LM35 GND
 │                              │  └──────────────────── LCD GND
 │                          A0  ├────────────────────── LM35 OUT
 │                          A4  ├────────────────────── LCD SDA
 │                          A5  ├────────────────────── LCD SCL
 │                              │
 │                    USB port  ├────────────────────── PC (serial)
 └──────────────────────────────┘
```
