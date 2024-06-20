from flask import Flask, request, jsonify
import requests
import threading
import time
from datetime import datetime, timedelta
import json
import re

app = Flask(__name__)
user_data_1 = {}
user_data_2 = {}
user_data_3 = {}
previous_user_data_1 = {}
previous_user_data_2 = {}
previous_user_data_3 = {}

# Webhook URLs
webhook_url_1 = 'https://discord.com/api/webhooks/1248280111950725222/qDyakT-1dUahZB0nlD3FGyfrqbPDH8vjxon-g3OvDGCALgGnhvGI7E8ZVU1c5nhM-Ozq'
webhook_url_2 = 'https://discord.com/api/webhooks/1250742183267663894/zWPKH9mdXFC8cB_63A3WZenlFLWrU_IAxTcTZRWP5PhUZQpyAXyW-FAE2KpWenPDdcnY'
webhook_url_3 = 'https://discord.com/api/webhooks/1252967328908447765/eZX2TbqPUJOSxaJreotfIXSVy1k5Wpcg-0pqNAocbrH10KzqWktzkCy4Hndk9E8l-3PT'
central_webhook_url = 'https://discord.com/api/webhooks/1253213159473545236/_5UTYYF-Bu6LIxM-nTA6PPpdrFdP1OC4SCiyg1tAvV4h8qRiUTMNKQiQkSjfdLB51X3t'

# Fetch conversion rates from GitHub
conversion_url = 'https://raw.githubusercontent.com/TimeDeos/Tracker/main/Data.json'
response = requests.get(conversion_url)
if response.status_code == 200:
    conversion_data = response.json()
    GEMS_RATE = conversion_data['exchangeRate']['Gems']
    RR_RATE = conversion_data['exchangeRate']['Rerolls']
    print(f"Successfully fetched conversion rates: GEMS_RATE={GEMS_RATE}, RR_RATE={RR_RATE}")
else:
    GEMS_RATE = 0.075  # Default value
    RR_RATE = 8.5  # Default value
    print("Failed to fetch conversion rates, using default values.")

# Timeout duration in seconds
timeout = 3600  # 1 hour

@app.route('/gato1', methods=['POST'])
def receive_data_1():
    data = request.get_json()
    print("Received data:", data)  # Debugging line
    process_data(data, user_data_1, previous_user_data_1)
    return jsonify({'status': 'success'}), 200

@app.route('/gato2', methods=['POST'])
def receive_data_2():
    data = request.get_json()
    print("Received data:", data)  # Debugging line
    process_data(data, user_data_2, previous_user_data_2)
    return jsonify({'status': 'success'}), 200

@app.route('/gato3', methods=['POST'])
def receive_data_3():
    data = request.get_json()
    print("Received data:", data)  # Debugging line
    process_data(data, user_data_3, previous_user_data_3)
    return jsonify({'status': 'success'}), 200

@app.route('/gato', methods=['POST'])
def combine_data():
    combined_data = combine_user_data(user_data_1, user_data_2, user_data_3)
    send_combined_webhook(combined_data)
    return jsonify({'status': 'success'}), 200

def process_data(data, user_data, previous_user_data):
    body = data.get('content', '')
    match = re.match(r'\[(\d+)\] ([^\s]+) - <:diamond:1244316023708979271> ([\d,]+) <:rr:1244982385242804304> (\d+)', body)

    if match:
        level = int(match.group(1))
        username = match.group(2)
        gems = int(match.group(3).replace(',', ''))
        rr = int(match.group(4))

        if username not in user_data:
            user_data[username] = {'gems': gems, 'rr': rr, 'level': level, 'last_updated': datetime.now()}
            previous_user_data[username] = {'gems': gems, 'rr': rr}
        else:
            user_data[username]['gems'] = gems
            user_data[username]['rr'] = rr
            user_data[username]['level'] = level
            user_data[username]['last_updated'] = datetime.now()

def combine_user_data(*data_dicts):
    combined_data = {}
    for data in data_dicts:
        for username, user_data in data.items():
            if username in combined_data:
                combined_data[username]['gems'] += user_data['gems']
                combined_data[username]['rr'] += user_data['rr']
            else:
                combined_data[username] = user_data
    return combined_data

