#include <Arduino.h>
#include <PubSubClient.h>
#include <WiFi.h>

#define PWR_PIN 4
#define FW_TAG "ORION_MQTT_ONLY_2026_03_01_D"

const char *ssid = "PRAVEENARCHER";
const char *password = "RP@30032019";
const char *hostname = "esp-mdr";

const char *mqttBroker = "192.168.0.103";
const uint16_t mqttPort = 1883;
const char *mqttClientId = "esp32-mdr";

const char *mqttCmdTopic = "orion/pc/cmd";
const char *mqttStatusTopic = "orion/pc/status";

const unsigned long defaultPulseMs = 500;
const unsigned long forceOffPulseMs = 5000;
const unsigned long maxPulseMs = 8000;

const unsigned long mqttRetryMs = 3000;
const unsigned long wifiRetryMs = 5000;

WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);

bool pulseActive = false;
unsigned long pulseStart = 0;
unsigned long pulseDuration = defaultPulseMs;

unsigned long lastMqttAttempt = 0;
unsigned long lastWifiAttempt = 0;

// ------------------------------------------------------------
// Publish transient event (non-retained)
// ------------------------------------------------------------
void publishEvent(const char *msg) {
  if (mqttClient.connected()) {
    mqttClient.publish(mqttStatusTopic, msg, false);
  }
}

// ------------------------------------------------------------
// Power pulse
// ------------------------------------------------------------
void startPulse(unsigned long durationMs) {

  if (pulseActive) {
    publishEvent("pulse_busy");
    return;
  }

  if (durationMs == 0 || durationMs > maxPulseMs) {
    durationMs = defaultPulseMs;
  }

  pulseDuration = durationMs;
  pulseStart = millis();
  pulseActive = true;

  pinMode(PWR_PIN, OUTPUT);
  digitalWrite(PWR_PIN, HIGH);

  publishEvent("pulse_started");
}

// ------------------------------------------------------------
// Command handler
// ------------------------------------------------------------
void handleCommand(const String &rawCmd) {

  String cmd = rawCmd;
  cmd.trim();
  cmd.toLowerCase();

  if (cmd == "pc/on_or_off" || cmd == "pc/on" || cmd == "power/on" ) {
    startPulse(defaultPulseMs);
    return;
  }

  if (cmd == "pc/forceoff" || cmd == "forceoff") {
    startPulse(forceOffPulseMs);
    return;
  }

  if (cmd.startsWith("pc/pulse/")) {
    unsigned long ms = static_cast<unsigned long>(cmd.substring(9).toInt());
    startPulse(ms);
    return;
  }

  publishEvent("unknown_command");
}

// ------------------------------------------------------------
// MQTT callback
// ------------------------------------------------------------
void mqttCallback(char *topic, byte *payload, unsigned int length) {

  String msg;
  msg.reserve(length);

  for (unsigned int i = 0; i < length; ++i) {
    msg += static_cast<char>(payload[i]);
  }

  handleCommand(msg);
}

// ------------------------------------------------------------
// MQTT reconnect
// ------------------------------------------------------------
void connectMqttIfNeeded() {

  if (mqttClient.connected() || WiFi.status() != WL_CONNECTED) {
    return;
  }

  const unsigned long now = millis();
  if (now - lastMqttAttempt < mqttRetryMs) {
    return;
  }
  lastMqttAttempt = now;

  if (mqttClient.connect(
        mqttClientId,
        mqttStatusTopic,
        0,
        true,
        "esp32_offline"   // LWT retained
      )) {

    mqttClient.subscribe(mqttCmdTopic);

    mqttClient.publish(mqttStatusTopic, "esp32_online", true);
  }
}

// ------------------------------------------------------------
// WiFi reconnect
// ------------------------------------------------------------
void connectWiFiIfNeeded() {

  if (WiFi.status() == WL_CONNECTED) {
    return;
  }

  const unsigned long now = millis();
  if (now - lastWifiAttempt < wifiRetryMs) {
    return;
  }
  lastWifiAttempt = now;

  WiFi.begin(ssid, password);
}

// ------------------------------------------------------------
// Setup
// ------------------------------------------------------------
void setup() {

  pinMode(PWR_PIN, OUTPUT);
  digitalWrite(PWR_PIN, LOW);
  pinMode(PWR_PIN, INPUT);  // tri-state for safety

  Serial.begin(115200);
  delay(50);
  Serial.printf("FW: %s\n", FW_TAG);

  WiFi.mode(WIFI_STA);
  WiFi.setHostname(hostname);
  WiFi.begin(ssid, password);

  mqttClient.setServer(mqttBroker, mqttPort);
  mqttClient.setCallback(mqttCallback);

  mqttClient.setKeepAlive(30);
  mqttClient.setSocketTimeout(3);
}

// ------------------------------------------------------------
// Main loop
// ------------------------------------------------------------
void loop() {

  connectWiFiIfNeeded();
  connectMqttIfNeeded();

  if (mqttClient.connected()) {
    mqttClient.loop();
  }

  if (pulseActive && (millis() - pulseStart >= pulseDuration)) {
    digitalWrite(PWR_PIN, LOW);
    pinMode(PWR_PIN, INPUT);  // tri-state after pulse
    pulseActive = false;
    publishEvent("pulse_complete");
  }
}