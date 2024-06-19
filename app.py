from flask import Flask, request, jsonify
import requests
import threading
import time
from datetime import datetime, timedelta
import pytz
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

# Fetch conversion rates from GitHub
conversion_url = 'https://raw.githubusercontent.com/TimeDeos/Tracker/main/Data.json'
response = requests.get(conversion_url)
if response.status_code == 200:
    conversion_data = response.json()
    GEMS_RATE = conversion_data['exchangeRate']['Gems']
    RR_RATE = conversion_data['exchangeRate']['Rerolls']
    print(f"Successfully fetched conversion rates: GEMS_RATE={GEMS_RATE}, RR_RATE={RR_RATE}")
else:
    GEMS_RATE = 0.05  # Default value
    RR_RATE = 6.0  # Default value
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

    total_string = f"Total: <:diamond:1244316023708979271> {total_gems:,} ; <:rr:1244982385242804304> {total_rr:,}\n"
    data_string = "\n".join([
        f"[{data['level']}] {username} - <:diamond:1244316023708979271> {data['gems']:,} <:rr:1244982385242804304> {data['rr']}"
        for username, data in combined_data.items()
    ])

    gmt_plus_7 = pytz.timezone('Asia/Bangkok')
    current_time_gmt_plus_7 = datetime.now(gmt_plus_7)
    formatted_time = current_time_gmt_plus_7.strftime('%H:%M:%S | %Y-%m-%d')

    embed = {
        "title": "Gato Status - Combined Data",
        "description": total_string + data_string,
        "color": 5814783,
        "footer": {
            "text": f"Current Rate: | Gems: {GEMS_RATE}/k | Rerolls: {RR_RATE}/k",
            "icon_url": "https://cdn.discordapp.com/emojis/1252850503042203739.webp?size=128&quality=lossless"
        },
    }

    send_webhook(embed, webhook_url_1)
    send_webhook(embed, webhook_url_2)
    send_webhook(embed, webhook_url_3)

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
        # Calculate the time until the next full hour
        now = datetime.now()
        next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        time_to_next_hour = (next_hour - now).seconds
        time.sleep(time_to_next_hour)  # Sleep until the next full hour

        print("Supposed to send..")

        for user_data, previous_user_data, webhook_url in [
            (user_data_1, previous_user_data_1, webhook_url_1),
            (user_data_2, previous_user_data_2, webhook_url_2),
            (user_data_3, previous_user_data_3, webhook_url_3)
        ]:
            inactive_users = []
            gains = {}
            total_gems_gained = 0
            total_rr_gained = 0
            total_gems = 0
            total_rr = 0

            for username, current_data in user_data.items():
                previous_data = previous_user_data.get(username, {'gems': current_data['gems'], 'rr': current_data['rr']})
                gems_gained = current_data['gems'] - previous_data['gems']
                rr_gained = current_data['rr'] - previous_data['rr']
                gains[username] = {'gems': gems_gained, 'rr': rr_gained}
                total_gems_gained += gems_gained
                total_rr_gained += rr_gained
                total_gems += current_data['gems']
                total_rr += current_data['rr']

                if (datetime.now() - current_data.get('last_updated', datetime.now())) > timedelta(seconds=timeout):
                    inactive_users.append(username)

            previous_user_data.update({username: {'gems': data['gems'], 'rr': data['rr']} for username, data in user_data.items()})

            gems_per_hour = total_gems_gained
            rr_per_hour = total_rr_gained
            dollars_per_hour_gems = (gems_per_hour / 1000) * GEMS_RATE
            dollars_per_hour_rr = (rr_per_hour / 1000) * RR_RATE
            total_dollars_per_hour = dollars_per_hour_gems + dollars_per_hour_rr

            total_string = f"Total: <:diamond:1244316023708979271> {total_gems:,} ; <:rr:1244982385242804304> {total_rr:,}\n"
            data_string = "\n".join([
                f"[{current_data['level']}] {username} - <:diamond:1244316023708979271> {current_data['gems']:,} <:rr:1244982385242804304> {current_data['rr']} [+{gains[username]['gems']:,};+{gains[username]['rr']}]"
                if username not in inactive_users
                else f"⚠️[{current_data['level']}] {username} - No Connection/Crashed"
                for username, current_data in user_data.items()
            ])

            stats_string = (
                f"\n\n**<:diamond:1244316023708979271> Per Hour:** {gems_per_hour:,}\n"
                f"**<:rr:1244982385242804304> Per Hour:** {rr_per_hour:,}\n"
                f"**<:diamond:1244316023708979271> USD Per Hour:** ${dollars_per_hour_gems:.2f}\n"
                f"**<:rr:1244982385242804304> USD Per Hour:** ${dollars_per_hour_rr:.2f}\n"
                f"**Total USD Per Hour:** ${total_dollars_per_hour:.2f}\n"
                f"\n**Inactive Users:**\n" + "\n".join([f"{username}" for username in inactive_users]) + "\n"
            )

            gmt_plus_7 = pytz.timezone('Asia/Bangkok')
            current_time_gmt_plus_7 = datetime.now(gmt_plus_7)
            formatted_time = current_time_gmt_plus_7.strftime('%H:%M:%S | %Y-%m-%d')

            embed = {
                "title": f"Gato Status - {formatted_time}",
                "description": total_string + data_string + stats_string,
                "color": 5814783,
                "footer": {
                    "text": f"Current Rate: | Gems: {GEMS_RATE}/k | Rerolls: {RR_RATE}/k",
                    "icon_url": "https://cdn.discordapp.com/emojis/1252850503042203739.webp?size=128&quality=lossless"
                },
            }

            send_webhook(embed, webhook_url)

# Start the background thread
thread = threading.Thread(target=post_webhook, daemon=True)
thread.start()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