def send_combined_webhook(combined_data):
    total_gems = sum(data['gems'] for data in combined_data.values())
    total_rr = sum(data['rr'] for data in combined_data.values())

    total_gems_gained = sum(data['gems'] - previous_user_data_1.get(username, {}).get('gems', data['gems']) for username, data in user_data_1.items())
    total_rr_gained = sum(data['rr'] - previous_user_data_1.get(username, {}).get('rr', data['rr']) for username, data in user_data_1.items())
    total_gems_gained += sum(data['gems'] - previous_user_data_2.get(username, {}).get('gems', data['gems']) for username, data in user_data_2.items())
    total_rr_gained += sum(data['rr'] - previous_user_data_2.get(username, {}).get('rr', data['rr']) for username, data in user_data_2.items())
    total_gems_gained += sum(data['gems'] - previous_user_data_3.get(username, {}).get('gems', data['gems']) for username, data in user_data_3.items())
    total_rr_gained += sum(data['rr'] - previous_user_data_3.get(username, {}).get('rr', data['rr']) for username, data in user_data_3.items())

    gems_per_hour = total_gems_gained
    rr_per_hour = total_rr_gained
    dollars_per_hour_gems = (gems_per_hour / 1000) * GEMS_RATE
    dollars_per_hour_rr = (rr_per_hour / 1000) * RR_RATE
    total_dollars_per_hour = dollars_per_hour_gems + dollars_per_hour_rr

    tracker_status = [
        f"Tracker 1: {'<:green:1018976505159749664>' if any(data['last_updated'] > datetime.now() - timedelta(seconds=timeout) for data in user_data_1.values()) else '<:red:1018976808651960320>'}",
        f"Tracker 2: {'<:green:1018976505159749664>' if any(data['last_updated'] > datetime.now() - timedelta(seconds=timeout) for data in user_data_2.values()) else '<:red:1018976808651960320>'}",
        f"Tracker 3: {'<:green:1018976505159749664>' if any(data['last_updated'] > datetime.now() - timedelta(seconds=timeout) for data in user_data_3.values()) else '<:red:1018976808651960320>'}",
    ]

    total_string = f"Total: <:diamond:1244316023708979271> {total_gems:,} ; <:rr:1244982385242804304> {total_rr:,}\n"
    tracker_string = "\n".join(tracker_status)
    stats_string = (
        f"\n\n**<:diamond:1244316023708979271> Per Hour:** {gems_per_hour:,}\n"
        f"**<:rr:1244982385242804304> Per Hour:** {rr_per_hour:,}\n"
        f"**$/Hour:** ${total_dollars_per_hour:.2f}\n"
    )

    embed = {
        "title": "Gato Status - Anime Defenders",
        "description": total_string + tracker_string + stats_string,
        "color": 5814783,
        "footer": {
            "text": f"Current Rate: | Gems: {GEMS_RATE}/k | Rerolls: {RR_RATE}/k",
            "icon_url": "https://cdn.discordapp.com/emojis/1252850503042203739.webp?size=128&quality=lossless"
        },
    }

    send_webhook(embed, central_webhook_url)

def send_webhook(embed, webhook_url, mention_everyone=False):
    headers = {
        "Content-Type": "application/json"
    }

    payload = {
        "content": "@everyone" if mention_everyone else "",
        "embeds": [embed]
    }

    response = requests.post(webhook_url, data=json.dumps(payload), headers=headers)
    print("Discord response:", response.status_code, response.content)  # Debugging line
    return response

def post_webhook():
    global previous_user_data_1, previous_user_data_2, previous_user_data_3
    while True:
        time.sleep(3600)  # 1 hour interval
        if user_data_1:
            previous_user_data_1 = user_data_1.copy()
            send_webhook(user_data_1, webhook_url_1)
        if user_data_2:
            previous_user_data_2 = user_data_2.copy()
            send_webhook(user_data_2, webhook_url_2)
        if user_data_3:
            previous_user_data_3 = user_data_3.copy()
            send_webhook(user_data_3, webhook_url_3)

        # Send the combined status to the central webhook
        combined_data = combine_user_data(user_data_1, user_data_2, user_data_3)
        send_combined_webhook(combined_data)

# Start the background thread
thread = threading.Thread(target=post_webhook, daemon=True)
thread.start()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
