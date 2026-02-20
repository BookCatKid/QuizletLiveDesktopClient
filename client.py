from curl_cffi import requests
import json
import re

class QuizletLiveClient:
    """
    A client to interact with Quizlet Live game verification APIs.
    Uses curl_cffi to bypass Cloudflare 403 errors by impersonating Chrome.
    """

    API_VERIFY_ENDPOINT = "https://quizlet.com/webapi/3.8/multiplayer/game-instance"
    MP_BASE_URL = "https://mp.quizlet.com"

    def __init__(self):
        self.session = requests.Session(impersonate="chrome120")
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://quizlet.com/",
        })
        self.token = None
        self.person_id = None

        self._hydrate_session()

    def _hydrate_session(self):
        """
        Visits the main page to get the 'multiplayerToken' embedded in the HTML.
        """
        print("[*] Hydrating session...")

        response = self.session.get("https://quizlet.com/live")

        if response.status_code == 403:
            raise Exception("Still getting 403. Cloudflare is blocking this IP. Try using a proxy or a different network.")

        response.raise_for_status()

        match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', response.text)

        if not match:
            raise Exception("Could not find __NEXT_DATA__ in HTML. The page structure might have changed.")

        data = json.loads(match.group(1))

        try:
            self.token = data['props']['pageProps']['multiplayerToken']
            self.person_id = data['props']['pageProps']['personId']
            print(f"[*] Success! Session ID: {self.person_id}")
        except KeyError:
            print("Available keys in props:", data.get('props', {}).keys())
            raise Exception("Could not extract multiplayerToken from page data.")

    def check_game_code(self, code: str):
        """
        Verifies a game code against the Quizlet API.
        """
        if not self.token:
            self._hydrate_session()

        api_headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://quizlet.com/live",
            "CS-Token": self.session.cookies.get("qtkn", "")
        }

        print(f"[*] Verifying code: {code}...")

        try:
            response = self.session.get(
                self.API_VERIFY_ENDPOINT,
                params={"gameCode": code},
                headers=api_headers
            )

            if response.status_code == 403:
                return {"valid": False, "error": "API returned 403 Forbidden. Token might be invalid."}

            data = response.json()

            if "error" in data:
                return {
                    "valid": False,
                    "error_type": data['error'].get('type'),
                    "message": data['error'].get('message', 'Game not found')
                }

            if "gameInstance" in data:
                instance = data['gameInstance']
                server_base = instance.get('serverBasePath')

                return {
                    "valid": True,
                    "instance": instance,
                    "game_uuid": instance.get('gameInstanceUuid'),
                    "game_code": instance.get('gameCode'),
                    "item_id": instance.get('itemId'),
                    "host_name": instance.get('hostName'),
                    "socket_url": f"{self.MP_BASE_URL}/{server_base}/games/socket",
                    "connection_token": self.token
                }

            return {"valid": False, "error": "Unknown response format", "raw": data}

        except Exception as e:
            return {"valid": False, "error": str(e)}
