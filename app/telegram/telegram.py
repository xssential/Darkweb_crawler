import requests
BOT_TOKEN = '8079638698:AAFzIsI5C1ikXLXbSpbCZYHlYOtQId-v0Os'
CHAT_ID = '-1002178735706' # channel chat_id # '7730634302' (bot chat_id)
URL = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
DOCUMENT_URL = f'https://api.telegram.org/bot{BOT_TOKEN}/sendDocument'

def refined_text(message):
    refined_message = ''
    for key, value in message.items():
        if value != "N/A" and value != []:
            refined_message += f'*{key}*: {value}\n'
    return refined_message

def send_telegram(name, title, message):
    payload = {
    'chat_id': CHAT_ID,
    'text': f'#{name}\n\n*{title}*\n\n{refined_text(message)}',
    'parse_mode': 'Markdown'
    }
    requests.post(URL, data=payload)

def send_file_telegram(file_path):
    with open(file_path, 'rb') as file:
        payload = {'chat_id': CHAT_ID}
        files = {'document': file}
        requests.post(DOCUMENT_URL, data=payload, files=files)

def send_message(name, message):
    for title in message:
        send_telegram(name, title, message[title])