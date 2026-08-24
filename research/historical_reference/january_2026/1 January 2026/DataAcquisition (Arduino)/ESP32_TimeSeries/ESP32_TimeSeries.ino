// Libraries
#include <DHT.h>
#include <WiFi.h>
#include <esp32cam.h>
// Variables
#define lightPin   0
#define DHT11_PIN  15
DHT dht11(DHT11_PIN, DHT11);
unsigned long lastRead = 0;
void setup() {
  // Sensors setup
  Serial.begin(115200);
  dht11.begin();
  pinMode(lightPin, INPUT);
  // Headers
  Serial.println("=== ESP32 Sensor Time Series ===");
  Serial.println("TIMESTAMP(ms),TEMPERATURE(°C),HUMIDITY(%),LIGHT(0-4095)");
}
void loop() {
  unsigned long now = millis();
  if (now - lastRead >= 500) {
    // Values
    lastRead = now;
    float tempC = dht11.readTemperature();
    float humi  = dht11.readHumidity();
    float light = analogRead(lightPin);
    // Output
    Serial.print(now);
    Serial.print(",");
    Serial.print(tempC);
    Serial.print(",");
    Serial.print(humi);
    Serial.print(",");
    Serial.println(light);
    }
  }
