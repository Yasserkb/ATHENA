from fastapi import FastAPI

app = FastAPI()


class UserService:
    def get_user(self, user_id: str) -> dict[str, str]:
        return {"id": user_id}


@app.get("/users/{user_id}")
def get_user(user_id: str) -> dict[str, str]:
    return UserService().get_user(user_id)
