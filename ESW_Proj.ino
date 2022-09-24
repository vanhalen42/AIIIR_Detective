#define TS_ENABLE_SSL // For HTTPS SSL connection

#include "Adafruit_SHT4x.h"
#include "PubSubClient.h"
#include "Adafruit_SGP40.h"
#include <WiFiClientSecure.h>
#include "ThingSpeak.h"
#include "HTTPClient.h"
#include "time.h"
#include <ArduinoJson.h>
#include <WebServer.h>
//
//#define WIFI_SSID "LANofTheFree"
//#define WIFI_PASS "Yashification9"
char WIFI_SSID[] = "AndroidAP";   // your network SSID (name) 
char WIFI_PASS[] = "aaron@monis";   // your network password
const char *server = "mqtt3.thingspeak.com";
char mqttUserName[] = "BwUMIQoAPAAdAw4RDCczCSc";
char mqttPass[] = "7sMniNbk3BvZR2iSCox27Wr6";
int writeChannelID = 1864875;
char writeAPIKey[] = "1FKWZ0DZM7T4STLD";

String cse_ip = "esw-onem2m.iiit.ac.in" ; // YOUR IP from ipconfig/ifconfig
String cse_port = "443";
String server_om2m = "https://" +  cse_ip + ":" + cse_port + "/~/in-cse/in-name/";
String ae = "Team-5";
String cnt = "Node-1/Data";
String cnt1 = "Node-2/Data";
String cnt2 = "Node-3/Data";
String cnt3 = "Node-4/Data";
String cnt4 = "Node-5/Data";
String cnt5 = "Node-6/Data";

WiFiClientSecure  client;
// PubSubClient mqttClient(espClient);

WiFiServer server1(80);

void ConnectToWifi(){
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID,WIFI_PASS);
  int start = millis();
  while(WiFi.status() != WL_CONNECTED){
    Serial.print(".");
    delay(100);
  }
}

void createCI(String val, String cont){
  HTTPClient http;
  http.begin(server_om2m + ae + "/" + cont + "/");
  http.addHeader("X-M2M-Origin", "K3iE!!:nOKfGx");
  http.addHeader("Content-Type", "application/json;ty=4");
  int code = http.POST("{\"m2m:cin\": {\"cnf\":\"application/json\",\"con\": " + String(val) + "}}");
  Serial.println(code);
  if (code == -1) {
    Serial.println("UNABLE TO CONNECT TO THE SERVER");
  }
  http.end();
}

#define PIN 12
unsigned long duration, th, tl;
int ppm;

void CO2_Reading(){
  th = pulseIn(PIN, HIGH, 2008000) / 1000;
  tl = 1004 - th;
  ppm = 2000 * (th - 2) / (th + tl - 4);
  
  String dataString3 = "field4=" + String(ppm);
  ThingSpeak.setField(3, ppm);

  createCI(String(ppm), cnt3);
}

Adafruit_SHT4x sht4 = Adafruit_SHT4x();

void SHT_setup(){
  if (! sht4.begin()) {
    Serial.println("Couldn't find SHT4x");
    while (! sht4.begin()) delay(1);
  }
  sht4.setPrecision(SHT4X_HIGH_PRECISION);
  sht4.setHeater(SHT4X_NO_HEATER);

}

Adafruit_SGP40 sgp;

void SGP_setup(){
  while (! sgp.begin()){
    Serial.println("Sensor not found :(");
  }
}

void SHT_SGP_Reading(){
  uint16_t raw;
  int32_t voc_index;
  
  raw = sgp.measureRaw();

  sensors_event_t humidity, temp;
  
  uint32_t timestamp = millis();
  sht4.getEvent(&humidity, &temp);// populate temp and humidity objects with fresh data
  timestamp = millis() - timestamp;

  String dataString = "field1=" + String(temp.temperature);
  ThingSpeak.setField(1, temp.temperature);
  String dataString1 = "field2=" + String(humidity.relative_humidity);
  ThingSpeak.setField(2, humidity.relative_humidity);

  createCI(String(temp.temperature), cnt);
  createCI(String(humidity.relative_humidity), cnt1);
  
  delay(1000);

  voc_index = sgp.measureVocIndex();

  String dataString2 = "field3=" + String(voc_index);
//  ThingSpeak.setField(3, voc_index);
  createCI(String(voc_index), cnt2);

  delay(1000);
}


