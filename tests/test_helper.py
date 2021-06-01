import json
import os
import urllib.request

from dotenv import load_dotenv

load_dotenv()


def get_master_servers_from_steam(appid, limit=1000):
    with urllib.request.urlopen(
        'http://api.steampowered.com/IGameServersService/GetServerList/v1/?key={}&filter=appid\\{}&limit={}'
        .format(os.environ['STEAM_API_KEY'], appid, limit)
    ) as f:
        # Load servers from web request
        server_list = json.loads(f.read().decode('latin-1').encode('utf-8'))['response']['servers']

        # Remove valve official servers
        server_list = [s for s in server_list if 'gametype' in s and 'valve' not in s['gametype']]

        # Sort the servers by players desc
        return sorted(server_list, key=lambda s: s['players'], reverse=True)


if __name__ == '__main__':
    print(get_master_servers_from_steam(appid=440, limit=50))
