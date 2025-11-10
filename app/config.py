import os
from functools import lru_cache
from typing import Optional

class Settings:
    app_name: str = "LLM Analysis Quiz Server"
    secret: str
    email: str
    github_repo_url: Optional[str]
    deployment_url: Optional[str]
    headless: bool = True
    user_agent: str = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )
    request_timeout: float = 45.0
    disable_solver: bool = False

    def __init__(self) -> None:
        self.secret = os.getenv("QUIZ_SECRET", "")
        self.email = os.getenv("QUIZ_EMAIL", "")
        self.github_repo_url = os.getenv("GITHUB_REPO_URL")
        self.deployment_url = os.getenv("DEPLOYMENT_URL")
        self.headless = os.getenv("HEADLESS", "true").lower() != "false"
        self.request_timeout = float(os.getenv("REQUEST_TIMEOUT", "45"))
        self.disable_solver = os.getenv("DISABLE_SOLVER", "false").lower() == "true"

    def validate(self) -> None:
        missing = []
        if not self.secret:
            missing.append("QUIZ_SECRET")
        if not self.email:
            missing.append("QUIZ_EMAIL")
        if missing:
            raise RuntimeError(
                "Missing required environment variables: " + ", ".join(missing)
            )

@lru_cache
def get_settings() -> Settings:
    s = Settings()
    return s
