/* Imported libraries */
#include <WiFi.h>
#include <WebServer.h>
#include <esp32cam.h>
#include <DHT.h>

/* Wi-Fi Access Point configuration */
const char* AP_SSID = "ESP32CAM";
const char* AP_PASS = "siolLab";

/* WebServer on port 80 */
WebServer server(80);

/* Camera resolutions */
//static auto hiRes = esp32cam::Resolution::find(800, 600);
static auto midRes = esp32cam::Resolution::find(320, 240);
//static auto loRes  = esp32cam::Resolution::find(160, 120);

/* DHT11 setup */
#define DHT11_PIN 15
DHT dht11(DHT11_PIN, DHT11);

/* Soil Moisture setup */
const int AOUT_PIN = 23;

/* Geiger Counter setup */
const int GEIGER_PIN = 36;
volatile unsigned long pulseCount = 0;
unsigned long lastMeasureMillis = 0;
const unsigned long measureInterval = 5000;

// Conversion factor (rough for SBM‑20, adjust after calibration): µSv/h = CPS * 0.57
const float CPS_TO_USVH = 0.57f;
void IRAM_ATTR handleGeigerPulse() { pulseCount++; }

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
//void handleJpgHi()  { esp32cam::Camera.changeResolution(hiRes); serveJpg(); }
void handleJpgMid() { esp32cam::Camera.changeResolution(midRes); serveJpg(); }
//void handleJpgLo()  { esp32cam::Camera.changeResolution(loRes); serveJpg(); }

/* Handle temperature and humidity signals */
void handleSignals() {
  float tempC = dht11.readTemperature();
  float humi  = dht11.readHumidity();
  int soilMoist = analogRead(AOUT_PIN);

  unsigned long now = millis();
  if (now - lastMeasureMillis >= measureInterval) {
    // Copy and reset count atomically
    noInterrupts();
    unsigned long counts = pulseCount;
    pulseCount = 0;
    interrupts();
    // Counts per second
    float cps = counts * 1000.0f / (now - lastMeasureMillis);
    // Counts per minute
    float cpm = cps * 60.0f;
    // Approximate dose rate in µSv/h
    float uSv_h = cps * CPS_TO_USVH;

  String data = String(tempC) + "," + String(humi) + "," + String(soilMoist) + "," + String(uSv_h);
  lastMeasureMillis = now;
  
  server.send(200, "text/plain", data);
  }
}

void setup() {
  Serial.begin(2000000);
  delay(5000);

  /* Sensors */
  dht11.begin();
  pinMode(GEIGER_PIN, INPUT);
  attachInterrupt(digitalPinToInterrupt(GEIGER_PIN), handleGeigerPulse, RISING);
  lastMeasureMillis = millis();

  /* Initialize camera */
  using namespace esp32cam;
  Config cfg;
  cfg.setPins(pins::AiThinker);
  cfg.setResolution(midRes);
  cfg.setBufferCount(2);
  cfg.setJpeg(80);
  bool ok = Camera.begin(cfg);
  Serial.println(ok ? "Camera OK" : "Camera FAIL");
  
  /* Start access point */
  WiFi.mode(WIFI_AP);
  WiFi.softAP(AP_SSID, AP_PASS);

  /* Ready to connect */
  Serial.println("Connect to ESP32CAM");
  Serial.println("Then open:");
  //Serial.println("http://" + WiFi.softAPIP().toString() + "/cam-lo.jpg");
  Serial.println("http://" + WiFi.softAPIP().toString() + "/cam-mid.jpg");
  //Serial.println("http://" + WiFi.softAPIP().toString() + "/cam-hi.jpg");
  Serial.println("http://" + WiFi.softAPIP().toString() + "/signals");

  /* Configure routes */
  //server.on("/cam-lo.jpg", handleJpgLo);
  server.on("/cam-mid.jpg", handleJpgMid);
  //server.on("/cam-hi.jpg", handleJpgHi);
  server.on("/signals", handleSignals);
  server.begin();
}

void loop() {
  server.handleClient();
}