unsigned long previous_loop, previous_10, previous_25, prev_time;

int pm2;
int pm10;
byte command_frame[9] = {0xAA, 0x02, 0x00, 0x00, 0x00, 0x00, 0x01, 0x67, 0xBB};
byte received_data[9];
int sum = 0;

void send_command(byte command)
{
  command_frame[1] = command;
  int sum = command_frame[0] + command_frame[1] + command_frame[2] + command_frame[3] + command_frame[4] + command_frame[5] + command_frame[8];
  int rem = sum % 256;
  command_frame[6] = (sum - rem) / 256;
  command_frame[7] = rem;
  delay(5000);
  Serial.write(command_frame, 9);

}

bool checksum()
{
  sum = int(received_data[0]) + int(received_data[1]) + int(received_data[2]) + int(received_data[3]) + int(received_data[4]) + int(received_data[5]) + int(received_data[8]);
  if (sum == ((int(received_data[6]) * 256) + int(received_data[7])))
  {
    return true;
  }
  else
    return false;
}
void calculate_pm()
{
  int pm2 = int(received_data[4]) * 256 + int(received_data[5]);
  delay(5000);
  int pm10 = int(received_data[2]) * 256 + int(received_data[3]);
  String dataString4 = "field5=" + String(pm2);
  ThingSpeak.setField(4, pm2);
  String dataString5 = "field6=" + String(pm10);
  ThingSpeak.setField(5, pm10);

  createCI(String(pm2), cnt4);
  createCI(String(pm10), cnt5);
  
  Serial.println(pm2);
  Serial.println(pm10);
}

void PM_setup(){
  send_command(0x01);
}

void PM_Reading(){
  delay(5000);
  if (millis() - prev_time > 5000)
  {
    send_command(0x02);
    prev_time = millis();
  }
  if (Serial.available())
  {
    Serial.readBytes(received_data, 9);
    if (checksum())
    {
      calculate_pm();
    }
  }
}

void setup() {
  Serial.begin(9600);  
  delay(5000);
  ConnectToWifi();
  ThingSpeak.begin(client);

  server1.begin();
  Serial.println("HTTP Server Started");
  
  SHT_setup();
  SGP_setup();
  PM_setup();
}

// void reconnect() {
//   while (!mqttClient.connected()) {
//     if (mqttClient.connect("BwUMIQoAPAAdAw4RDCczCSc", mqttUserName, mqttPass)) {
//     } else {
//       Serial.print("failed, rc=");
//       Serial.print(mqttClient.state());
//       Serial.println(" try again in 1 seconds");
//       delay(200);
//     }
//   }
// }
// void mqttPublish(String message) {
//   String topicString ="channels/" + String( writeChannelID ) + "/publish";
//   mqttClient.publish( topicString.c_str(), message.c_str() );
// }

int counter = 0;

int previousMillis = 0;

int interval = 15000;

void loop() {
  unsigned long currentMillis = millis();
  // if WiFi is down, try reconnecting every CHECK_WIFI_TIME seconds
  if ((WiFi.status() != WL_CONNECTED) && (currentMillis - previousMillis >=interval)) {
//    Serial.print(millis());
//    Serial.println("Reconnecting to WiFi...");
    WiFi.disconnect();
    WiFi.reconnect();
    previousMillis = currentMillis;
  }
  if(WiFi.status() != WL_CONNECTED)
  {
    return;
  }
  CO2_Reading();
  SHT_SGP_Reading();
  PM_Reading();

  int x = ThingSpeak.writeFields(writeChannelID, writeAPIKey);

  delay(45000);
}