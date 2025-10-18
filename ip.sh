#!/bin/bash
IP="192.168.1.225"
START=1
END=1024

echo "🔍 Escaneando puertos abiertos en $IP del $START al $END..."
for PORT in $(seq $START $END); do
  (echo > /dev/tcp/$IP/$PORT) >/dev/null 2>&1 && echo "✅ Puerto $PORT abierto" &
done
wait
echo "✅ Escaneo completado."
