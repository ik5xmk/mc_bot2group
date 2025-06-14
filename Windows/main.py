import socket
import json
import re
import requests
import threading
import time
import random
import string
from datetime import datetime
import configparser
import os
import sys

# === LETTURA CONFIGURAZIONE ===

config = configparser.ConfigParser()
config.read('config.ini')

LISTEN_IP = config.get('network', 'listen_ip')
PORT = config.getint('network', 'port')

REMOTE_IP = config.get('network', 'remote_ip')
REMOTE_PORT = config.getint('network', 'remote_port')

MCC_GROUP = config.get('message', 'mcc_group')
SRC_CALLSIGN = config.get('message', 'src_callsign')

TELEGRAM_BOT_TOKEN = config.get('telegram', 'bot_token')
TELEGRAM_CHAT_ID = config.get('telegram', 'chat_id')
POLL_INTERVAL = config.getint('telegram', 'poll_interval')


def genera_msg_id(lunghezza=8):
    caratteri = string.ascii_letters.upper() + string.digits
    return ''.join(random.choice(caratteri) for _ in range(lunghezza))


def is_valid_dst(dst: str) -> bool:
    return dst.startswith(MCC_GROUP) and re.fullmatch(r"\d{3,5}", dst) is not None


def send_to_telegram(text: str) -> None:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text
    }
    try:
        response = requests.post(url, json=payload)
        if not response.ok:
            print(f"Errore Telegram: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Errore durante l'invio a Telegram: {e}")


def send_udp_message(dst: str, msg: str):
    msgid = genera_msg_id()
    payload = {
        "src_type": "lora",
        "type": "msg",
        "src": SRC_CALLSIGN,
        "dst": dst,
        "msg": msg,
        "msg_id": msgid,
        "firmware": 0,
        "fw_sub": "#"
    }
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(json.dumps(payload).encode(), (REMOTE_IP, REMOTE_PORT))
        print(f"Inviato ({datetime.now()}) via UDP a {REMOTE_IP}:{REMOTE_PORT} -> {payload}")
        sock.close()
    except Exception as e:
        print(f"Errore nell'invio UDP: {e}")


def udp_listener():
    print(f"In ascolto su UDP {LISTEN_IP}:{PORT}...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((LISTEN_IP, PORT))

    while True:
        try:
            data, addr = sock.recvfrom(4096)
            print(f"Dati ricevuti da {addr}: {data.decode(errors='ignore')}")
            try:
                payload = json.loads(data.decode())

                if payload.get("type") == "msg" and all(k in payload for k in ("dst", "msg", "src")):
                    dst = payload["dst"]
                    src = payload["src"]
                    msg = payload["msg"]

                    if is_valid_dst(dst):
                        text = f"Gruppo:{dst} Origine:{src}\n{msg}"
                        print(f"Inoltro a Telegram: {text}")
                        send_to_telegram(text)
                    else:
                        print(f"ATTENZIONE: 'dst' non valido: {dst}")
                else:
                    print("ATTENZIONE: Payload non conforme.")
            except json.JSONDecodeError:
                print("ATTENZIONE: Dati non in formato JSON.")
        except Exception as e:
            print(f"Errore ricezione UDP: {e}")


def telegram_command_listener():
    print("Inizio polling comandi Telegram...")
    last_update_id = None

    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
            if last_update_id:
                url += f"?offset={last_update_id + 1}"

            response = requests.get(url)
            if response.ok:
                data = response.json()
                for update in data.get("result", []):
                    last_update_id = update["update_id"]
                    message = update.get("message", {})
                    text = message.get("text", "")
                    chat_id = message.get("chat", {}).get("id")

                    if str(chat_id) != str(TELEGRAM_CHAT_ID):
                        continue

                    match = re.match(r'^/(\d{3,5})\s+(.*)', text.strip())
                    if match:
                        dst, msg = match.groups()
                        if is_valid_dst(dst):
                            print(f"Comando ricevuto: dst={dst}, msg={msg}")
                            send_udp_message(dst, msg)
                        else:
                            send_to_telegram("ERRORE: 'dst' non valido (deve iniziare per MCC_GROUP e max 5 cifre)")
            else:
                print(f"ERRORE polling Telegram: {response.status_code} - {response.text}")

        except Exception as e:
            print(f"ERRORE nel polling Telegram: {e}")

        time.sleep(POLL_INTERVAL)


def main():
    threading.Thread(target=udp_listener, daemon=True).start()
    threading.Thread(target=telegram_command_listener, daemon=True).start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Interrotto dall'utente.")


if __name__ == "__main__":
    main()
