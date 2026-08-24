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
static auto midRes = esp32cam::Resolution::find(400, 400);

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

// Cached radiation values (updated periodically in loop)
volatile float lastCps = 0.0f;
volatile float lastUSvh = 0.0f;
volatile bool haveRadiation = false;

/* Serve camera frame */
void serveJpg() {
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
  // Read sensors quickly and return most recent cached radiation value
  float tempC = dht11.readTemperature();
  float humi  = dht11.readHumidity();
  int soilMoist = analogRead(AOUT_PIN);

  // Use the last computed radiation value (updated periodically in loop)
  float uSv_h = 0.0f;
  bool have = false;
  noInterrupts();
  have = haveRadiation;
  uSv_h = lastUSvh;
  interrupts();

  String data = String(tempC) + "," + String(humi) + "," + String(soilMoist) + "," + String(uSv_h);
  server.send(200, "text/plain", data);
}

void setup() {
  // Use a reliable baud rate for serial output
  Serial.begin(9600);
  delay(1000);

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
  cfg.setBufferCount(1);
  cfg.setJpeg(50);
  bool ok = Camera.begin(cfg);
  Serial.println(ok ? "Camera OK" : "Camera FAIL");
  
  /* Start access point */
  WiFi.mode(WIFI_AP);
  WiFi.softAP(AP_SSID, AP_PASS);

  /* Ready to connect */
  Serial.println("Connect to ESP32CAM");
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

  // Periodically compute radiation statistics without blocking request handling
  unsigned long now = millis();
  if (now - lastMeasureMillis >= measureInterval) {
    // Atomically copy & reset the pulse count
    noInterrupts();
    unsigned long counts = pulseCount;
    pulseCount = 0;
    interrupts();

    unsigned long elapsed = now - lastMeasureMillis;
    if (elapsed > 0) {
      float cps = (float)counts * 1000.0f / (float)elapsed; // counts per second
      float cpm = cps * 60.0f;
      float uSv_h = cps * CPS_TO_USVH;

      // store atomically for handler use
      noInterrupts();
      lastCps = cps;
      lastUSvh = uSv_h;
      haveRadiation = true;
      interrupts();

      Serial.printf("Geiger: counts=%lu elapsed_ms=%lu CPS=%.3f CPM=%.3f uSv/h=%.6f\n", counts, elapsed, cps, cpm, uSv_h);
    }

    lastMeasureMillis = now;
  }

  // Small yield to allow background tasks
  delay(1);
}
