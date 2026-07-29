import time
from pathlib import Path

import httpx
import jwt

from apps.backend.agents.pr_reviewer_agent.apps.code_reviewer.schema.pr_schema import (
    PullRequestFile,
)
from apps.backend.bot.application import config


class GitHubAppConfigError(RuntimeError):
    pass


class GitHubInstallationTokenService:
    def __init__(
        self,
        *,
        app_id: str | None = None,
        private_key: str | None = None,
        private_key_path: str | None = None,
    ):
        self.app_id = app_id or config.GITHUB_APP_ID
        self.private_key = config.GITHUB_PRIVATE_KEY
        self.private_key_path = private_key_path or config.GITHUB_PRIVATE_KEY_PATH

    async def create_installation_access_token(self, installation_id: int) -> str:
        app_jwt = self._create_app_jwt()
        url = (
            f"https://api.github.com/app/installations/{installation_id}/access_tokens"
        )
        headers = {
            "Authorization": f"Bearer {app_jwt}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers)
            response.raise_for_status()
            return response.json()["token"]

    def _create_app_jwt(self) -> str:
        if not self.app_id:
            raise GitHubAppConfigError("GITHUB_APP_ID is required")

        private_key = self._load_private_key()
        now = int(time.time())
        payload = {
            "iat": now - 60,
            "exp": now + (9 * 60),
            "iss": self.app_id,
        }
        return jwt.encode(payload, private_key, algorithm="RS256")

    def _load_private_key(self) -> str:
        if self.private_key:
            return self.private_key.replace("\\n", "\n")

        if self.private_key_path:
            return Path(self.private_key_path).read_text(encoding="utf-8")

        raise GitHubAppConfigError(
            "GITHUB_PRIVATE_KEY or GITHUB_PRIVATE_KEY_PATH is required"
        )


class GitHubPullRequestService:
    def __init__(
        self,
        token_service: GitHubInstallationTokenService | None = None,
    ):
        self.token_service = token_service or GitHubInstallationTokenService()

    async def get_pull_request_files(
        self,
        owner: str,
        repo: str,
        pull_number: int,
        installation_id: int,
    ) -> list[PullRequestFile]:
        token = await self.token_service.create_installation_access_token(
            installation_id
        )
        url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}/files"
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        files: list[PullRequestFile] = []
        page = 1

        async with httpx.AsyncClient(timeout=30.0) as client:
            while True:
                response = await client.get(
                    url, headers=headers, params={"per_page": 100, "page": page}
                )
                response.raise_for_status()
                page_files = response.json()
                files.extend(
                    PullRequestFile.model_validate(file_data)
                    for file_data in page_files
                )

                if len(page_files) < 100:
                    break

                page += 1

        return files
