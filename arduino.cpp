#include <Servo.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// --- CONFIGURACIÓN DE LA PANTALLA OLED ---
#define ANCHO_PANTALLA 128
#define ALTO_PANTALLA 64
#define DIRECCION_I2C 0x3C // Dirección estándar de fábrica para OLED 0.96"

Adafruit_SSD1306 display(ANCHO_PANTALLA, ALTO_PANTALLA, &Wire, -1);

// --- CONFIGURACIÓN DE PINES FÍSICOS ---
const int servoPin = 10;
const int trigPin = 11;
const int echoPin = 12;

Servo miRadar;

void setup() {
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
  miRadar.attach(servoPin);
  
  miRadar.write(0);
  Serial.begin(9600);

  // Inicializar la pantalla OLED
  if(!display.begin(SSD1306_SWITCHCAPVCC, DIRECCION_I2C)) {
    Serial.println(F("Fallo al iniciar SSD1306"));
    for(;;); // Detiene el sistema si no detecta la pantalla físicamente
  }
  
  // Pantalla de Inicio / Reposo
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 20);
  display.println(F("   SISTEMA RADAR"));
  display.setCursor(0, 40);
  display.println(F("  [ ESPERANDO S ]"));
  display.display();
}

void loop() {
  if (Serial.available() > 0) {
    char orden = Serial.read();
    
    if (orden == 'S') {
      // --- BARRIDO DE IDA ---
      for (int angulo = 0; angulo <= 180; angulo += 4) {
        miRadar.write(angulo);
        delay(35); 
        float distancia = medirDistancia();
        
        // 1. Enviar telemetría limpia a Python por USB
        Serial.print(angulo);
        Serial.print(",");
        Serial.println(distancia);
        
        // 2. Dibujar gráficos tácticos en la OLED localmente
        actualizarOLED(angulo, distancia);
      }
      
      // --- BARRIDO DE VUELTA ---
      for (int angulo = 180; angulo >= 0; angulo -= 4) {
        miRadar.write(angulo);
        delay(35);
        float distancia = medirDistancia();
        
        Serial.print(angulo);
        Serial.print(",");
        Serial.println(distancia);
        
        actualizarOLED(angulo, distancia);
      }
      
      // Al terminar un ciclo, vuelve a estado de reposo si Python no pide otro
      display.clearDisplay();
      display.setCursor(0, 20);
      display.println(F("   SISTEMA RADAR"));
      display.setCursor(0, 40);
      display.println(F("  [ SCAN READY ]"));
      display.display();
    }
  }
}

float medirDistancia() {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);
  
  long duracion = pulseIn(echoPin, HIGH, 30000); 
  
  if (duracion == 0) {
    return 40.0; 
  }
  
  return duracion * 0.034 / 2;
}

// Función encargada exclusivamente del diseño de la interfaz OLED
void actualizarOLED(int angulo, float distancia) {
  display.clearDisplay();
  
  // Fila 1: Estado del Sistema
  display.setTextSize(1);
  display.setCursor(0, 0);
  display.print(F("[ SCANNING... ]"));
  
  // Fila 2: Telemetría de Ángulo
  display.setCursor(0, 20);
  display.print(F("ANGULO: "));
  display.print(angulo);
  display.print(F(" DEG"));
  
  // Fila 3: Telemetría de Distancia
  display.setCursor(0, 35);
  display.print(F("DIST:   "));
  display.print(distancia, 1);
  display.print(F(" CM"));
  
  // Fila 4: Barra de Progreso Dinámica
  // Mapeamos el ángulo de 0 a 180 hacia los 128 píxeles de ancho de la pantalla
  int anchoBarra = map(angulo, 0, 180, 0, 128); 
  display.drawRect(0, 52, 128, 10, SSD1306_WHITE); // Dibuja el marco de la barra
  display.fillRect(0, 52, anchoBarra, 10, SSD1306_WHITE); // Dibuja el relleno interno
  
  // Enviar todo el buffer a la pantalla
  display.display();
}