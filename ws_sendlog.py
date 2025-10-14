import asyncio
import websockets
import json
from datetime import datetime

WS_URL = "ws://telemetriaperu.com:7788/ws"

# Cambia aquí: "valid" | "invalid" | "malformed"
MESSAGE_MODE = "valid"

# ------------------- REGISTRO -------------------
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

# ------------------- SENDLOG -------------------
VALID_SENDLOG = {
    "cmd": "sendlog",
    "count": 4,
    "record": [
        # Usuario 1 - Entrada
        {
            "enrollid": 1,
            "time": "2025-10-13 09:00:00",
            "mode": 0,   # 0=fp (huella)
            "inout": 0,  # 0=in
            "event": 0   # evento normal
        },
        # Usuario 1 - Salida
        {
            "enrollid": 1,
            "time": "2025-10-13 17:00:00",
            "mode": 0,
            "inout": 1,  # 1=out
            "event": 0
        },
        # Usuario 2 - Entrada
        {
            "enrollid": 4,
            "time": "2025-10-13 09:15:00",
            "mode": 0,
            "inout": 0,
            "event": 0
        },
        # Usuario 2 - Salida
        {
            "enrollid": 4,
            "time": "2025-10-13 17:10:00",
            "mode": 0,
            "inout": 1,
            "event": 0
        }
    ]
}

# Mensaje inválido (falta 'record')
INVALID_SENDLOG = {
    "cmd": "sendlog",
    "count": 2
    # record intencionalmente omitido
}

# Mensaje malformado (string no JSON válido)
MALFORMED_JSON = '{"cmd": "sendlog", "count": 2, "record": ['  # falta cierre


async def run(mode: str):
    print(f"Conectando a {WS_URL} ... (modo: {mode})")
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

            # --- 2️⃣ ENVIAR LOGS SEGÚN EL MODO ---
            if mode == "valid":
                payload = VALID_SENDLOG
                msg = json.dumps(payload)
                print("\n➡ Enviando mensaje VALID:")
                print(msg)
                await ws.send(msg)

            elif mode == "invalid":
                payload = INVALID_SENDLOG
                msg = json.dumps(payload)
                print("\n➡ Enviando mensaje INVALID (falta 'record'):")
                print(msg)
                await ws.send(msg)

            elif mode == "malformed":
                msg = MALFORMED_JSON
                print("\n➡ Enviando MALFORMED JSON (no válido):")
                print(msg)
                await ws.send(msg)

            else:
                print("Modo desconocido. Usa 'valid', 'invalid' o 'malformed'.")
                return

            # --- 3️⃣ RECIBIR RESPUESTA DE SENDLOG ---
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=5)
                print("\n📩 Respuesta cruda del servidor:")
                print(response)

                try:
                    resp_json = json.loads(response)
                    if resp_json.get("ret") == "sendlog" and resp_json.get("result") is False:
                        print("❌ Respuesta: FALLIDO (detalle):")
                        print(json.dumps(resp_json, indent=2, ensure_ascii=False))
                    elif resp_json.get("ret") == "sendlog" and resp_json.get("result") is True:
                        print("✅ Respuesta: EXITOSO (detalle):")
                        print(json.dumps(resp_json, indent=2, ensure_ascii=False))
                    else:
                        print("ℹ Respuesta (otro formato):")
                        print(json.dumps(resp_json, indent=2, ensure_ascii=False))
                except Exception as e:
                    print("No se pudo parsear la respuesta como JSON:", e)

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
