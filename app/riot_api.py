# app/riot_api.py
import requests
from urllib.parse import quote
from PySide6.QtCore import QThread, Signal
from app.database import DatabaseManager, Account

# Map stored Region strings to Riot’s routing/platform values:
REGION_MAP = {
    "EUNE": "eun1",
    "EUW":  "euw1",
    "TR":   "tr1",
    "PBE":  "pbe1"
}

class RiotUpdateThread(QThread):
    """
    For each Account in SQLite, uses its stored `login` (Summoner name) to:
      1) Lookup Summoner via Summoner-V4 endpoint:
         GET /lol/summoner/v4/summoners/by-name/{summonerName}
         → returns summonerLevel + encryptedSummonerId
      2) Lookup League entries via League-V4 endpoint:
         GET /lol/league/v4/entries/by-summoner/{encryptedSummonerId}
         → find “RANKED_SOLO_5x5” entry → wins & losses

    Emits: finished(list_of_tuples)
      where each tuple is (account_id, new_level, new_wins, new_losses).
    """
    finished = Signal(list)

    def __init__(self, db_path: str, api_key: str):
        super().__init__()
        self.db_path = db_path
        self.api_key = api_key

    def run(self):
        mgr = DatabaseManager(self.db_path)
        accounts = mgr.fetch_accounts()
        updated = []
        headers = {"X-Riot-Token": self.api_key}

        for acc in accounts:
            platform = REGION_MAP.get(acc.region)
            if not platform:
                continue
            summoner_name = acc.login.strip()
            if not summoner_name:
                continue
            summoner_enc = quote(summoner_name, safe="")

            try:
                # 1) Summoner-V4: lookup Summoner by name
                url_sum = (
                    f"https://{platform}.api.riotgames.com/"
                    f"lol/summoner/v4/summoners/by-name/{summoner_enc}"
                )
                resp_sum = requests.get(url_sum, headers=headers, timeout=5)
                resp_sum.raise_for_status()
                sum_data = resp_sum.json()

                new_level = sum_data.get("summonerLevel", acc.level)
                summoner_id = sum_data.get("id")

                # 2) League-V4: lookup ranked entries by Summoner ID
                url_lg = (
                    f"https://{platform}.api.riotgames.com/"
                    f"lol/league/v4/entries/by-summoner/{quote(summoner_id, safe='')}"
                )
                resp_lg = requests.get(url_lg, headers=headers, timeout=5)
                resp_lg.raise_for_status()
                entries = resp_lg.json()  # list of dicts

                solo_entry = next(
                    (e for e in entries if e.get("queueType") == "RANKED_SOLO_5x5"),
                    None
                )
                if solo_entry:
                    new_wins = solo_entry.get("wins", acc.wins)
                    new_losses = solo_entry.get("losses", acc.losses)
                else:
                    new_wins, new_losses = acc.wins, acc.losses

                updated.append((acc.id, new_level, new_wins, new_losses))

            except requests.HTTPError:
                continue
            except requests.RequestException:
                continue
            except Exception:
                continue

        self.finished.emit(updated)