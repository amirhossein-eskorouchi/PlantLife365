#include <esp32cam.h>
#include <WebServer.h>
#include <WiFi.h>

#define AP_SSID "Ethan"
#define AP_PASS "siol"
WebServer server(80);

void handleStream() {
  WiFiClient client = server.client();

  client.print(
    "HTTP/1.1 200 OK\r\n"
    "Content-Type: multipart/x-mixed-replace; boundary=frame\r\n"
    "Connection: close\r\n\r\n"
  );

  while (client.connected()) {
    auto img = esp32cam::capture();
    if (!img) {
      break;
    }

    client.print("--frame\r\n");
    client.print("Content-Type: image/jpeg\r\n");
    client.print("Content-Length: ");
    client.print(img->size());
    client.print("\r\n\r\n");

    img->writeTo(client);
    client.print("\r\n");
    delay(42);
  }
}

void setup() {
  auto res = esp32cam::Resolution::find(640, 480);
  esp32cam::Config cfg;
  cfg.setPins(esp32cam::pins::AiThinker);
  cfg.setResolution(res);
  cfg.setJpeg(80);
  esp32cam::Camera.begin(cfg);

  // 192.168.4.1
  WiFi.softAP(AP_SSID, AP_PASS);

  // single snapshot (keep if you still want it)
  //server.on("/capture.jpg", handleCapture);

  // continuous MJPEG stream
  server.on("/stream", handleStream);

  server.begin();
}

void loop() {
  server.handleClient();
}

/*
void handleCapture() {
  auto img = esp32cam::capture();
  
  if (img == nullptr) {
    server.send(500, "", "");
    return;
  }

  server.setContentLength(img->size());
  server.send(200, "image/jpeg");
  WiFiClient client = server.client();
  img->writeTo(client);
}
*/

/*
#define lightPin 35
void setup() {
  // Initialize serial communication at 115200 bits per second:
  Serial.begin(115200);
}

void loop() {
  // Read the analog value
  int analogValue = analogRead(lightPin);
  
  // Print out the values
  Serial.printf("Analog value = %d\n",analogValue);
  
  delay(300);  // delay between reads for clear read from serial monitor
}
*/

/*
#include <DHT.h>
#define DHT11_PIN 21
DHT dht11(DHT11_PIN, DHT11);

void setup() {
  Serial.begin(115200);
  dht11.begin();
}

void loop() {
  float humi  = dht11.readHumidity();
  float tempC = dht11.readTemperature();
  float tempF = dht11.readTemperature(true);

  // check whether the reading is successful or not
  if ( isnan(tempC) || isnan(tempF) || isnan(humi)) {
    Serial.println("Failed to read from DHT11 sensor!");
  } else {
    Serial.print("Humidity: ");
    Serial.print(humi);
    Serial.print("%");

    Serial.print("  |  ");

    Serial.print("Temperature: ");
    Serial.print(tempC);
    Serial.print("°C  ~  ");
    Serial.print(tempF);
    Serial.println("°F");
  }

  // wait a 2 seconds between readings
  delay(2000);
}
*/
