import os
import sys
import math
import time

# --- PARCHE DE INGENIERÍA: CARGA DE DLLS CORPORATIVAS ---
try:
    import msvc_runtime
    ruta_dll = os.path.dirname(msvc_runtime.__file__)
    os.add_dll_directory(ruta_dll)
except Exception:
    pass
# --------------------------------------------------------

import cv2
import numpy as np
import serial
from mediapipe.python.solutions import hands as mp_hands
from mediapipe.python.solutions import drawing_utils as mp_drawing

# --- CONFIGURACIÓN DE PUERTO SERIAL ---
PUERTO_COM = "COM8"
try:
    arduino = serial.Serial(PUERTO_COM, 9600, timeout=0.1)
    time.sleep(2) 
    print(f"✅ Comunicacion Serial establecida en {PUERTO_COM}")
except Exception as e:
    print(f"❌ Error al abrir el puerto {PUERTO_COM}: {e}")
    exit()

# --- CONFIGURACIÓN ESTÉTICA DE LA PANTALLA ---
ANCHO_RADAR, ALTO_RADAR = 700, 450
CENTRO_X, CENTRO_Y = ANCHO_RADAR // 2, ALTO_RADAR - 30
RADIO_MAX = 380
MAX_DISTANCIA_CM = 40.0

# PALETA DE COLORES NEÓN (Formato BGR de OpenCV)
COLOR_GRID_BASE = (80, 50, 0)       # Azul oscuro muy tenue para la rejilla de fondo
COLOR_GRID_TEXT = (120, 80, 0)      # Azul intermedio para etiquetas de escala
COLOR_TEXTO = (255, 255, 0)         # Neon Cyan brillante para datos tacticos
COLOR_BARRIDO = (255, 200, 0)       # Cyan intermedio para la linea del haz electrico
COLOR_OBSTACULO = (0, 0, 255)       # Rojo carmesi puro para el punto real del objeto

historial_radar = {}

