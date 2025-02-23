TOTAL_DAILY = 6
TOTAL_WEEKLY = 4


def get_response(user_input: str) -> str:
    lowered: str = user_input.lower()
    if lowered == '':
        return 'soooooo....'
    elif 'hello' in lowered:
        return 'hello'

    # --------Summary---------
