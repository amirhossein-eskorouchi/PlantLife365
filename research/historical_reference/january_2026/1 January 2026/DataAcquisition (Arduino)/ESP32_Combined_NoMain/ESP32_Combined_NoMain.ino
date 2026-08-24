// Libraries
#include <esp32cam.h>
#include <WebServer.h>
#include <WiFi.h>
#include <DHT.h>

// Variables
#define AP_SSID "Ethan"
#define AP_PASS "siol"
#define lightPin 35
#define DHT11_PIN 23
DHT dht11(DHT11_PIN, DHT11);

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
    delay(100); // 10fps
  }
}

void handleSignals() {
  server.sendHeader("Content-Type", "text/event-stream");
  server.sendHeader("Cache-Control", "no-cache");
  server.sendHeader("Connection", "keep-alive");
  server.send(200);
  
  WiFiClient client = server.client();
  unsigned long lastSend = 0;
  
  while (client.connected()) {
    if (millis() - lastSend > 2000) {  // Send every 2s
      float tempC = dht11.readTemperature();
      float humi  = dht11.readHumidity();
      float light = analogRead(lightPin);
      
      client.printf("data: %.1f,%.1f,%.0f\n\n", tempC, humi, light);
      lastSend = millis();
    }
    yield();
    delay(100);
  }
}

void setup() {
  Serial.begin(115200);
  
  dht11.begin();

  // Camera setup
  auto res = esp32cam::Resolution::find(640, 480);
  esp32cam::Config cfg;
  cfg.setPins(esp32cam::pins::AiThinker);
  cfg.setResolution(res);
  cfg.setJpeg(80);
  esp32cam::Camera.begin(cfg);

  WiFi.softAP(AP_SSID, AP_PASS);
  Serial.print("AP IP: ");
  Serial.println(WiFi.softAPIP());

  // ALL ROUTES ENABLED
  server.on("/stream", handleStream);      // Infinite MJPEG stream
  server.on("/signals", handleSignals);    // Infinite SSE sensor stream
  server.begin();
  Serial.println("Server started");
}

void loop() {
  server.handleClient();
  yield();
  delay(1);
}
