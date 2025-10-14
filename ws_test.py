import asyncio
import websockets
from config import WS_URL, TIMEOUT_SECONDS

async def test_websocket():
    print(f"Conectando a {WS_URL}...")
    try:
        async with websockets.connect(WS_URL) as websocket:
            print("Conexión establecida!")

            # Enviar un mensaje de prueba
            message = '{"cmd": "reg", "deviceId": "12345"}'
            print(f"Enviando mensaje: {message}")
            await websocket.send(message)

            # Esperar respuesta del servidor (opcional)
            response = await websocket.recv()
            print(f"Mensaje recibido: {response}")

    except Exception as e:
        print(f"Error: {e}")

# Ejecutar
asyncio.run(test_websocket())
