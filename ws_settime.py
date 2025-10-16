import asyncio
import websockets
import json
from datetime import datetime

# ------------------- CONFIGURACIÓN -------------------
WS_URL = "ws://telemetriaperu.com:7788/ws"
TIMEOUT = 5
SIMULAR_ERROR = False  # 👈 Cambia a True para probar fallos

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

    # --- DELETE USER ---
    if cmd == "deleteuser":
        enrollid = data.get("enrollid")
        backupnum = data.get("backupnum")
        print(f"🗑️ Servidor solicita eliminar usuario: enrollid={enrollid}, backupnum={backupnum}")
        response = {"ret": "deleteuser", "result": not SIMULAR_ERROR}
        if SIMULAR_ERROR:
            response["reason"] = 1
        await asyncio.sleep(1)
        await ws.send(json.dumps(response))
        print("📤 Respuesta enviada:", json.dumps(response, indent=2))

    # --- CLEAN ADMIN ---
    elif cmd == "cleanadmin":
        print("🧹 Servidor solicita limpiar todos los administradores (convertirlos en usuarios normales).")

        response = {"ret": "cleanadmin", "result": not SIMULAR_ERROR}
        if SIMULAR_ERROR:
            response["reason"] = 1

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
            print("⚠️ Se recibieron más de 50 registros, truncando a 50 registros.")
            records = records[:50]
            count = 50

        print(f"📝 Servidor solicita actualizar nombres de usuario ({count} registros):")
        for r in records:
            print(f"   ➤ enrollid={r.get('enrollid')}, name={r.get('name')}")

        response = {"ret": "setusername", "result": not SIMULAR_ERROR}
        if SIMULAR_ERROR:
            response["reason"] = 1
        await asyncio.sleep(1)
        await ws.send(json.dumps(response))
        print("📤 Respuesta enviada:", json.dumps(response, indent=2))

    # --- SETTIME (16) ---
    elif cmd == "settime":
        cloudtime = data.get("cloudtime")
        print(f"⏰ Servidor solicita sincronizar hora del dispositivo con: {cloudtime}")

        # Aquí podrías incluso actualizar la hora del sistema (solo si es necesario y con permisos)
        # Pero en este simulador solo mostramos el log

        response = {"ret": "settime", "result": not SIMULAR_ERROR}
        if SIMULAR_ERROR:
            response["reason"] = 1

        await asyncio.sleep(1)
        await ws.send(json.dumps(response))
        print("📤 Respuesta enviada (SETTIME):", json.dumps(response, indent=2))

    # --- Otros comandos ---
    elif cmd in ["setuserinfo", "getuserinfo"]:
        print(f"ℹ️ Comando {cmd} recibido (omitido en este simulador).")

    else:
        print("⚙️ Comando no reconocido, ignorando.")

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
