USERS = {
    "User1": "TechnicalChallengePromptior",
    "User2": "TechnicalChallengePromptior",
}


def authenticate(username: str, password: str) -> bool:
    return USERS.get(username) == password
