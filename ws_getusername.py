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
    "sn": "ZX0006827500",  # Número de serie del dispositivo simulado
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
    """Envía el mensaje de registro inicial del dispositivo."""
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
    """Procesa los mensajes enviados por el servidor."""
    try:
        data = json.loads(message)
    except json.JSONDecodeError:
        print("⚠️ Mensaje inválido (no JSON):", message)
        return

    cmd = data.get("cmd") or data.get("ret") or "unknown"
    print(f"\n📨 Mensaje recibido del servidor: cmd={cmd}")
    print(json.dumps(data, indent=2))

    # ==========================================================
    # 🔹 1️⃣ Comando DELETE USER
    # ==========================================================
    if cmd == "deleteuser":
        enrollid = data.get("enrollid")
        backupnum = data.get("backupnum")

        print("🗑️  El servidor solicita ELIMINAR usuario del dispositivo:")
        print(f"   ➤ EnrollID = {enrollid}")
        print(f"   ➤ BackupNum = {backupnum} (0–9=huella, 10=password, 11=RFID)")

        # Simular respuesta
        if SIMULAR_ERROR:
            response = {"ret": "deleteuser", "result": False, "reason": 1}
        else:
            response = {"ret": "deleteuser", "result": True}

        await asyncio.sleep(1)
        await ws.send(json.dumps(response))

        print("📤 Respuesta enviada al servidor:")
        print(json.dumps(response, indent=2))

    # ==========================================================
    # 🔹 2️⃣ Comando GET USER NAME
    # ==========================================================
    elif cmd == "getusername":
        enrollid = data.get("enrollid")

        print(f"🧩 El servidor solicita NOMBRE DE USUARIO con enrollid={enrollid}")

        # Simular respuesta
        if SIMULAR_ERROR:
            response = {"ret": "getusername", "result": False, "reason": 1}
        else:
            response = {
                "ret": "getusername",
                "result": True,
                "record": "chingzou"  # nombre del usuario en texto UTF-8
            }

        await asyncio.sleep(1)
        await ws.send(json.dumps(response))
        print("📤 Respuesta enviada al servidor:")
        print(json.dumps(response, indent=2))

    # ==========================================================
    # 🔹 Otros comandos (opcional)
    # ==========================================================
    elif cmd == "setuserinfo":
        print("ℹ️ Comando setuserinfo recibido (omitido en este simulador).")

    elif cmd == "getuserinfo":
        print("ℹ️ Comando getuserinfo recibido (omitido en este simulador).")

    else:
        print("⚙️ Comando no reconocido, ignorando.")


async def message_consumer(ws, queue):
    """Procesa los mensajes en orden."""
    while True:
        message = await queue.get()
        await handle_server_message(ws, message)
        queue.task_done()


async def run():
    print(f"🔗 Conectando a {WS_URL} ...")
    try:
        async with websockets.connect(WS_URL) as ws:
            print("✅ Conexión establecida con el servidor")

            # --- Registro inicial ---
            await send_registration(ws)

            # --- Cola para mensajes ---
            queue = asyncio.Queue()
            asyncio.create_task(message_consumer(ws, queue))

            print("\n⏳ Esperando comandos del servidor (Ctrl+C para salir)...")

            # --- Escuchar indefinidamente ---
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
