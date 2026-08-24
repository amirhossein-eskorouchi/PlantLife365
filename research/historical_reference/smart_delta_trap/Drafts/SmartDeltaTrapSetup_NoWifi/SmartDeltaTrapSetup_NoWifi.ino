#include <WiFi.h>
#include <WebServer.h>
#include <esp32cam.h>

const char* AP_SSID = "ESP32CAM1";
const char* AP_PASS = "siolLab";

IPAddress local_ip(192,168,1,1);
IPAddress gateway(192,168,1,1);
IPAddress subnet(255,255,255,0);

WebServer server(80);

static auto hiRes = esp32cam::Resolution::find(800, 600);
static auto midRes = esp32cam::Resolution::find(320, 240);
static auto loRes = esp32cam::Resolution::find(160, 120);

void serveJpg()
{
  auto frame = esp32cam::capture();
  if (!frame) {
    Serial.println("Capture failed");
    server.send(503, "", "");
    return;
  }

  server.sendHeader("Content-Type", "image/jpeg");
  server.sendHeader("Content-Length", String(frame->size()));
  server.send(200);
  WiFiClient client = server.client();
  frame->writeTo(client);
}

void handleJpgHi() { esp32cam::Camera.changeResolution(hiRes); serveJpg(); }
void handleJpgMid() { esp32cam::Camera.changeResolution(midRes); serveJpg(); }
void handleJpgLo() { esp32cam::Camera.changeResolution(loRes); serveJpg(); }

void setup() {
  Serial.begin(9600);
  Serial.println();

  using namespace esp32cam;
  Config cfg;
  cfg.setPins(pins::AiThinker);
  cfg.setResolution(hiRes);
  cfg.setBufferCount(2);
  cfg.setJpeg(80);
  bool ok = Camera.begin(cfg);
  Serial.println(ok ? "Camera OK" : "Camera FAIL");

  WiFi.mode(WIFI_AP);
  WiFi.softAPConfig(local_ip, gateway, subnet);
  WiFi.softAP(AP_SSID, AP_PASS);

  delay(500);
  Serial.print("AP IP address: ");
  Serial.println(WiFi.softAPIP());

  server.on("/cam-lo.jpg", handleJpgLo);
  server.on("/cam-mid.jpg", handleJpgMid);
  server.on("/cam-hi.jpg", handleJpgHi);

  server.begin();
  Serial.println("HTTP server started");
  Serial.println("Connect to Wi-Fi: ESP32CAM1");
  Serial.println("Then open:");
  Serial.println("  http://192.168.1.1/cam-lo.jpg");
  Serial.println("  http://192.168.1.1/cam-mid.jpg");
  Serial.println("  http://192.168.1.1/cam-hi.jpg");
}

void loop() {
  server.handleClient();
}
