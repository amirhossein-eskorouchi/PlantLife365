/* Imported libraries */
#include <WiFi.h>
#include <WebServer.h>
#include <esp32cam.h>
#include <DHT.h>

/* Wi-Fi Access Point configuration */
const char* AP_SSID = "Ethan";
const char* AP_PASS = "siolLab";

/* WebServer on port 80 */
WebServer server(80);

/* Camera resolutions */
static auto midRes = esp32cam::Resolution::find(200, 200);

/* DHT11 setup */
#define DHT11_PIN 15
DHT dht11(DHT11_PIN, DHT11);

/* Serve camera frame */
void serveJpg()
{
  auto frame = esp32cam::capture();
  if (!frame) {
    Serial.println("Capture failed");
    server.send(503, "text/plain", "Capture failed");
    return;
  }
  server.sendHeader("Content-Type", "image/jpeg");
  server.sendHeader("Content-Length", String(frame->size()));
  server.send(200);
  WiFiClient client = server.client();
  frame->writeTo(client);
}

/* Handlers for different resolutions */
void handleJpgMid() { 
  esp32cam::Camera.changeResolution(midRes); 
  serveJpg();
  }

/* Handle temperature and humidity signals */
void handleSignals() {
  float tempC = dht11.readTemperature();
  float humi  = dht11.readHumidity();
  String data = String(tempC) + "," + String(humi);
  server.send(200, "text/plain", data);
}

void setup() {
  Serial.begin(9600);
  dht11.begin();

  /* Initialize camera */
  using namespace esp32cam;
  Config cfg;
  cfg.setPins(pins::AiThinker);
  cfg.setResolution(midRes);
  cfg.setBufferCount(1);
  cfg.setJpeg(50);
  bool ok = Camera.begin(cfg);
  Serial.println(ok ? "Camera OK" : "Camera FAIL");
  
  /* Start access point */
  WiFi.mode(WIFI_AP);
  WiFi.softAP(AP_SSID, AP_PASS);
  delay(500);

  /* Ready to connect */
  Serial.println("Connect to ESP32");
  Serial.println("Then open:");
  Serial.println("http://" + WiFi.softAPIP().toString() + "/cam-mid.jpg");
  Serial.println("http://" + WiFi.softAPIP().toString() + "/signals");

  /* Configure routes */
  server.on("/cam-mid.jpg", handleJpgMid);
  server.on("/signals", handleSignals);
  server.begin();
}

void loop() {
  server.handleClient();
  delay(1);
}
