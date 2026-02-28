#include <WiFi.h>
#include <WebServer.h>
#include <ESPmDNS.h>

const char* ssid = "PRAVEENARCHER";
const char* password = "RP@30032019";

WebServer server(80);

void handleMessage() {
  if (server.hasArg("text")) {
    String msg = server.arg("text");
    Serial.println("Received from Pi:");
    Serial.println(msg);
    server.send(200, "text/plain", "Message received: " + msg);
  } else {
    server.send(400, "text/plain", "Missing text parameter");
  }
}

void setup() {
  Serial.begin(115200);
  delay(2000);

  Serial.println("Booting...");

  WiFi.mode(WIFI_STA);
  WiFi.setHostname("esp-mdr");   // DHCP hostname
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nConnected!");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());

  // 🔥 Start mDNS AFTER WiFi connected
  if (MDNS.begin("esp-mdr")) {
    Serial.println("mDNS responder started");
  } else {
    Serial.println("Error setting up mDNS!");
  }

  server.on("/", []() {
    server.send(200, "text/plain", "ESP32 is alive");
  });

  server.on("/message", handleMessage);

  server.begin();
  Serial.println("HTTP server started");
}

void loop() {
  server.handleClient();
}