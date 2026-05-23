# Sistema de Radar Táctico IoT con Instrumentación Local (OLED) 📡

Este repositorio contiene el código fuente, la configuración de hardware y la documentación necesaria para desplegar un sistema de radar táctico basado en la Internet de las Cosas (IoT). El proyecto implementa una arquitectura distribuida cliente-servidor que integra telemetría en tiempo real, instrumentación gráfica local y un panel de control multiplataforma accesible desde navegadores web o aplicaciones de escritorio.

---

## 🚀 Arquitectura General del Sistema

El sistema se divide en tres capas de operación independientes que se comunican de forma asíncrona:
1. **Capa de Hardware (Arduino UNO):** Controla físicamente un servomotor para el barrido angular y calcula distancias mediante un sensor ultrasónico. Los datos se despliegan localmente en tiempo real en una pantalla OLED y se envían de forma empaquetada (`ángulo,distancia`) por el cable USB.
2. **Capa de Servidor (Python Gateway):** Escucha el puerto serie de la computadora. Procesa el flujo de texto entrante y lo distribuye de forma instantánea a través de WebSockets de alta velocidad o mediante renderizado local.
3. **Capa de Interfaz de Usuario (UI):** Renderiza dinámicamente un mapa de radar vectorial con efectos de persistencia (sombras de arrastre de objetivos) empleando gráficos acelerados por hardware.

---

## 🔌 Diagrama de Conexiones Físicas (Pinout)

Para replicar el circuito físico, conecta los componentes al Arduino UNO siguiendo estrictamente la siguiente distribución de pines. Todos los componentes comparten las líneas de alimentación comunes de **5V** y **GND** en la protoboard.

| Componente | Pin del Componente | Pin Digital/Análogo Arduino | Función Técnica |
| :--- | :--- | :--- | :--- |
| **Servomotor SG90** | Cable Naranja / Amarillo (PWM) | **Pin 10** | Control del barrido angular (0° - 180°) |
| **Sensor HC-SR04** | Trigger (Trig) | **Pin 11** | Disparador del pulso ultrasónico |
| **Sensor HC-SR04** | Echo | **Pin 12** | Receptor del eco de retorno |
| **Pantalla OLED 0.96"** | SDA (Datos I2C) | **Pin A4** | Transmisión de datos gráficos locales |
| **Pantalla OLED 0.96"** | SCL (Reloj I2C) | **Pin A5** | Sincronización de reloj de la pantalla |

*Nota eléctrica: Si el servomotor experimenta sutiles bloqueos o reinicia el Arduino, se recomienda alimentar el riel de la protoboard mediante una fuente externa de 5V o conectar la computadora al cargador de pared para garantizar el suministro adecuado de miliamperios en el puerto USB.*

---

## 📦 Prerrequisitos e Instalación

### 1. Preparación del Hardware (Arduino IDE)
Antes de conectar la placa, abre el **Arduino IDE** e instala los siguientes módulos a través del Gestor de Librerías (`Ctrl + Shift + I`):
* `Servo` (Librería nativa incorporada)
* `Adafruit SSD1306` (Controlador del motor gráfico de la pantalla)
* `Adafruit GFX Library` (Núcleo de funciones de dibujo vectorial)

Carga el archivo de firmware proporcionado en la carpeta `hardware/` hacia tu placa Arduino UNO. Al energizarse, la pantalla OLED mostrará el mensaje de inicialización: `[ ESPERANDO S ]`.

### 2. Configuración del Entorno de Software (Python)
El sistema requiere **Python 3.10 o superior** instalado en la computadora que actuará como servidor o estación base. 

Abre una terminal (PowerShell o CMD) dentro de la carpeta del proyecto y ejecuta la siguiente secuencia de comandos para inicializar un entorno virtual limpio e instalar las dependencias aisladas:

```powershell
# 1. Crear el entorno virtual de aislamiento
python -m venv .venv

# 2. Instalar el paquete completo de librerías requeridas
.\.venv\Scripts\pip install fastapi uvicorn pyserial websockets opencv-python numpy