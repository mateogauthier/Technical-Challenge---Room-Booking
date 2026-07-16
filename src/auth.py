USERS = {
    "User1": "TechnicalChallengPromtior",
    "User2": "TechnicalChallengPromtior",
}


def authenticate(username: str, password: str) -> bool:
    return USERS.get(username) == password
