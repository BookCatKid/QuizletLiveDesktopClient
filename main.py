import client

def parse_code(code: str) -> str:
    """
    Cleans up the input code by removing dashes and whitespace.
    Also verify that it is in a valid format.
    Parse join urls as well.
    """
    code = code.replace("-", "").replace(" ", "").upper()
    if code.startswith("https://quizlet.com/live/"):
        code = code.split("/")[-1]
    if not code.isalnum() or len(code) != 6:
        raise ValueError("Invalid code format. Please enter a 6-character alphanumeric code or a valid Quizlet Live URL.")
    return code

if __name__ == "__main__":
    try:
        client = client.QuizletLiveClient()
        code_input = input("Enter Quizlet Live Code: ")
        result = client.check_game_code(parse_code(code_input))

        if result['valid']:
            print("\n" + "="*30)
            print(" GAME FOUND ")
            print("="*30)
            print(f"Game ID:   {result['game_id']}")
            print(f"Host:      {result.get('host_name', 'Hidden')}")
            print(f"Socket:    {result['socket_url']}")
        else:
            print(f"\n[FAILED] {result.get('message', result.get('error'))}")

    except Exception as e:
        print(f"\n[CRITICAL ERROR] {e}")
