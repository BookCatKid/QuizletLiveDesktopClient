import client
import quizlet_live
from urllib.parse import urlparse

def parse_code(code: str) -> str:
    """
    Cleans up the input code by removing dashes and whitespace.
    Also verifies that it is in a valid format.
    Parses Quizlet Live join URLs as well.
    """
    code = code.strip()

    if code.startswith("http"):
        parsed = urlparse(code)
        parts = parsed.path.rstrip("/").split("/")
        if len(parts) >= 3 and parts[-2] == "live":
            code = parts[-1]
        else:
            raise ValueError("Invalid Quizlet Live URL format.")

    code = code.replace("-", "").replace(" ", "").upper()

    if not code.isalnum() or len(code) != 6:
        raise ValueError(
            "Invalid code format. Please enter a 6-character alphanumeric code or a valid Quizlet Live URL."
        )

    return code

if __name__ == "__main__":
    try:
        http_client = client.QuizletLiveClient()
        code_input = input("Enter Quizlet Live Code: ")
        result = http_client.check_game_code(parse_code(code_input))

        if result.get('valid'):
            print("\n" + "="*30)
            print(" GAME FOUND ")
            print("="*30)
            print(f"Game Code:   {result['game_code']}")
            print(f"Set ID:      {result['item_id']}")
            print(f"Socket:    {result['socket_url']}")
            print(result)

            name = input("Enter Nickname: ")
            handler = quizlet_live.QuizletGameHandler(game_info=result, person_id=http_client.person_id)
            handler.join_game(name)
        else:
            print(f"\n[FAILED] {result.get('message', result.get('error'))}")

    except Exception as e:
        print(f"\n[CRITICAL ERROR] {e}")
