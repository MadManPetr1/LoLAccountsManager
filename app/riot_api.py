# app/riot_api.py
import sqlite3
import requests
from PySide6.QtCore import QThread, Signal

class RiotUpdateThread(QThread):
    finished = Signal(list)

    def __init__(self, db_path, api_key):
        super().__init__()
        self.db_path = db_path
        self.api_key = api_key

    def run(self):
        updates = []
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT id, riot_id FROM accounts WHERE riot_id != ''")
        rows = cursor.fetchall()

        headers = {"X-Riot-Token": self.api_key}

        for row in rows:
            acc_id = row["id"]
            riot_id = row["riot_id"]
            try:
                game_name, tag = riot_id.split("#")
            except ValueError:
                continue

            puuid_resp = requests.get(
                f"https://europe.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag}",
                headers=headers,
            )
            if puuid_resp.status_code != 200:
                continue
            puuid = puuid_resp.json().get("puuid")

            summoner_resp = requests.get(
                f"https://europe.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}",
                headers=headers,
            )
            if summoner_resp.status_code != 200:
                continue
            summoner_data = summoner_resp.json()
            summoner_id = summoner_data.get("id")
            lvl = summoner_data.get("summonerLevel", 0)

            league_resp = requests.get(
                f"https://europe.api.riotgames.com/lol/league/v4/entries/by-summoner/{summoner_id}",
                headers=headers,
            )
            if league_resp.status_code != 200:
                continue
            queue_data = [
                entry for entry in league_resp.json() if entry.get("queueType") == "RANKED_SOLO_5x5"
            ]
            wins, losses, ranked_str = 0, 0, ""
            if queue_data:
                entry = queue_data[0]
                wins = entry.get("wins", 0)
                losses = entry.get("losses", 0)
                tier = entry.get("tier", "")
                rank = entry.get("rank", "")
                lp = entry.get("leaguePoints", 0)
                if tier and rank is not None:
                    ranked_str = f"{tier[0]}{rank}/{lp}LP"

            updates.append((acc_id, lvl, wins, losses, ranked_str))

        conn.close()
        self.finished.emit(updates)