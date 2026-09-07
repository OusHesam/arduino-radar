#include <Servo.h>
#include <EEPROM.h>

Servo radarServo;

const byte SERVO_PIN  = 6;
const byte TRIG_PIN   = 9;
const byte ECHO_PIN   = 10;
const byte BUZZER_PIN = 8;

const float DEFAULT_MAX_DISTANCE = 20.0;
float maxDistance = DEFAULT_MAX_DISTANCE;

const unsigned long SERVO_INTERVAL = 35;
const unsigned long MEASURE_INTERVAL = 35;

int angle = 90;
int direction = 1;

const int EEPROM_ADDR = 0;

unsigned long lastServoMove = 0;
unsigned long lastEEPROMSave = 0;
unsigned long lastMeasure = 0;

bool manualMode = false;

float getDistance() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  unsigned long duration = pulseIn(ECHO_PIN, HIGH, 7000);
  if (duration == 0) return -1;

  float distance = duration * 0.0343 / 2.0;
  if (distance < 2.0 || distance > maxDistance) return -1;
  return distance;
}

void setup() {
  Serial.begin(9600);

  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(BUZZER_PIN, OUTPUT);

  digitalWrite(TRIG_PIN, LOW);
  noTone(BUZZER_PIN);

  int savedAngle = EEPROM.read(EEPROM_ADDR);
  if (savedAngle >= 0 && savedAngle <= 180) {
    angle = savedAngle;
  } else {
    angle = 90;
  }

  if (angle >= 180) direction = -1;
  else direction = 1;

  radarServo.attach(SERVO_PIN);
  radarServo.write(angle);
  delay(250);

  lastServoMove = millis();
  lastEEPROMSave = millis();
  lastMeasure = millis();
}

void loop() {
  unsigned long now = millis();
  if (Serial.available() > 0) {
    char cmd = Serial.read();

    if (cmd == 'M' || cmd == 'm') {
      manualMode = !manualMode;
      Serial.println("MANUAL TOGGLED");
      if (manualMode) {
        radarServo.write(angle);
      }
    }
    else if (cmd == 'A' || cmd == 'a') {
      int newAngle = Serial.parseInt();
      if (newAngle >= 0 && newAngle <= 180) {
        angle = newAngle;
        radarServo.write(angle);
        Serial.print("ANGLE SET TO: ");
        Serial.println(angle);
      }
    }
    else if (cmd == 'D' || cmd == 'd') {
      float newMax = Serial.parseFloat();
      if (newMax >= 10.0 && newMax <= 100.0) {
        maxDistance = newMax;
        Serial.print("MAX DISTANCE SET TO: ");
        Serial.println(maxDistance);
      }
    }
    while (Serial.available()) Serial.read();
  }

  if (now - lastMeasure >= MEASURE_INTERVAL) {
    lastMeasure = now;

    float distance = getDistance();

    Serial.print("ANGLE:");
    Serial.print(angle);
    Serial.print(",DIST:");

    if (distance > 0) {
      Serial.println(distance, 1);
      tone(BUZZER_PIN, 1200, 15);
    } else {
      Serial.println(-1);
    }
  }

  if (!manualMode) {
    if (now - lastServoMove >= SERVO_INTERVAL) {
      lastServoMove = now;

      angle += direction;
      if (angle >= 180) {
        angle = 180;
        direction = -1;
      }
      if (angle <= 0) {
        angle = 0;
        direction = 1;
      }

      radarServo.write(angle);
    }
  }

  if (now - lastEEPROMSave >= 500) {
    lastEEPROMSave = now;
    EEPROM.update(EEPROM_ADDR, angle);
  }
}
