#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include <ESPmDNS.h>

#define PWR_PIN 4

// -------- WIFI CONFIG ----------
const char *ssid = "PRAVEENARCHER";
const char *password = "RP@30032019";
const char* hostname = "esp-mdr";

// -------- WEB SERVER ----------
WebServer server(80);

// -------- POWER CONTROL ----------
bool pulseActive = false;
unsigned long pulseStart = 0;
unsigned long pulseDuration = 500;
const unsigned long maxPulseDuration = 8000;

// ---------- POWER FUNCTION ----------
void startPulse(unsigned long durationMs) {
  if (pulseActive) return;

  if (durationMs == 0 || durationMs > maxPulseDuration)
    durationMs = 500;

  pulseDuration = durationMs;
  pulseStart = millis();
  pulseActive = true;

  digitalWrite(PWR_PIN, HIGH);
}

// ---------- WEB HANDLERS ----------
void handleRoot() {
  server.send(200, "text/plain", "ORION ESP32 Power Controller Ready");
}

void handlePowerOn() {
  startPulse(500);
  server.send(200, "text/plain", "Power pulse 500ms triggered");
}

void handleForceOff() {
  startPulse(5000);
  server.send(200, "text/plain", "Force shutdown pulse triggered");
}

void handleCustomPulse() {
  if (server.hasArg("ms")) {
    unsigned long duration = server.arg("ms").toInt();
    startPulse(duration);
    server.send(200, "text/plain", "Custom pulse triggered");
    return;
  }
  server.send(400, "text/plain", "Missing ms parameter");
}

void handleStatus() {
  String status = pulseActive ? "PULSE_ACTIVE" : "IDLE";
  server.send(200, "text/plain", status);
}

// ---------- SETUP ----------
void setup() {

  pinMode(PWR_PIN, OUTPUT);
  digitalWrite(PWR_PIN, LOW);   // Safe boot state

  Serial.begin(115200);
  delay(100);

  WiFi.mode(WIFI_STA);
  WiFi.setHostname(hostname);   // DHCP hostname
  WiFi.begin(ssid, password);

  Serial.print("Connecting to WiFi");

  unsigned long wifiStart = millis();
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    if (millis() - wifiStart > 20000) break;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nConnected!");
    Serial.print("IP Address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\nWiFi Failed.");
  }

  // -------- mDNS START ----------
  if (MDNS.begin(hostname)) {
    Serial.println("mDNS responder started");
    MDNS.addService("http", "tcp", 80);
  } else {
    Serial.println("Error setting up mDNS responder!");
  }

  // Routes
  server.on("/", handleRoot);
  server.on("/pc/on", handlePowerOn);
  server.on("/pc/forceoff", handleForceOff);
  server.on("/pc/pulse", handleCustomPulse);
  server.on("/status", handleStatus);

  server.begin();
  Serial.println("Webserver started.");
}

// ---------- LOOP ----------
void loop() {

  server.handleClient();

  if (pulseActive && (millis() - pulseStart >= pulseDuration)) {
    digitalWrite(PWR_PIN, LOW);
    pulseActive = false;
  }
}