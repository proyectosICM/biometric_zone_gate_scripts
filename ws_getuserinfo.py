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

async def send_getuserinfo(ws, enrollid: int, backupnum: int):
    """Envía la solicitud getuserinfo al dispositivo"""
    msg = {
        "cmd": "getuserinfo",
        "enrollid": enrollid,
        "backupnum": backupnum
    }
    print("\n➡ Enviando comando GET USER INFO:")
    print(msg)
    await ws.send(json.dumps(msg))

async def run():
    print(f"🔗 Conectando a {WS_URL} ...")
    try:
        async with websockets.connect(WS_URL) as ws:
            print("✅ Conexión establecida")

            # --- 1️⃣ REGISTRAR DISPOSITIVO ---
            reg_msg = json.dumps(VALID_REGISTER)
            print("\n➡ Enviando registro del dispositivo:")
            print(reg_msg)
            await ws.send(reg_msg)

            try:
                reg_response = await asyncio.wait_for(ws.recv(), timeout=TIMEOUT)
                print("📩 Respuesta de registro:")
                print(reg_response)
            except asyncio.TimeoutError:
                print("⚠ No se recibió respuesta de registro en el tiempo esperado.")
                return

            # --- 2️⃣ Esperar y procesar mensajes del servidor ---
            print("\n⏳ Esperando mensajes del servidor...")
            while True:
                try:
                    message = await ws.recv()
                    print("📨 Mensaje recibido del servidor:", message)

                    try:
                        data = json.loads(message)
                        cmd = data.get("cmd")
                    except Exception as e:
                        print("⚠ No se pudo parsear el JSON:", e)
                        continue

                    # --- 3️⃣ Procesar getuserlist (si el servidor lo solicita) ---
                    if cmd == "getuserlist":
                        stn = data.get("stn", False)
                        print(f"\n🧾 Solicitud GETUSERLIST recibida (stn={stn})")
                        # Aquí podrías reenviar los paquetes si quieres simular
                        # omitido por simplicidad

                    # --- 4️⃣ Procesar getuserinfo ---
                    elif cmd == "getuserinfo":
                        # El servidor pide información de un usuario
                        enrollid = data.get("enrollid")
                        backupnum = data.get("backupnum")
                        print(f"\n🧾 Solicitud GETUSERINFO recibida (enrollid={enrollid}, backupnum={backupnum})")

                        # Simular respuesta del terminal
                        response = {
                            "ret": "getuserinfo",
                            "result": True,
                            "enrollid": enrollid,
                            "name": f"Usuario{enrollid}",
                            "backupnum": backupnum,
                            "admin": 0,
                            "record": "simulated_record_data"
                        }
                        await ws.send(json.dumps(response))
                        print("📩 Respuesta enviada al servidor:")
                        print(response)

                    else:
                        print("ℹ Comando no reconocido:", cmd)

                except websockets.ConnectionClosed:
                    print("🔌 Conexión cerrada por el servidor.")
                    break

    except Exception as ex:
        print("❌ Error general:", ex)


if __name__ == "__main__":
    asyncio.run(run())
