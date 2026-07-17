USERS = {
    "User1": "TechnicalChallengePromtior",
    "User2": "TechnicalChallengePromtior",
}


def authenticate(username: str, password: str) -> bool:
    return USERS.get(username) == password
