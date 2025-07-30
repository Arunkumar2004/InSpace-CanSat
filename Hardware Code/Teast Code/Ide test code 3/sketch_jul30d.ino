#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_ADXL345_U.h>

Adafruit_ADXL345_Unified accel = Adafruit_ADXL345_Unified();

const int sensorPin = 2;
int sensorValue = 0;

void setup() {
  Serial.begin(9600);
  pinMode(sensorPin, INPUT);

  if (!accel.begin()) {
    Serial.println("Could not find ADXL345 sensor!");
    while (1);
  }
  accel.setRange(ADXL345_RANGE_16_G);
}

void loop() {
  sensorValue = digitalRead(sensorPin);

  sensors_event_t event;
  accel.getEvent(&event);

  // Dummy values for fields you don't have yet
  float voltage = 3.7;          // example battery voltage
  float gps_lat = 12.3456;      // dummy GPS latitude
  float gps_lon = 98.7654;      // dummy GPS longitude
  float altitude = 123.45;      // dummy altitude
  float temperature = 25.5;     // dummy temperature
  float pressure = 1013.25;     // dummy pressure
  float vertical_speed = 1.2;   // dummy vertical speed
  float current = 0.5;          // dummy current
  float battery = 95.0;         // dummy battery percentage
  String time = "12:30:15";     // dummy timestamp

  // CSV in GUI format
  Serial.print(voltage); Serial.print(",");
  Serial.print(gps_lat); Serial.print(",");
  Serial.print(gps_lon); Serial.print(",");
  Serial.print(altitude); Serial.print(",");
  Serial.print(temperature); Serial.print(",");
  Serial.print(pressure); Serial.print(",");
  Serial.print(vertical_speed); Serial.print(",");
  Serial.print(current); Serial.print(",");
  Serial.print(event.acceleration.x); Serial.print(",");
  Serial.print(event.acceleration.y); Serial.print(",");
  Serial.print(event.acceleration.z); Serial.print(",");
  Serial.print(battery); Serial.print(",");
  Serial.println(time);

  delay(500);
}
