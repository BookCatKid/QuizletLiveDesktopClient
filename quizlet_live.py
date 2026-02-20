import socketio
import time
import json
import urllib.parse

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/121.0.0.0 Safari/537.36",
}

class QuizletGameHandler:
    """Handles the WebSocket connection and game state for a Quizlet Live session."""

    def __init__(self, game_info: dict = None, person_id: str = None):
        self.sio = socketio.Client(logger=True, engineio_logger=True)
        self.game_data = game_info
        self.current_state = {}
        self.is_connected = False
        self.person_id = person_id

        self.sio.on('connect', self._on_connect)
        self.sio.on('disconnect', self._on_disconnect)
        self.sio.on('current-game-state', self._on_game_state)
        self.sio.on('current-teams-and-players', self._on_teams_players)
        self.sio.on('game-error', self._on_error)

        self.sio.on('matchteam.new-streak', self._on_streak)
        self.sio.on('matchteam.new-answer', self._on_answer)

    def join_game(self, username: str):
        """Connects to the game socket and joins the lobby as `username`."""

        if not self.game_data:
            raise RuntimeError("No game information available. Provide `game_info` when creating handler.")

        socket_base = urllib.parse.urlparse(self.game_data['socket_url']).path
        query_string = urllib.parse.urlencode({
            'gameId': self.game_data.get('game_code'),
            'token': self.game_data.get('connection_token')
        })
        connection_url = f"https://mp.quizlet.com?{query_string}"

        try:
            print(f"[*] Connecting to {connection_url}...")
            self.sio.connect(
                connection_url,
                socketio_path=socket_base,
                transports=['websocket', 'polling'],
                headers=headers
            )

            print(f"[*] Joining lobby as '{username}'...")
            self.sio.emit('gamehub.player-join-game', {
                'username': username,
                'image': None
            })

            self.is_connected = True
            self._wait_loop()

        except Exception as e:
            print(f"[!] Connection failed: {e}")
            return False

    def _wait_loop(self):
        """Keeps the main thread alive to receive events."""
        try:
            while self.sio.connected:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[*] Disconnecting...")
            self.sio.disconnect()

    def _on_connect(self):
        print("[+] WebSocket Connected!")

    def _on_disconnect(self):
        print("[-] WebSocket Disconnected.")
        self.is_connected = False

    def _on_error(self, data):
        print(f"[!] Game Error: {data}")

    def _on_game_state(self, data):
        """Received when game status changes (Lobby -> Playing -> Ended)."""
        self.current_state.update(data)
        status = data.get('status', 'unknown')
        print(f"[*] Game State Update: {status}")

        if status == 'playing':
            print(">>> GAME STARTED! <<<")
            # This is where you would look at self.current_state['terms'] to find answers

    def _on_teams_players(self, data):
        """
        Received when teams are assigned or updated.
        """
        self.current_state['teams'] = data.get('teams', {})
        self.current_state['players'] = data.get('players', {})

        # Check if we have been assigned a team
        my_id = self.person_id

        # Find which team I am on
        my_team = None
        for team_id, team_data in self.current_state['teams'].items():
            if my_id in team_data.get('playerIds', []):
                my_team = team_data.get('mascotName', 'Unknown Team')
                break

        if my_team:
            print(f"[*] You are on team: {my_team}")

    def _on_streak(self, data):
        """Triggered when a streak updates (correct/incorrect answer)."""
        pass

    def _on_answer(self, data):
        """Triggered when an answer is submitted."""
        pass
