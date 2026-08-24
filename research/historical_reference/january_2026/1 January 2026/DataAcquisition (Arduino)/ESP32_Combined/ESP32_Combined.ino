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
    delay(10);
  }
}

void handleMainPage() {
  String html = "<!DOCTYPE html><html><head><meta charset='UTF-8'><title>ESP32 Cam&Sensors</title>"
  "<style>body{font-family:Arial;margin:20px;}.value{font-weight:bold;color:#f00;font-size:1.2em;}"
  ".container{display:flex;flex-wrap:wrap;gap:20px;align-items:flex-start;}"
  ".block{border:1px solid#ccc;padding:15px;border-radius:8px;flex:1;min-width:300px;}"
  "img{max-width:100%;height:auto;border-radius:4px;}</style></head>"
  "<body><h1>ESP32 Camera & Sensors</h1><div class='container'>"
  "<div class='block'><h2>📹 Live Stream</h2><img id='stream' src='/stream' alt='Camera'></div>"
  "<div class='block'><h2>📊 Current Values</h2>"
  "<p>🌡Temp: <span id='tempC' class='value'>--</span>°C</p>"
  "<p>💧Humidity: <span id='humi' class='value'>--</span>%</p>"
  "<p>Light: <span id='light' class='value'>--</span></p></div></div>"
  "<script>const es=new EventSource('/signals');"
  "es.onmessage=function(e){const p=e.data.split(',');"
  "if(p.length==3){document.getElementById('tempC').textContent=p[0];"
  "document.getElementById('humi').textContent=p[1];"
  "document.getElementById('light').textContent=p[2];}}</script></body></html>";
  server.send(200, "text/html", html);
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
  server.on("/", handleMainPage);
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
