class SpotifyPaginator:
    def __init__(self, client, max_pages=10):
        self.client = client
        self.max_pages = max_pages

    async def fetch_all(self, url: str):
        results = []
        page = 0


        while url and page < self.max_pages:
            response = await self.client.get(url)
            body = response.json()
            if not body.get("items") and not body.get("next"):
                break
            results.extend(body.get("items", []))

            url = body.get("next")
            page += 1

        return results