#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_ADXL345_U.h>

// ADXL345 object
Adafruit_ADXL345_Unified accel = Adafruit_ADXL345_Unified();

// HW-036 sensor pin
const int sensorPin = 2;
int sensorValue = 0;

void setup() {
  Serial.begin(9600);
  pinMode(sensorPin, INPUT);
  Serial.println("HW-036 + ADXL345 Sensor Test");

  // Initialize ADXL345
  if (!accel.begin()) {
    Serial.println("Could not find ADXL345 sensor!");
    while (1);  // Halt here
  }
  accel.setRange(ADXL345_RANGE_16_G);
  Serial.println("ADXL345 initialized!");
  delay(1000);
}

void loop() {
  // Read HW-036 digital sensor
  sensorValue = digitalRead(sensorPin);

  // Read accelerometer data
  sensors_event_t event;
  accel.getEvent(&event);

  // Print all data in CSV: HW036,AccelX,AccelY,AccelZ
  Serial.print(sensorValue);
  Serial.print(",");
  Serial.print(event.acceleration.x);
  Serial.print(",");
  Serial.print(event.acceleration.y);
  Serial.print(",");
  Serial.println(event.acceleration.z);

  delay(500);
}
