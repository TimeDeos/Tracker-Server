from flask import Flask, request
import requests
import time
import threading

koala = Flask(__name__)

timeout = 3600  # 1 hour in seconds

# logic to get webhooks through ur shitty github account or whatever ill do that later
# for now, i have a static webhook url hehe

githuburl = "https://raw.githubusercontent.com/TimeDeos/Tracker/main/Data.json"
r = requests.get(githuburl)
githubdata = r.json()
gemrates = githubdata['exchangeRate']['Gems']
rerolls = githubdata['exchangeRate']['Rerolls']
webhookurl1 = githubdata['webhookLinks']['Gato1']
webhookurl2 = githubdata['webhookLinks']['Gato2']
webhookurl3 = githubdata['webhookLinks']['Gato3']
webhookurl4 = githubdata['webhookLinks']['Gato4']

print(f''' Loaded data:
Webhook 1 : {webhookurl1}
Webhook 2 : {webhookurl2}
Webhook 3 : {webhookurl3}
Webhook 4 : {webhookurl4}

gems exchange rate : {gemrates}
reroll exchange rate : {rerolls}
''')

# Function to send embeds to Discord webhooks
def sendEmbed(url, data):
    r = requests.post(url, json=data)
    print(f"sendEmbed func debug: {r.status_code}, {r.text}")

# Define routes to cache the data using API

@koala.route('/gato1', methods=['POST'])
def gato1():
    data = request.json
    payload = data.get('content')
    with open("gato1.txt", "w") as file:
        file.write(payload)
    return 'koala', 200

@koala.route('/gato2', methods=['POST'])
def gato2():
    data = request.json
    payload = data.get('content')
    with open("gato2.txt", "w") as file:
        file.write(payload)
    return 'koala', 200

@koala.route('/gato3', methods=['POST'])
def gato3():
    data = request.json
    payload = data.get('content')
    with open("gato3.txt", "w") as file:
        file.write(payload)
    return 'koala', 200

@koala.route('/gato4', methods=['POST'])
def gato4():
    data = request.json
    payload = data.get('content')
    with open("gato4.txt", "w") as file:
        file.write(payload)
    return 'koala', 200

# Function to handle hourly cache updates
def hourlyCache():
    while True:
        time.sleep(timeout)
        for i in range(1, 5):
            try:
                with open(f"gato{i}.txt", 'r') as file:
                    content = file.read()
                embed = {
                    "content": "@everyone",
                    "embeds": [
                        {
                            "title": "Gato Status - Anime Defender",
                            "description": content,
                            "color": 5814783,
                            "footer": {
                                "text": f"Current Rate: | Gems: {gemrates}/k | Rerolls: {rerolls}/k",
                                "icon_url": "https://cdn.discordapp.com/emojis/1252850503042203739.webp?size=128&quality=lossless"
                            }
                        }
                    ]
                }
                webhook_url = globals().get(f'webhookurl{i}')
                if webhook_url:
                    sendEmbed(webhook_url, embed)
                    print('Webhook sent')
                else:
                    print(f"Webhook error for gato{i}")  # debug
                    pass
            except Exception as e:
                print(f"file error at gato{i}.txt: {e}")  # debug
                continue

# Start the thread for hourly caching
thread1 = threading.Thread(target=hourlyCache, daemon=True)
thread1.start()

koala.run('127.0.0.1', port=4545, debug=True)
