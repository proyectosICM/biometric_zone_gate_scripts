import asyncio
import websockets
import json
from datetime import datetime
from config import WS_URL, TIMEOUT_SECONDS

# Cambia aquí: "valid" | "invalid" | "malformed"
MESSAGE_MODE = "valid"

# Mensaje válido (correcto)
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

# Mensaje inválido (falta "sn")
INVALID_REGISTER = {
    "cmd": "reg",
    # "sn" intencionalmente omitido
    "devinfo": {
        "modelname": "tfs30",
        "usersize": 3000
    }
}

# Mensaje malformado (string no JSON válido)
MALFORMED_JSON = '{"cmd": "reg", "sn": "BAD_SN", "devinfo": {"modelname":"tfs30"'  # falta cierre

async def run(mode: str):
    print(f"Conectando a {WS_URL} ... (modo: {mode})")
    try:
        async with websockets.connect(WS_URL) as ws:
            print("Conexión establecida")

            if mode == "valid":
                payload = VALID_REGISTER
                msg = json.dumps(payload)
                print("➡ Enviando mensaje VALID:")
                print(msg)
                await ws.send(msg)

            elif mode == "invalid":
                payload = INVALID_REGISTER
                msg = json.dumps(payload)
                print("➡ Enviando mensaje INVALID (falta 'sn'):")
                print(msg)
                await ws.send(msg)

            elif mode == "malformed":
                msg = MALFORMED_JSON
                print("➡ Enviando MALFORMED JSON (no válido):")
                print(msg)
                await ws.send(msg)

            else:
                print("Modo desconocido. Usa 'valid', 'invalid' o 'malformed'.")
                return

            try:
                response = await asyncio.wait_for(ws.recv(), timeout=5)
                print("Respuesta cruda del servidor:")
                print(response)

                try:
                    resp_json = json.loads(response)
                    if resp_json.get("ret") == "reg" and resp_json.get("result") is False:
                        print("Respuesta: Registro FALLIDO (detalle):")
                        print(json.dumps(resp_json, indent=2, ensure_ascii=False))
                    elif resp_json.get("ret") == "reg" and resp_json.get("result") is True:
                        print("Respuesta: Registro EXITOSO (detalle):")
                        print(json.dumps(resp_json, indent=2, ensure_ascii=False))
                    else:
                        print("ℹRespuesta (otro formato):")
                        print(json.dumps(resp_json, indent=2, ensure_ascii=False))
                except Exception as e:
                    print("No se pudo parsear la respuesta como JSON:", e)

            except asyncio.TimeoutError:
                print("Timeout: no llegó respuesta en 5 segundos. El servidor puede haber cerrado la conexión.")

            # 🔄 Mantener la conexión viva sin cerrar
            print("🕓 Manteniendo la conexión abierta. Presiona Ctrl+C para salir.")
            while True:
                try:
                    # Espera mensajes del servidor, o envía ping cada 30 segundos
                    message = await asyncio.wait_for(ws.recv(), timeout=30)
                    print("📩 Mensaje recibido del servidor:", message)
                except asyncio.TimeoutError:
                    await ws.ping()
                    print("💓 Ping enviado para mantener la conexión activa")

    except Exception as ex:
        print("Error de conexión / envío:", ex)

if __name__ == "__main__":
    asyncio.run(run(MESSAGE_MODE))
