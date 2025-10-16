import asyncio
import websockets
import json
from datetime import datetime

# ------------------- CONFIGURACIÓN -------------------
WS_URL = "ws://telemetriaperu.com:7788/ws"
TIMEOUT = 5
SIMULAR_ERROR = False  # 👈 Cambia a True para probar respuestas con error

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
    try:
        data = json.loads(message)
    except json.JSONDecodeError:
        print("⚠️ Mensaje inválido (no JSON):", message)
        return

    cmd = data.get("cmd") or data.get("ret") or "unknown"
    print(f"\n📨 Mensaje recibido del servidor: cmd={cmd}")
    print(json.dumps(data, indent=2))

    # --- ENABLE / DISABLE USER ---
    if cmd == "enableuser":
        enrollid = data.get("enrollid")
        enflag = data.get("enflag")
        action = "HABILITAR" if enflag == 1 else "DESHABILITAR"
        print(f"🔐 Servidor solicita {action} usuario enrollid={enrollid}")

        response = {"ret": "enableuser", "result": not SIMULAR_ERROR}
        if SIMULAR_ERROR:
            response["reason"] = 1

        await asyncio.sleep(1)
        await ws.send(json.dumps(response))
        print("📤 Respuesta enviada:", json.dumps(response, indent=2))

    # --- DELETE USER ---
    elif cmd == "deleteuser":
        enrollid = data.get("enrollid")
        print(f"🗑️ Servidor solicita eliminar usuario: enrollid={enrollid}")

        response = {"ret": "deleteuser", "result": not SIMULAR_ERROR}
        if SIMULAR_ERROR:
            response["reason"] = 1

        await asyncio.sleep(1)
        await ws.send(json.dumps(response))
        print("📤 Respuesta enviada:", json.dumps(response, indent=2))

    # --- CLEAN ALL USERS ---
    elif cmd == "cleanuser":
        print("🧹 Servidor solicita limpiar TODOS los usuarios del dispositivo.")
        response = {"ret": "cleanuser", "result": not SIMULAR_ERROR}
        if SIMULAR_ERROR:
            response["reason"] = 1

        # Simulamos proceso de borrado
        await asyncio.sleep(2)
        await ws.send(json.dumps(response))
        print("📤 Respuesta enviada al servidor:", json.dumps(response, indent=2))

    # --- GET USERNAME ---
    elif cmd == "getusername":
        enrollid = data.get("enrollid")
        print(f"🧩 Servidor solicita nombre de usuario: enrollid={enrollid}")

        response = {
            "ret": "getusername",
            "result": not SIMULAR_ERROR,
            "record": "chingzou" if not SIMULAR_ERROR else None
        }
        if SIMULAR_ERROR:
            response["reason"] = 1

        await asyncio.sleep(1)
        await ws.send(json.dumps(response))
        print("📤 Respuesta enviada:", json.dumps(response, indent=2))

    # --- SET USERNAME ---
    elif cmd == "setusername":
        count = data.get("count", 0)
        records = data.get("record", [])

        if count > 50 or len(records) > 50:
            print("⚠️ Se recibieron más de 50 registros, truncando a 50.")
            records = records[:50]
            count = 50

        print(f"📝 Servidor solicita actualizar nombres ({count} registros):")
        for r in records:
            print(f"   ➤ enrollid={r.get('enrollid')}, name={r.get('name')}")

        response = {"ret": "setusername", "result": not SIMULAR_ERROR}
        if SIMULAR_ERROR:
            response["reason"] = 1

        await asyncio.sleep(1)
        await ws.send(json.dumps(response))
        print("📤 Respuesta enviada:", json.dumps(response, indent=2))

    else:
        print("⚙️ Comando no reconocido, ignorando...")

async def message_consumer(ws, queue):
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