def dibujar_interfaz_radar():
    """Genera el fondo grafico estilo instrumental Sci-Fi Neon Militar"""
    pantalla = np.zeros((ALTO_RADAR, ANCHO_RADAR, 3), dtype=np.uint8)
    
    escalas = [
        (RADIO_MAX // 4, "10cm"),
        (RADIO_MAX // 2, "20cm"),
        ((RADIO_MAX * 3) // 4, "30cm"),
        (RADIO_MAX, "40cm")
    ]
    
    for r, etiqueta in escalas:
        cv2.circle(pantalla, (CENTRO_X, CENTRO_Y), r, COLOR_GRID_BASE, 1)
        cv2.putText(pantalla, etiqueta, (CENTRO_X + 10, CENTRO_Y - r + 5), 
                    cv2.FONT_HERSHEY_PLAIN, 0.8, COLOR_GRID_TEXT, 1)
    
    for a in [30, 60, 90, 120, 150]:
        rad = math.radians(a)
        x = int(CENTRO_X + RADIO_MAX * math.cos(rad))
        y = int(CENTRO_Y - RADIO_MAX * math.sin(rad))
        cv2.line(pantalla, (CENTRO_X, CENTRO_Y), (x, y), COLOR_GRID_BASE, 1)
        cv2.putText(pantalla, f"{a}", (x - 10 if x < CENTRO_X else x, y - 5), 
                    cv2.FONT_HERSHEY_PLAIN, 0.8, COLOR_GRID_TEXT, 1)
        
    cv2.putText(pantalla, "SISTEMA TACTICO RADAR HC-SR04", (20, 35), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLOR_TEXTO, 2)
    cv2.putText(pantalla, f"Escala Max: {int(MAX_DISTANCIA_CM)} cm", (ANCHO_RADAR - 180, 35), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, COLOR_TEXTO, 1)
    
    return pantalla

# Inicializamos captura de video de forma segura
print("📷 Inicializando el hardware de la camara web...")
cap = cv2.VideoCapture(0)

with mp_hands.Hands(min_detection_confidence=0.5, min_tracking_confidence=0.5) as hands:
    print("\n🚀 Entorno Grafico Tactico y Vision IA listos.")
    print("👉 Une las puntas de los dedos para iniciar el escaneo fisico...\n")
    
    while cap.isOpened():
        success, frame = cap.read()
        if not success: 
            print("⚠️ Esperando flujo de la camara...")
            continue

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
            print("\n📡 Gesto Correcto. Adquiriendo telemetria del hardware...")
            arduino.write(b'S') 
            arduino.reset_input_buffer()
            
            # --- PARCHE DE SEGURIDAD: WATCHDOG TIMER ---
            lineas_leidas = 0
            tiempo_inicio_escaneo = time.time()
            max_tiempo_espera = 5.0 
            
            while lineas_leidas < 92:
                if (time.time() - tiempo_inicio_escaneo) > max_tiempo_espera:
                    print("⚠️ Alerta: El hardware tardo demasiado en transmitir. Abortando bucle por seguridad.")
                    break
                    
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
                            
                            # --- SECCIÓN DE RENDIMIENTO Y GRAFICADO DE OBSTÁCULOS ---
                            for antiguo_ang, antiguo_dist in historial_radar.items():
                                if antiguo_dist >= MAX_DISTANCIA_CM: continue 

                                rad_obstaculo = math.radians(antiguo_ang)
                                num_capas_sombra = 3 
                                decalaje_cm = 1.3

                                # =========================================================================
                                # 🔵 MODO 1 (POR DEFECTO): PUNTITO TRADICIONAL CON SOMBRA PROYECTADA ATRAS
                                # =========================================================================
                                # A. Dibujar sombras del puntito (Se alejan sumando distancia)
                                for i in range(1, num_capas_sombra + 1):
                                    r_capa = antiguo_dist + (i * decalaje_cm)
                                    if r_capa < MAX_DISTANCIA_CM:
                                        r_px_capa = int((r_capa / MAX_DISTANCIA_CM) * RADIO_MAX)
                                        sx = int(CENTRO_X + r_px_capa * math.cos(rad_obstaculo))
                                        sy = int(CENTRO_Y - r_px_capa * math.sin(rad_obstaculo))
                                        
                                        intensidad_r = 90 - (i * 20) 
                                        COLOR_CAPA = (0, 0, max(15, intensidad_r))
                                        cv2.circle(radar_img, (sx, sy), 3, COLOR_CAPA, -1)

                                # B. Dibujar el punto real al frente
                                r_pixel_frente = int((antiguo_dist / MAX_DISTANCIA_CM) * RADIO_MAX)
                                ox = int(CENTRO_X + r_pixel_frente * math.cos(rad_obstaculo))
                                oy = int(CENTRO_Y - r_pixel_frente * math.sin(rad_obstaculo))
                                cv2.circle(radar_img, (ox, oy), 5, COLOR_OBSTACULO, -1)
                                # =========================================================================

                                # =========================================================================
                                # 🟢 MODO 2 (COMENTADO): ARCOS DE IMPACTO (SECTORES DE CONO ACUSTICO)
                                # =========================================================================
                                # # A. Dibujar las capas de sombras en formato de arco curvo
                                # for i in range(1, num_capas_sombra + 1):
                                #     r_capa = antiguo_dist + (i * decalaje_cm)
                                #     if r_capa < MAX_DISTANCIA_CM:
                                #         r_px_capa = int((r_capa / MAX_DISTANCIA_CM) * RADIO_MAX)
                                #         intensidad_r = 90 - (i * 20) 
                                #         COLOR_CAPA = (0, 0, max(15, intensidad_r))
                                #         cv2.ellipse(radar_img, (CENTRO_X, CENTRO_Y), (r_px_capa, r_px_capa), 
                                #                     0, 360 - antiguo_ang - 3, 360 - antiguo_ang + 3, COLOR_CAPA, -1)
                                #
                                # # B. Dibujar el arco de impacto principal al frente
                                # r_pixel_frente = int((antiguo_dist / MAX_DISTANCIA_CM) * RADIO_MAX)
                                # cv2.ellipse(radar_img, (CENTRO_X, CENTRO_Y), (r_pixel_frente, r_pixel_frente), 
                                #             0, 360 - antiguo_ang - 3, 360 - antiguo_ang + 3, COLOR_OBSTACULO, -1)
                                # =========================================================================

                                # =========================================================================
                                # 🟡 MODO 3 (COMENTADO): RETICULAS DE FIJACION (CROSSHAIRS / MIRAS MILITARES)
                                # =========================================================================
                                # # A. Dibujar sombras del puntito
                                # for i in range(1, num_capas_sombra + 1):
                                #     r_capa = antiguo_dist + (i * decalaje_cm)
                                #     if r_capa < MAX_DISTANCIA_CM:
                                #         r_px_capa = int((r_capa / MAX_DISTANCIA_CM) * RADIO_MAX)
                                #         sx = int(CENTRO_X + r_px_capa * math.cos(rad_obstaculo))
                                #         sy = int(CENTRO_Y - r_px_capa * math.sin(rad_obstaculo))
                                #         intensidad_r = 90 - (i * 20) 
                                #         COLOR_CAPA = (0, 0, max(15, intensidad_r))
                                #         cv2.circle(radar_img, (sx, sy), 3, COLOR_CAPA, -1)
                                #
                                # # B. Calcular punto central y dibujar Mira Tactica de Cruz (+) encima
                                # r_pixel_frente = int((antiguo_dist / MAX_DISTANCIA_CM) * RADIO_MAX)
                                # ox = int(CENTRO_X + r_pixel_frente * math.cos(rad_obstaculo))
                                # oy = int(CENTRO_Y - r_pixel_frente * math.sin(rad_obstaculo))
                                # cv2.circle(radar_img, (ox, oy), 3, COLOR_OBSTACULO, -1)
                                # cv2.line(radar_img, (ox - 7, oy), (ox + 7, oy), COLOR_OBSTACULO, 1)
                                # cv2.line(radar_img, (ox, oy - 7), (ox, oy + 7), COLOR_OBSTACULO, 1)
                                # =========================================================================

                            # Haz de barrido Cyan
                            rad_actual = math.radians(ang)
                            lx = int(CENTRO_X + RADIO_MAX * math.cos(rad_actual))
                            ly = int(CENTRO_Y - RADIO_MAX * math.sin(rad_actual))
                            cv2.line(radar_img, (CENTRO_X, CENTRO_Y), (lx, ly), COLOR_BARRIDO, 3)
                            
                            # PANEL DE DATOS INFERIOR
                            cv2.putText(radar_img, f"AZIMUTH: {ang:3d} DEG | DISTANCIA OBJETIVO: {dist:4.1f} cm", 
                                        (20, ALTO_RADAR - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, COLOR_TEXTO, 1)
                            
                            cv2.imshow("Pantalla de Radar Militar - Datos HC-SR04", radar_img)
                            cv2.waitKey(1)
                        except ValueError:
                            pass

        cv2.imshow("Control Radar Windows - MediaPipe", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

# --- LIBERACIÓN DE RECURSOS ---
cap.release()
cv2.destroyAllWindows()
arduino.close()
print("\n✅ Puerto Serial cerrado de forma segura.")