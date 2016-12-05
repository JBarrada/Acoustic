void setup() {
  // put your setup code here, to run once:
  pinMode(2, OUTPUT);
  pinMode(3, OUTPUT);

  digitalWrite(2, HIGH);
  delayMicroseconds(2000);
  digitalWrite(2, LOW);
  
  delayMicroseconds(8000);
  
  digitalWrite(3, HIGH);
  delayMicroseconds(2000);
  digitalWrite(3, LOW);
}

void loop() {
  // put your main code here, to run repeatedly:

}
