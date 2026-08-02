from user_api import UserService


def test_get_user() -> None:
    assert UserService().get_user("42") == {"id": "42"}
