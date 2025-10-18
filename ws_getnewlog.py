import asyncio
import websockets
import json
from datetime import datetime

# ------------------- CONFIGURACIÓN -------------------
WS_URL = "ws://telemetriaperu.com:7788/ws"
TIMEOUT = 5

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
    """Envía el mensaje de registro del dispositivo"""
    reg_msg = json.dumps(VALID_REGISTER)
    print("\n➡️ Enviando registro del dispositivo...")
    await ws.send(reg_msg)
    try:
        response = await asyncio.wait_for(ws.recv(), timeout=TIMEOUT)
        print("📩 Respuesta de registro recibida:")
        print(response)
    except asyncio.TimeoutError:
        print("⚠️ No se recibió respuesta al registro.")


def generar_logs(desde, cantidad):
    """Genera registros de ejemplo simulando logs del dispositivo"""
    logs = []
    for i in range(desde, desde + cantidad):
        logs.append({
            "enrollid": i + 1,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "mode": i % 3,  # alterna entre 0 (huella), 1 (tarjeta), 2 (contraseña)
            "inout": i % 2,  # 0: entrada, 1: salida
            "event": 0 if i % 2 == 0 else 1
        })
    return logs


async def responder_getnewlog(ws, stn):
    """Simula respuesta del dispositivo al comando getnewlog"""
    if stn:  # primer paquete solicitado por el servidor
        logs = generar_logs(0, 50)
        response = {
            "ret": "getnewlog",
            "result": True,
            "count": len(logs),
            "from": 0,
            "to": 49,
            "record": logs
        }
        print("📤 Enviando primer paquete de logs (0-49)...")
        await ws.send(json.dumps(response, ensure_ascii=False))
    else:  # segundo paquete o fin
        logs = generar_logs(50, 50)
        response = {
            "ret": "getnewlog",
            "result": True,
            "count": len(logs),
            "from": 50,
            "to": 99,
            "record": logs
        }
        print("📤 Enviando segundo paquete de logs (50-99)...")
        await ws.send(json.dumps(response, ensure_ascii=False))

        # Enviar mensaje final del servidor indicando que ya terminó la descarga
        end_response = {
            "ret": "getnewlog",
            "result": True,
            "count": 0,
            "from": 0,
            "to": 0,
            "record": []
        }
        print("📤 Enviando confirmación final de que no hay más logs...")
        await ws.send(json.dumps(end_response, ensure_ascii=False))


async def handle_server_message(ws, message):
    """Procesa mensajes del servidor"""
    try:
        data = json.loads(message)
    except json.JSONDecodeError:
        print("⚠️ Mensaje inválido (no es JSON):", message)
        return

    cmd = data.get("cmd") or data.get("ret") or "unknown"

    print(f"\n📨 Mensaje recibido: cmd={cmd}")
    print(json.dumps(data, indent=2))

    # --- GETNEWLOG ---
    if cmd == "getnewlog":
        stn = data.get("stn", False)
        await responder_getnewlog(ws, stn)
        print("✅ Respuesta a GETNEWLOG enviada correctamente.")
        return

    # --- Otros comandos (ejemplo) ---
    elif cmd == "setuserinfo":
        response = {"ret": "setuserinfo", "result": True}
        await ws.send(json.dumps(response))
        print("✅ Respuesta a setuserinfo enviada.")
        return

    else:
        print("ℹ️ Comando no reconocido o no implementado, ignorando.")


async def message_consumer(ws, queue):
    """Consume mensajes de la cola"""
    while True:
        message = await queue.get()
        await handle_server_message(ws, message)
        queue.task_done()


async def run():
    print(f"🔗 Conectando a {WS_URL} ...")
    try:
        async with websockets.connect(WS_URL) as ws:
            print("✅ Conexión establecida con el servidor WebSocket")

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
