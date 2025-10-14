import asyncio
import websockets
import json
from datetime import datetime

WS_URL = "ws://telemetriaperu.com:7788/ws"

# Cambia aquí: "fingerprint" | "rfid" | "password" | "invalid" | "malformed"
MESSAGE_MODE = "fingerprint"

# ------------------- REGISTRO DEL DISPOSITIVO -------------------
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
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
}

# ------------------- SENDUSER MENSAJES -------------------

FINGERPRINT_USER = {
    "cmd": "senduser",
    "enrollid": 1,
    "name": "chingzou",
    "backupnum": 0,     # 0~9 fingerprint
    "admin": 0,
    "record": "kajgksjgaglas"  # string <1620
}

RFID_USER = {
    "cmd": "senduser",
    "enrollid": 2,
    "name": "maria",
    "backupnum": 11,   # 11 = tarjeta
    "admin": 0,
    "record": "2352253"
}

PASSWORD_USER = {
    "cmd": "senduser",
    "enrollid": 3,
    "name": "juan",
    "backupnum": 10,   # 10 = contraseña
    "admin": 0,
    "record": "12345678"
}

INVALID_USER = {
    "cmd": "senduser",
    "name": "usuario_sin_enrollid",
    "backupnum": 0
}

MALFORMED_JSON = '{"cmd": "senduser", "enrollid": 1, "name": "bad_json"'  # sin cierre


async def run(mode: str):
    print(f"🔗 Conectando a {WS_URL} ... (modo: {mode})")
    try:
        async with websockets.connect(WS_URL) as ws:
            print("✅ Conexión establecida")

            # --- 1️⃣ REGISTRAR EL DISPOSITIVO ---
            reg_msg = json.dumps(VALID_REGISTER)
            print("\n➡ Enviando registro del dispositivo:")
            print(reg_msg)
            await ws.send(reg_msg)

            try:
                reg_response = await asyncio.wait_for(ws.recv(), timeout=5)
                print("📩 Respuesta de registro:")
                print(reg_response)
            except asyncio.TimeoutError:
                print("⚠ No se recibió respuesta de registro en 5 segundos.")
                return

            # --- 2️⃣ ENVIAR USUARIO SEGÚN EL MODO ---
            if mode == "fingerprint":
                payload = FINGERPRINT_USER
            elif mode == "rfid":
                payload = RFID_USER
            elif mode == "password":
                payload = PASSWORD_USER
            elif mode == "invalid":
                payload = INVALID_USER
            elif mode == "malformed":
                payload = None
            else:
                print("❌ Modo desconocido. Usa 'fingerprint', 'rfid', 'password', 'invalid' o 'malformed'.")
                return

            if mode != "malformed":
                msg = json.dumps(payload)
                print(f"\n➡ Enviando mensaje {mode.upper()}:")
                print(msg)
                await ws.send(msg)
            else:
                print("\n➡ Enviando JSON malformado:")
                print(MALFORMED_JSON)
                await ws.send(MALFORMED_JSON)

            # --- 3️⃣ RECIBIR RESPUESTA DE SENDUSER ---
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=5)
                print("\n📩 Respuesta cruda del servidor:")
                print(response)

                try:
                    resp_json = json.loads(response)
                    if resp_json.get("ret") == "senduser" and resp_json.get("result") is False:
                        print("❌ Respuesta: FALLIDO (detalle):")
                        print(json.dumps(resp_json, indent=2, ensure_ascii=False))
                    elif resp_json.get("ret") == "senduser" and resp_json.get("result") is True:
                        print("✅ Respuesta: EXITOSO (detalle):")
                        print(json.dumps(resp_json, indent=2, ensure_ascii=False))
                    else:
                        print("ℹ Respuesta (otro formato):")
                        print(json.dumps(resp_json, indent=2, ensure_ascii=False))
                except Exception as e:
                    print("⚠ No se pudo parsear la respuesta como JSON:", e)

            except asyncio.TimeoutError:
                print("⚠ Timeout: no llegó respuesta en 5 segundos.")

            # --- 4️⃣ MANTENER CONEXIÓN ABIERTA ---
            print("\n⏳ Manteniendo conexión abierta, escuchando mensajes...")
            while True:
                try:
                    msg = await ws.recv()
                    print("📨 Mensaje recibido del servidor:", msg)
                except websockets.ConnectionClosed:
                    print("🔌 Conexión cerrada por el servidor.")
                    break

    except Exception as ex:
        print("❌ Error de conexión / envío:", ex)


if __name__ == "__main__":
    asyncio.run(run(MESSAGE_MODE))
