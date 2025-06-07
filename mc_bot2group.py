import socket
import json
import re
import requests
import threading
import time
import random
import string
from datetime import datetime

# === CONFIGURAZIONE ===

# IP locale dove il socket UDP è in ascolto (es. "0.0.0.0" per tutte le interfacce)
LISTEN_IP = "0.0.0.0"
PORT = 1799 # i pacchetti provenienti dal nodo lora meshcom

# Prefisso richiesto nel campo "dst"
MCC_GROUP = "222" # ex. 262...
SRC_CALLSIGN = "CALL-12" # per formattazione pacchetto, ma esce con il nominativo del gateway/nodo

# IP remoto a cui inviare i comandi ricevuti da Telegram
REMOTE_IP = "123.123.123.123"
# se stessa rete codice e nodo, usa 1799
REMOTE_PORT = 1798 # CONTROLLA CHE DST-NAT NEL FW/NAT GIRI IL PACCHETTO ALLA 1799 DELLA SCHEDA LORA

# --- TELEGRAM ---
TELEGRAM_BOT_TOKEN = "__YOUR_TOKEN_FROM_BOTFATHER__"
TELEGRAM_CHAT_ID = "-1001122334455"

# Polling interval (secondi) per ricevere messaggi dal bot
POLL_INTERVAL = 3

def genera_msg_id(lunghezza=8):
    caratteri = string.ascii_letters.upper() + string.digits
    stringa_casual = ''.join(random.choice(caratteri) for i in range(lunghezza))
    return stringa_casual

def is_valid_dst(dst: str) -> bool:
    # Controlla che il campo dst sia valido: inizi con MCC_GROUP e massimo 5 cifre
    return dst.startswith(MCC_GROUP) and re.fullmatch(r"\d{3,5}", dst) is not None


def send_to_telegram(text: str) -> None:
    # Invia un messaggio formattato al BOT Telegram.
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
    # Costruisce il messaggio in JSON e lo invia via UDP a REMOTE_IP:REMOTE_PORT
    msgid = genera_msg_id() # 8 lettere/numeri casuali
    payload = {
        "src_type": "lora",
        "type"    : "msg",
        "src"     : SRC_CALLSIGN, # esce sempre con il callsign del nodo/gateway remoto, questo campo è inutile al momento
        "dst"     : dst,
        "msg"     : msg,
        "msg_id"  : msgid,
        "firmware": 0,
        "fw_sub"  : "#"
    }
    try:
        sock_invio = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock_invio.sendto(json.dumps(payload).encode(), (REMOTE_IP, REMOTE_PORT))
        current_dateTime = datetime.now()
        print(f"Inviato ({current_dateTime}) via UDP a {REMOTE_IP}:{REMOTE_PORT} -> {payload}")
        sock_invio.close()
    except Exception as e:
        print(f"Errore nell'invio UDP: {e}")

def udp_listener():
    # Thread per ricezione messaggi UDP e inoltro su Telegram
    print(f"In ascolto su UDP {LISTEN_IP}:{PORT}...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((LISTEN_IP, PORT))

    while True:
        try:
            data, addr = sock.recvfrom(4096)
            print(f"Dati ricevuti da {addr}: {data.decode(errors='ignore')}")

            try:
                payload = json.loads(data.decode()) # pacchetto dati arrivato dal nodo

                if payload.get("type") == "msg" and "dst" in payload and "msg" in payload and "src" in payload:
                    # ci interessano solo questi tre campi da inviare al bot, se si tratta di un messaggio
                    dst = payload["dst"]
                    src = payload["src"]
                    msg = payload["msg"]

                    if is_valid_dst(dst):
                        text = f"Gruppo:{dst} Origine:{src}\n{msg}"
                        print(f"Inoltro a Telegram: {text}")
                        send_to_telegram(text)
                    else:
                        print(f"ATTENZIONE: 'dst' non valido: {dst}") # non è un pacchetto contenente un messaggio
                else:
                    print("ATTENZIONE: Payload non conforme.")
            except json.JSONDecodeError:
                print("ATTENZONE: Dati ricevuti non in formato JSON.")
        except Exception as e:
            print(f"Errore ricezione UDP: {e}")


def telegram_command_listener():
    # Thread che interroga periodicamente il BOT Telegram per comandi
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
                        continue  # ignora altri utenti

                    # Cerca comandi in formato: /22201 messaggio
                    match = re.match(r'^/(\d{3,5})\s+(.*)', text.strip())
                    if match:
                        dst = match.group(1)
                        msg = match.group(2)

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
    # Avvio listener UDP e listener Telegram su due thread separati
    threading.Thread(target=udp_listener, daemon=True).start()
    threading.Thread(target=telegram_command_listener, daemon=True).start()

    # Mantiene il programma vivo
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Interrotto dall'utente.")


if __name__ == "__main__":
    main()
