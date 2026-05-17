import time
from pyfirmata2 import Arduino, SERVO

port = "COM8"  
pin_servo = 10

print("🔌 Conectando con el Arduino en el puerto COM8...")

try:
    board = Arduino(port)
    board.digital[pin_servo].mode = SERVO
    print("✅ ¡Conexión exitosa! Iniciando movimiento de prueba...")
    
    print("Moviendo a 0 grados...")
    board.digital[pin_servo].write(0)
    time.sleep(1.5)
    
    print("Moviendo a 90 grados...")
    board.digital[pin_servo].write(90)
    time.sleep(1.5)
    
    print("Moviendo a 180 grados...")
    board.digital[pin_servo].write(180)
    time.sleep(1.5)
    
    print("Regresando a 0 grados...")
    board.digital[pin_servo].write(0)
    time.sleep(1.5)
    
    print("🎉 ¡Prueba de hardware superada con éxito! El motor funciona.")

except Exception as e:
    print(f"❌ Error en la prueba: {e}")

finally:
    if 'board' in locals():
        board.exit()