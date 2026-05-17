import os
import sys
import math
import time

try:
    import msvc_runtime
    ruta_dll = os.path.dirname(msvc_runtime.__file__)
    os.add_dll_directory(ruta_dll)
except Exception:
    pass

import cv2
import numpy as np
import serial
from mediapipe.python.solutions import hands as mp_hands
from mediapipe.python.solutions import drawing_utils as mp_drawing

PUERTO_COM = "COM8"
try:
    arduino = serial.Serial(PUERTO_COM, 9600, timeout=0.1)
    time.sleep(2)
    print(f"✅ Comunicación Serial establecida en {PUERTO_COM}")
except Exception as e:
    print(f"❌ Error al abrir el puerto {PUERTO_COM}: {e}")
    exit()

ANCHO_RADAR, ALTO_RADAR = 600, 400
CENTRO_X, CENTRO_Y = ANCHO_RADAR // 2, ALTO_RADAR - 20
RADIO_MAX = 350
MAX_DISTANCIA_CM = 40.0

historial_radar = {}

def dibujar_interfaz_radar():
    """Genera el fondo gráfico estilo sonar militar"""
    pantalla = np.zeros((ALTO_RADAR, ANCHO_RADAR, 3), dtype=np.uint8)
    
    for r in [RADIO_MAX // 4, RADIO_MAX // 2, (RADIO_MAX * 3) // 4, RADIO_MAX]:
        cv2.circle(pantalla, (CENTRO_X, CENTRO_Y), r, (0, 100, 0), 1)
    
    for a in [30, 60, 90, 120, 150]:
        rad = math.radians(a)
        x = int(CENTRO_X + RADIO_MAX * math.cos(rad))
        y = int(CENTRO_Y - RADIO_MAX * math.sin(rad))
        cv2.line(pantalla, (CENTRO_X, CENTRO_Y), (x, y), (0, 60, 0), 1)
        
    cv2.putText(pantalla, "SISTEMA SONAR RADAR", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    cv2.putText(pantalla, f"Rango Max: {int(MAX_DISTANCIA_CM)}cm", (ANCHO_RADAR - 160, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    return pantalla

cap = cv2.VideoCapture(0)

with mp_hands.Hands(min_detection_confidence=0.5, min_tracking_confidence=0.5) as hands:
    print("\n🚀 Entorno Gráfico y Visión IA listos.")
    print("👉 Une los dedos para iniciar el escaneo físico y ver el mapa...")
    
    while cap.isOpened():
        success, frame = cap.read()
        if not success: break

        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb_frame)
        
        escaneo_activo = False

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                
                p1 = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
                p2 = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                distancia_dedos = math.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2)
                
                print(f"✋ Mano Detectada -> Distancia dedos: {distancia_dedos:.3f}", end="\r")

                if distancia_dedos < 0.09:
                    escaneo_activo = True

        if escaneo_activo:
            print("\n📡 ¡Gesto Correcto! Ordenando escaneo al hardware...")
            arduino.write(b'S')
            
            arduino.reset_input_buffer()
            
            lineas_leidas = 0
            while lineas_leidas < 92:
                if arduino.in_waiting > 0:
                    linea = arduino.readline().decode('utf-8', errors='ignore').strip()
                    if "," in linea:
                        try:
                            str_ang, str_dist = linea.split(",")
                            ang = int(str_ang)
                            dist = float(str_dist)
                            
                            historial_radar[ang] = dist
                            lineas_leidas += 1
                            
                            radar_img = dibujar_interfaz_radar()
                            
                            for antiguo_ang, antiguo_dist in historial_radar.items():
                                rad_obstaculo = math.radians(antiguo_ang)
                                r_pixel = int((antiguo_dist / MAX_DISTANCIA_CM) * RADIO_MAX)
                                ox = int(CENTRO_X + r_pixel * math.cos(rad_obstaculo))
                                oy = int(CENTRO_Y - r_pixel * math.sin(rad_obstaculo))
                                
                                if antiguo_dist < MAX_DISTANCIA_CM:
                                    cv2.circle(radar_img, (ox, oy), 4, (0, 0, 255), -1)
                            
                            rad_actual = math.radians(ang)
                            lx = int(CENTRO_X + RADIO_MAX * math.cos(rad_actual))
                            ly = int(CENTRO_Y - RADIO_MAX * math.sin(rad_actual))
                            cv2.line(radar_img, (CENTRO_X, CENTRO_Y), (lx, ly), (0, 255, 0), 2)
                            
                            cv2.putText(radar_img, f"Angulo: {ang}deg | Dist: {dist}cm", (10, ALTO_RADAR - 10), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
                            
                            cv2.imshow("Pantalla de Radar Militar - Datos HC-SR04", radar_img)
                            cv2.waitKey(1)
                        except ValueError:
                            pass

        cv2.imshow("Control Radar Windows - MediaPipe", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()
arduino.close()
print("\n✅ Puerto Serial cerrado y entorno limpio de forma segura.")