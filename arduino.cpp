#include <Servo.h>

Servo myServo;
const int trigPin = 11;
const int echoPin = 12;

void setup() {
  myServo.attach(10);
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
  
  Serial.begin(9600);
  myServo.write(0);
}

void loop() {
  if (Serial.available() > 0) {
    char comando = Serial.read();
    
    if (comando == 'S') {
      
      for (int angulo = 0; angulo <= 180; angulo += 4) {
        myServo.write(angulo);
        delay(35);
        long distancia = tomarDistancia();
        
        Serial.print(angulo);
        Serial.print(",");
        Serial.println(distancia);
      }
      
      for (int angulo = 180; angulo >= 0; angulo -= 4) {
        myServo.write(angulo);
        delay(35);
        long distancia = tomarDistancia();
        
        Serial.print(angulo);
        Serial.print(",");
        Serial.println(distancia);
      }
    }
  }
}

long tomarDistancia() {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);
  
  long duracion = pulseIn(echoPin, HIGH, 25000); 
  long distancia = duracion * 0.034 / 2;
  
  if (distancia == 0 || distancia > 40) {
    return 40;
  }
  return distancia;
}