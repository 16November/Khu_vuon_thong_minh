#include "DHT.h"
#include <SoftwareSerial.h>
#include <Arduino.h>

// define
#define DHTPIN A0
#define SOIL1 A1
#define SOIL2 A2
#define SOIL3 A3
#define PUMP1 6
#define PUMP2 5
#define PUMP3 4
#define FAN A5
#define STEP 8
#define DIR 7

int stepToPos = 460;
int dhtHumidity = 0;
int dhtTemperature = 0;
int SoilMoisture1 = 0;
int SoilMoisture2 = 0;
int SoilMoisture3 = 0;
int recentPos = 1;

// dữ liệu gửi
int data[13];

// dht11
const int DHTTYPE = DHT11;
DHT dht(DHTPIN, DHTTYPE);

// Manual override flags
bool manualOverridePUMP1 = false;
bool manualOverridePUMP2 = false;
bool manualOverridePUMP3 = false;

// function
void turnON(int pin) {
  digitalWrite(pin, LOW);
  switch (pin) {
    case FAN:
      data[0] = 1;
      break;
    case PUMP1:
      data[1] = 1;
      break;
    case PUMP2:
      data[2] = 1;
      break;
    case PUMP3:
      data[3] = 1;
      break;
  }
}

void turnOFF(int pin) {
  digitalWrite(pin, HIGH);
  switch (pin) {
    case FAN:
      data[0] = 0;
      break;
    case PUMP1:
      data[1] = 0;
      break;
    case PUMP2:
      data[2] = 0;
      break;
    case PUMP3:
      data[3] = 0;
      break;
  }
}

void updateSensor() {
  dhtHumidity = dht.readHumidity();
  dhtTemperature = dht.readTemperature();
  SoilMoisture1 = map(analogRead(SOIL1), 0, 1023, 100, 0);
  SoilMoisture2 = map(analogRead(SOIL2), 0, 1023, 100, 0);
  SoilMoisture3 = map(analogRead(SOIL3), 0, 1023, 100, 0);
  data[4] = SoilMoisture1;
  data[5] = SoilMoisture2;
  data[6] = SoilMoisture3;
  data[7] = dhtHumidity;
  data[8] = dhtTemperature;
  data[9] = recentPos;
}

void checkSensor() {
  Serial.print("do am = ");
  Serial.println(dhtHumidity);
  Serial.print("nhiet do = ");
  Serial.println(dhtTemperature);
  Serial.print("do am dat 1 = ");
  Serial.println(SoilMoisture1);
  Serial.print("do am dat 2 = ");
  Serial.println(SoilMoisture2);
  Serial.print("do am dat 3 = ");
  Serial.println(SoilMoisture3);
  Serial.println("-----------------------------------");
}

void moveCamera(int pos) {
  if (pos == recentPos) return;
  if (pos > recentPos) {
    digitalWrite(DIR, HIGH);  // Đặt Dir  ở trạng thái HIGH
    for (int x = 0; x < (pos - recentPos) * stepToPos; x++) {
      digitalWrite(STEP, HIGH);
      delayMicroseconds(700);
      digitalWrite(STEP, LOW);
      delayMicroseconds(700);
    }
  }
  if (pos < recentPos) {
    digitalWrite(DIR, LOW);  // Đặt Dir  ở trạng thái LOW
    for (int x = 0; x < (recentPos - pos) * stepToPos; x++) {
      digitalWrite(STEP, HIGH);
      delayMicroseconds(700);
      digitalWrite(STEP, LOW);
      delayMicroseconds(700);
    }
  }
  recentPos = pos;
}

void autoWaterPlants() {
  updateSensor();
  int SoilMoisturemax = 30;

  if (!manualOverridePUMP1) {
    if (SoilMoisture1 < SoilMoisturemax && data[10] == 1) {
      turnON(PUMP1);
    } else {
      turnOFF(PUMP1);
    }
  }

  if (!manualOverridePUMP2) {
    if (SoilMoisture2 < SoilMoisturemax && data[11] == 1) {
      turnON(PUMP2);
    } else {
      turnOFF(PUMP2);
    }
  }

  if (!manualOverridePUMP3) {
    if (SoilMoisture3 < SoilMoisturemax && data[12] == 1) {
      turnON(PUMP3);
    } else {
      turnOFF(PUMP3);
    }
  }
}

SoftwareSerial mySerial(2, 3); // RX, TX

// main
void setup() {
  data[10] = 0;
  data[11] = 0;
  data[12] = 0;
  Serial.begin(19200); // Bắt đầu cổng Serial của Arduino Nano
  mySerial.begin(19200); // Bắt đầu cổng Serial phụ
  
  dht.begin();
  pinMode(PUMP1, OUTPUT);
  pinMode(PUMP2, OUTPUT);
  pinMode(PUMP3, OUTPUT);
  pinMode(FAN, OUTPUT);
  pinMode(STEP, OUTPUT);
  pinMode(DIR, OUTPUT);
  turnOFF(PUMP1);
  turnOFF(PUMP2);
  turnOFF(PUMP3);
  turnOFF(FAN);
  pinMode(DHTPIN, INPUT);
  pinMode(SOIL1, INPUT);
  pinMode(SOIL2, INPUT);
  pinMode(SOIL3, INPUT);
}

void loop() {
  // Call autoWaterPlants() without blocking serial handling
  static unsigned long lastUpdate = 0;
  unsigned long now = millis();

  // Update sensor readings every second
  if (now - lastUpdate >= 1000) {
    autoWaterPlants();
    lastUpdate = now;
  }

  if (Serial.available() > 0) {
    char receivedChar = Serial.read();
    Serial.print("Received: ");
    Serial.println(receivedChar);
    switch (receivedChar) {
      case 'A':
        turnON(FAN);
        break;
      case 'B':
        turnOFF(FAN);
        break;
      case 'C':
        manualOverridePUMP1 = true; // Manual override for PUMP1
        turnON(PUMP1);
        break;
      case 'D':
        manualOverridePUMP1 = false; // Clear manual override for PUMP1
        turnOFF(PUMP1);
        break;
      case 'E':
        manualOverridePUMP2 = true; // Manual override for PUMP2
        turnON(PUMP2);
        break;
      case 'F':
        manualOverridePUMP2 = false; // Clear manual override for PUMP2
        turnOFF(PUMP2);
        break;
      case 'G':
        manualOverridePUMP3 = true; // Manual override for PUMP3
        turnON(PUMP3);
        break;
      case 'H':
        manualOverridePUMP3 = false; // Clear manual override for PUMP3
        turnOFF(PUMP3);
        break;
      case '1':
        moveCamera(1);
        break;
      case '2':
        moveCamera(2);
        break;
      case '3':
        moveCamera(3);
        break;
      case '5': // bật tự động bơm 1
        data[10] = 1;
        break;
      case '6': // tắt tự động bơm 1
        data[10] = 0;
        break;
      case '7': // bật tự động bơm 2
        data[11] = 1;
        break;
      case '8': // tắt tự động bơm 2
        data[11] = 0;
        break;
      case '9': // bật tự động bơm 3
        data[12] = 1;
        break;
      case '0': // tắt tự động bơm 3
        data[12] = 0;
        break;
      case '4':
        updateSensor();
        String s = "";
        for (int i = 0; i < 13; i++) {
          s += (String)data[i];
          s += ",";
        }
        mySerial.print(s);
        Serial.print(s);
        break;
    }
  }
}