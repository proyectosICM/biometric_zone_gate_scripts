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
    "sn": "ZX0006827502",
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

# ------------------- RESPUESTAS GETUSERLIST -------------------

# Primer paquete (40 usuarios máximo por paquete)
GETUSERLIST_RESPONSE_1 = {
    "ret": "getuserlist",
    "result": True,
    "count": 3,
    "from": 0,
    "to": 2,
    "record": [
        {"enrollid": 1, "admin": 0, "backupnum": 0},   # Huella
        {"enrollid": 2, "admin": 1, "backupnum": 10},  # Password
        {"enrollid": 3, "admin": 0, "backupnum": 11},  # Tarjeta RFID
    ],
}

# Segundo paquete de ejemplo (podrías no enviarlo si tienes pocos usuarios)
GETUSERLIST_RESPONSE_2 = {
    "ret": "getuserlist",
    "result": True,
    "count": 2,
    "from": 3,
    "to": 4,
    "record": [
        {"enrollid": 4, "admin": 0, "backupnum": 0},
        {"enrollid": 5, "admin": 0, "backupnum": 10},
    ],
}

# Ejemplo vacío (cuando no hay usuarios)
GETUSERLIST_EMPTY = {
    "ret": "getuserlist",
    "result": True,
    "count": 0,
    "from": 0,
    "to": 0,
    "record": [],
}


# ------------------- LÓGICA PRINCIPAL -------------------

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

            # --- 2️⃣ ESPERAR MENSAJE DEL SERVIDOR ---
            print("\n⏳ Esperando solicitud 'getuserlist' del servidor...")
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

                    # --- 3️⃣ SI EL SERVIDOR SOLICITA GETUSERLIST ---
                    if cmd == "getuserlist":
                        stn = data.get("stn", False)
                        print(f"\n🧾 Solicitud GETUSERLIST recibida (stn={stn})")

                        if stn:
                            # Primer paquete de usuarios
                            response1 = json.dumps(GETUSERLIST_RESPONSE_1)
                            print("\n➡ Enviando primer paquete de usuarios:")
                            print(response1)
                            await ws.send(response1)

                            # Servidor responde con stn:false → enviamos segundo paquete
                            await asyncio.sleep(1)
                            server_ack = {
                                "cmd": "getuserlist",
                                "stn": False
                            }
                            print("\n📩 Simulando respuesta del servidor (stn:false):")
                            print(server_ack)

                            response2 = json.dumps(GETUSERLIST_RESPONSE_2)
                            print("\n➡ Enviando segundo paquete de usuarios:")
                            print(response2)
                            await ws.send(response2)
                        else:
                            print("ℹ stn es False, no se envían más paquetes.")

                    else:
                        print("ℹ Comando no reconocido:", cmd)

                except websockets.ConnectionClosed:
                    print("🔌 Conexión cerrada por el servidor.")
                    break

    except Exception as ex:
        print("❌ Error general:", ex)


if __name__ == "__main__":
    asyncio.run(run())
