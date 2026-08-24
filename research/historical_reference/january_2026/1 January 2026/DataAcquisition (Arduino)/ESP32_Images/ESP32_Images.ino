// Libraries
#include <esp32cam.h>
#include <WebServer.h>
#include <WiFi.h>
#include <DHT.h>

// Usernames
#define AP_SSID "Ethan"
#define AP_PASS "siol"
WebServer server(80);
#define lightPin   0
#define DHT11_PIN  15
DHT dht11(DHT11_PIN, DHT11);

// Stream
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

// Setup
void setup() {
  Serial.begin(115200);
  dht11.begin();
  pinMode(lightPin, INPUT);
  
  auto res = esp32cam::Resolution::find(640, 480);
  esp32cam::Config cfg;
  cfg.setPins(esp32cam::pins::AiThinker);
  cfg.setResolution(res);
  cfg.setJpeg(80);
  esp32cam::Camera.begin(cfg);
  WiFi.softAP(AP_SSID, AP_PASS);
  server.on("/stream", handleStream);
  server.begin();
}

// Loop
void loop() { 
  server.handleClient();
}
