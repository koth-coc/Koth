import coc


class CocClient:
    """Thin wrapper around coc.py.

    coc.py's email/password login automatically creates (and reuses/rotates)
    an API key scoped to whatever IP the process is currently running on.
    That's what makes this work on Railway despite the box not having a
    fixed IP - there's no API token to hardcode or whitelist manually.
    """

    def __init__(self):
        self.client: coc.Client | None = None

    async def login(self, email: str, password: str):
        self.client = coc.Client()
        await self.client.login(email, password)

    async def get_player(self, tag: str):
        """Returns a coc.Player, or None if the tag doesn't exist."""
        try:
            return await self.client.get_player(tag)
        except coc.NotFound:
            return None
        except coc.PrivateWarLog:
            return None

    async def close(self):
        if self.client:
            await self.client.close()


def normalize_tag(tag: str) -> str:
    tag = tag.strip().upper().replace("O", "0")
    if not tag.startswith("#"):
        tag = "#" + tag
    return tag
