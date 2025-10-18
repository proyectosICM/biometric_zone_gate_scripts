import asyncio
import websockets
import json
from datetime import datetime, timedelta

# -------------------------------------------------
# CONFIGURACIÓN
# -------------------------------------------------
WS_URL = "ws://telemetriaperu.com:7788/ws"
TIMEOUT = 5
DEVICE_SN = "ZX0006827500"

# -------------------------------------------------
# REGISTRO DEL DISPOSITIVO
# -------------------------------------------------
VALID_REGISTER = {
    "cmd": "reg",
    "sn": DEVICE_SN,
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

# -------------------------------------------------
# FUNCIONES AUXILIARES
# -------------------------------------------------
def generar_logs_realistas():
    """
    Genera 30 registros (entradas/salidas) de prueba
    para usuarios 1, 4 y 5 con fechas recientes.
    """
    logs = []
    usuarios = [1, 4, 5]
    base_date = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)

    for user_id in usuarios:
        for i in range(5):
            fecha = base_date - timedelta(days=i)

            entrada = fecha + timedelta(minutes=user_id * 2)
            salida = entrada + timedelta(hours=8)

            logs.append({
                "enrollid": user_id,
                "time": entrada.strftime("%Y-%m-%d %H:%M:%S"),
                "mode": 0,  # huella
                "inout": 0,  # entrada
                "event": 0
            })
            logs.append({
                "enrollid": user_id,
                "time": salida.strftime("%Y-%m-%d %H:%M:%S"),
                "mode": 0,
                "inout": 1,  # salida
                "event": 0
            })

    logs.sort(key=lambda x: x["time"])
    return logs


async def send_registration(ws):
    """Envía el registro inicial del dispositivo."""
    msg = json.dumps(VALID_REGISTER)
    print("\n➡️ Enviando registro del dispositivo...")
    await ws.send(msg)
    try:
        response = await asyncio.wait_for(ws.recv(), timeout=TIMEOUT)
        print("📩 Respuesta de registro recibida:")
        print(response)
    except asyncio.TimeoutError:
        print("⚠️ No se recibió respuesta al registro.")


# -------------------------------------------------
# MANEJO DE COMANDOS DEL SERVIDOR
# -------------------------------------------------
async def responder_getalllog(ws, stn):
    """
    Simula respuesta al comando getalllog.
    Envía los logs en paquetes de 10 registros hasta agotarlos.
    """
    logs = generar_logs_realistas()
    chunk_size = 10
    paquetes = [logs[i:i + chunk_size] for i in range(0, len(logs), chunk_size)]

    # Control de índice de paquete (se mantiene entre llamadas)
    if not hasattr(responder_getalllog, "index"):
        responder_getalllog.index = 0

    if stn:
        print("🔁 Reiniciando secuencia de paquetes (stn=true)")
        responder_getalllog.index = 0

    if responder_getalllog.index < len(paquetes):
        paquete = paquetes[responder_getalllog.index]
        response = {
            "ret": "getalllog",
            "result": True,
            "count": len(paquete),
            "from": responder_getalllog.index * chunk_size,
            "to": responder_getalllog.index * chunk_size + len(paquete) - 1,
            "record": paquete
        }

        print(f"📤 Enviando paquete #{responder_getalllog.index + 1} "
              f"({response['from']}–{response['to']}) con {len(paquete)} registros...")
        await ws.send(json.dumps(response, ensure_ascii=False))
        responder_getalllog.index += 1

    else:
        # No hay más registros
        end_response = {
            "ret": "getalllog",
            "result": True,
            "count": 0,
            "from": 0,
            "to": 0,
            "record": []
        }
        print("📭 No hay más registros, enviando respuesta final...")
        await ws.send(json.dumps(end_response, ensure_ascii=False))
        responder_getalllog.index = 0


async def handle_server_message(ws, message):
    """Procesa los mensajes recibidos del servidor."""
    try:
        data = json.loads(message)
    except json.JSONDecodeError:
        print("⚠️ Mensaje no es JSON válido:", message)
        return

    cmd = data.get("cmd") or data.get("ret") or "unknown"
    print(f"\n📨 Mensaje recibido: cmd={cmd}")
    print(json.dumps(data, indent=2, ensure_ascii=False))

    if cmd == "getalllog":
        stn = data.get("stn", False)
        await responder_getalllog(ws, stn)
        print("✅ Respuesta a GETALLLOG enviada correctamente.")
    else:
        print("ℹ️ Comando no implementado, ignorando.")


# -------------------------------------------------
# LOOP PRINCIPAL
# -------------------------------------------------
async def message_consumer(ws, queue):
    """Procesa mensajes del servidor en segundo plano."""
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


# -------------------------------------------------
# EJECUCIÓN
# -------------------------------------------------
if __name__ == "__main__":
    asyncio.run(run())
