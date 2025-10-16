import asyncio
import websockets
import json
from datetime import datetime

# ------------------- CONFIGURACIÓN -------------------
WS_URL = "ws://telemetriaperu.com:7788/ws"
TIMEOUT = 5
SIMULAR_ERROR = False  # 👈 Cambia a True para simular fallo en comandos

# ------------------- MENSAJE DE REGISTRO -------------------
VALID_REGISTER = {
    "cmd": "reg",
    "sn": "ZX0006827500",
    "devinfo": {
        "modelname": "tfs30",
        "usersize": 3000,
        "fpsize": 3000,
        "cardsize": 3000,
        "pwdsize": 3000,
        "logsize": 100000,
        "useduser": 1000,
        "usedfp": 1000,
        "usedcard": 2000,
        "usedpwd": 400,
        "usedlog": 100000,
        "usednewlog": 5000,
        "fpalgo": "thbio3.0",
        "firmware": "th600w v6.1",
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    },
}

# ------------------- FUNCIONES -------------------

async def send_registration(ws):
    """Envía mensaje de registro inicial al servidor"""
    reg_msg = json.dumps(VALID_REGISTER)
    print("\n➡️ Enviando registro del dispositivo...")
    await ws.send(reg_msg)
    try:
        response = await asyncio.wait_for(ws.recv(), timeout=TIMEOUT)
        print("📩 Respuesta de registro:")
        print(response)
    except asyncio.TimeoutError:
        print("⚠️ No se recibió respuesta al registro.")

async def handle_server_message(ws, message):
    """Procesa los comandos recibidos desde el servidor"""
    try:
        data = json.loads(message)
    except json.JSONDecodeError:
        print("⚠️ Mensaje inválido (no JSON):", message)
        return

    cmd = data.get("cmd") or data.get("ret") or "unknown"
    print(f"\n📨 Mensaje recibido del servidor: cmd={cmd}")
    print(json.dumps(data, indent=2))

    # --- COMANDO 18: GET DEV INFO ---
    if cmd == "getdevinfo":
        print("🧠 Servidor solicita parámetros del terminal (GETDEVINFO)...")

        if SIMULAR_ERROR:
            response = {"ret": "getdevinfo", "result": False, "reason": 1}
        else:
            response = {
                "ret": "getdevinfo",
                "result": True,
                "deviceid": 1,
                "language": 0,
                "volume": 0,
                "screensaver": 0,
                "verifymode": 0,
                "sleep": 0,
                "userfpnum": 3,
                "loghint": 1000,
                "reverifytime": 0
            }

        await asyncio.sleep(1)
        await ws.send(json.dumps(response))
        print("📤 Respuesta enviada al servidor (GETDEVINFO):")
        print(json.dumps(response, indent=2))

    # --- COMANDO 19: OPEN DOOR ---
    elif cmd == "opendoor":
        print("🔓 Servidor solicita abrir la puerta... (activando relay simulado)")

        response = {"ret": "opendoor", "result": not SIMULAR_ERROR}
        if SIMULAR_ERROR:
            response["reason"] = 1

        await asyncio.sleep(2)
        await ws.send(json.dumps(response))
        print("📤 Respuesta enviada al servidor (OPENDOOR):")
        print(json.dumps(response, indent=2))

    # --- COMANDO 12: CLEAN LOG ---
    elif cmd == "cleanlog":
        print("🧹 Servidor solicita limpiar todos los logs (CLEANLOG)...")

        response = {"ret": "cleanlog", "result": not SIMULAR_ERROR}
        if SIMULAR_ERROR:
            response["reason"] = 1

        await asyncio.sleep(1)
        await ws.send(json.dumps(response))
        print("📤 Respuesta enviada al servidor (CLEANLOG):")
        print(json.dumps(response, indent=2))

    else:
        print("⚙️ Comando no reconocido o no implementado en este simulador.")

async def message_consumer(ws, queue):
    """Consume mensajes recibidos en cola"""
    while True:
        message = await queue.get()
        await handle_server_message(ws, message)
        queue.task_done()

async def run():
    print(f"🔗 Conectando a {WS_URL} ...")
    try:
        async with websockets.connect(WS_URL) as ws:
            print("✅ Conexión establecida con el servidor")
            await send_registration(ws)

            queue = asyncio.Queue()
            asyncio.create_task(message_consumer(ws, queue))

            print("\n⏳ Esperando comandos del servidor (Ctrl+C para salir)...")
            while True:
                try:
                    message = await ws.recv()
                    await queue.put(message)
                except websockets.ConnectionClosed:
                    print("🔌 Conexión cerrada por el servidor.")
                    break

    except Exception as ex:
        print("❌ Error general:", ex)

if __name__ == "__main__":
    asyncio.run(run())
