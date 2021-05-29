import json
import os
import urllib.request

from dotenv import load_dotenv
from opengsq.protocols import A2S

load_dotenv()

steam_api_key = os.environ['STEAM_API_KEY']
appid = 440

servers = []

with urllib.request.urlopen(f'http://api.steampowered.com/IGameServersService/GetServerList/v1/?key={steam_api_key}&filter=appid\\{appid}\\empty\\1&limit=100') as f:
    server_list = json.loads(f.read().decode('latin-1').encode('utf-8'))['response']['servers']
    server_list = sorted(server_list, key=lambda s: s['players'], reverse=True)[:3]

    for server in server_list:
        subs = server['addr'].split(':')
        servers.append(A2S(address=subs[0], query_port=int(subs[1]), timeout=5.0, engine=A2S.SOURCE))

def test_query():
    for server in servers:
        print(server.query().to_json(indent=4))

def test_get_info():
    for server in servers:
        print(server.get_info())

def test_get_players():
    for server in servers:
        print(server.get_players())

def test_get_rules():
    for server in servers:
        print(server.get_rules())
