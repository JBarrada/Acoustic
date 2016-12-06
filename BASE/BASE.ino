// TETRA_BASE

#include <SoftwareSerial.h>

SoftwareSerial mySerial(10, 11); // RX, TX

int CHIRP_LEN = 2000; // microseconds
int CHIRP_GAP = 10000; // microseconds

void setup() {
  // put your setup code here, to run once:
  pinMode(2, OUTPUT);
  pinMode(3, OUTPUT);
  pinMode(4, OUTPUT);
  pinMode(5, OUTPUT);
  
  mySerial.begin(9600);

  for (int i = 2; i < 20; i+=2) {
    digitalWrite(2, HIGH);
    delayMicroseconds(i*1000);
    digitalWrite(2, LOW);

    delay(100);
    //delayMicroseconds(CHIRP_GAP - CHIRP_LEN);
  }
}

void echo() {
  for (int i = 2; i < 6; i++) {
    digitalWrite(i, HIGH);
    delayMicroseconds(CHIRP_LEN);
    digitalWrite(i, LOW);

    delay(30);
    //delayMicroseconds(CHIRP_GAP - CHIRP_LEN);
  }
}

void loop() {
  // put your main code here, to run repeatedly:
  if (mySerial.available()) {
    char c = mySerial.read();

    if (c == 'S') {
      echo();
    }
  }
}
