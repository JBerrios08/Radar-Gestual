import cv2
import mediapipe as mp
import serial
import math
import numpy as np
import time

# --- CONFIGURACIÓN DE PUERTO SERIAL ---
# ¡IMPORTANTE!: Cambia "COM8" por el puerto que te asigne la nueva máquina
PUERTO_COM = "COM3"
try:
    arduino = serial.Serial(PUERTO_COM, 9600, timeout=0.01)
    time.sleep(2)
    print(f"✅ Comunicación Serial establecida en {PUERTO_COM}")
except Exception as e:
    print(f"❌ Error al abrir el puerto {PUERTO_COM}: {e}")
    arduino = None

# --- CONFIGURACIÓN DE MEDIAPIPE (DETECCIÓN DE MANOS) ---
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)
mp_dibujo = mp.solutions.drawing_utils

# --- VARIABLES DEL RADAR ---
WIDTH, HEIGHT = 700, 420
CENTRO_X, CENTRO_Y = WIDTH // 2, HEIGHT - 30
RADIO_MAX = 360
MAX_DISTANCIA_CM = 40.0

historial_radar = {}
angulo_actual = 0
distancia_actual = 0
escaneando = False
tiempo_ultimo_escaneo = 0

def dibujar_radar(angulo, historial):
    # Crear un lienzo negro vacío
    lienzo = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)

    # Colores BGR para OpenCV
    color_grid = (120, 80, 0)      # Azul oscuro
    color_texto = (255, 255, 0)    # Cian
    color_barrido = (255, 200, 0)  # Cian brillante
    color_obstaculo = (0, 0, 255)  # Rojo

    # 1. Dibujar Rejilla Concéntrica
    escalas = [RADIO_MAX // 4, RADIO_MAX // 2, (RADIO_MAX * 3) // 4, RADIO_MAX]
    etiquetas = ["10cm", "20cm", "30cm", "40cm"]
    
    for i, r in enumerate(escalas):
        cv2.circle(lienzo, (CENTRO_X, CENTRO_Y), r, color_grid, 1)
        cv2.putText(lienzo, etiquetas[i], (CENTRO_X + 5, CENTRO_Y - r + 15), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, color_grid, 1, cv2.LINE_AA)

    # Líneas radiales de ángulos
    angulos_grid = [30, 60, 90, 120, 150]
    for a in angulos_grid:
        rad = math.radians(a)
        x = int(CENTRO_X + RADIO_MAX * math.cos(rad))
        y = int(CENTRO_Y - RADIO_MAX * math.sin(rad))
        cv2.line(lienzo, (CENTRO_X, CENTRO_Y), (x, y), color_grid, 1)
        cv2.putText(lienzo, f"{a} deg", (x - 15, y - 5), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, color_grid, 1, cv2.LINE_AA)

    # 2. Dibujar Obstáculos con Sombra Invertida (Modo 1)
    for ang, dist in historial.items():
        if dist >= MAX_DISTANCIA_CM:
            continue
            
        rad_obs = math.radians(ang)
        num_capas_sombra = 3
        decalaje_cm = 1.3

        # A. Sombras proyectadas hacia atrás
        for i in range(1, num_capas_sombra + 1):
            r_capa = dist + (i * decalaje_cm)
            if r_capa < MAX_DISTANCIA_CM:
                r_px_capa = int((r_capa / MAX_DISTANCIA_CM) * RADIO_MAX)
                sx = int(CENTRO_X + r_px_capa * math.cos(rad_obs))
                sy = int(CENTRO_Y - r_px_capa * math.sin(rad_obs))
                # Atenuar el color rojo simulando opacidad
                color_atenuado = (0, 0, int(255 - (i * 60)))
                cv2.circle(lienzo, (sx, sy), 2, color_atenuado, -1)

        # B. Punto real al frente
        r_px_frente = int((dist / MAX_DISTANCIA_CM) * RADIO_MAX)
        ox = int(CENTRO_X + r_px_frente * math.cos(rad_obs))
        oy = int(CENTRO_Y - r_px_frente * math.sin(rad_obs))
        cv2.circle(lienzo, (ox, oy), 4, color_obstaculo, -1)

    # 3. Dibujar Línea de Barrido Actual
    rad_actual = math.radians(angulo)
    lx = int(CENTRO_X + RADIO_MAX * math.cos(rad_actual))
    ly = int(CENTRO_Y - RADIO_MAX * math.sin(rad_actual))
    cv2.line(lienzo, (CENTRO_X, CENTRO_Y), (lx, ly), color_barrido, 2)
    
    # Textos de Telemetría
    cv2.putText(lienzo, "SISTEMA TACTICO IA LOCAL", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color_texto, 1)
    cv2.putText(lienzo, f"AZIMUTH: {angulo} DEG", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color_texto, 1)
    cv2.putText(lienzo, "GESTO: JUNTAR DEDOS PARA ESCANEAR", (WIDTH - 280, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)

    return lienzo

# --- BUCLE PRINCIPAL DE CÁMARA Y RADAR ---
cap = cv2.VideoCapture(0)

print("🎥 Iniciando cámara y esperando gestos...")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1) # Efecto espejo
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    resultados = hands.process(frame_rgb)

    # --- 1. LÓGICA DE INTELIGENCIA ARTIFICIAL (DETECCIÓN DE PINZA) ---
    gesto_detectado = False
    if resultados.multi_hand_landmarks:
        for hand_landmarks in resultados.multi_hand_landmarks:
            mp_dibujo.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            
            # Obtener coordenadas del dedo índice (8) y pulgar (4)
            h, w, _ = frame.shape
            x_indice, y_indice = int(hand_landmarks.landmark[8].x * w), int(hand_landmarks.landmark[8].y * h)
            x_pulgar, y_pulgar = int(hand_landmarks.landmark[4].x * w), int(hand_landmarks.landmark[4].y * h)
            
            # Dibujar puntos en los dedos
            cv2.circle(frame, (x_indice, y_indice), 8, (255, 0, 0), -1)
            cv2.circle(frame, (x_pulgar, y_pulgar), 8, (255, 0, 0), -1)
            cv2.line(frame, (x_indice, y_indice), (x_pulgar, y_pulgar), (0, 255, 0), 2)
            
            # Calcular distancia entre los dedos
            distancia_dedos = math.hypot(x_indice - x_pulgar, y_indice - y_pulgar)
            
            # Si los dedos se tocan (pinza), activar bandera
            if distancia_dedos < 30:
                gesto_detectado = True
                cv2.putText(frame, "GATILLO ACTIVADO!", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)

    # --- 2. LÓGICA DE CONTROL DEL ARDUINO ---
    # Disparar solo si el gesto se detecta, no estamos escaneando, y ha pasado 1 segundo desde el último disparo
    if gesto_detectado and not escaneando and (time.time() - tiempo_ultimo_escaneo > 1.0):
        if arduino:
            print("📡 Gesto detectado: Ordenando barrido al Arduino...")
            arduino.write(b'S')
            arduino.reset_input_buffer()
        escaneando = True
        tiempo_ultimo_escaneo = time.time()

    # --- 3. LECTURA SERIAL Y RENDERIZADO DEL RADAR ---
    if arduino and arduino.in_waiting > 0:
        linea = arduino.readline().decode('utf-8', errors='ignore').strip()
        if "," in linea:
            try:
                partes = linea.split(",")
                angulo_actual = int(partes[0])
                distancia_actual = float(partes[1])
                historial_radar[angulo_actual] = distancia_actual
                
                # Si el Arduino vuelve a 0 grados después de un tiempo, asumimos que terminó un barrido
                if angulo_actual == 0 and (time.time() - tiempo_ultimo_escaneo > 2.0):
                    escaneando = False
            except ValueError:
                pass

    # Dibujar la ventana de la cámara
    cv2.imshow("IA Vision - Control", frame)
    
    # Dibujar la ventana del Radar
    imagen_radar = dibujar_radar(angulo_actual, historial_radar)
    cv2.imshow("Pantalla Radar Tactico", imagen_radar)

    # Salir con la tecla 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Limpieza al salir
cap.release()
cv2.destroyAllWindows()
if arduino:
    arduino.close()