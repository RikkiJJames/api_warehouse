import asyncio

from src.pipelines.spotify.pipeline import SpotifyPipeline
from src.pipelines.football.pipeline import FootballPipeline
from src.pipelines.mma.pipeline import MmaPipeline
from src.pipelines.trakt.pipeline import TraktPipeline


async def main():
    # for Pipeline in [SpotifyPipeline, FootballPipeline, MmaPipeline]:
    for Pipeline in [SpotifyPipeline, TraktPipeline]:
        result = await Pipeline().run()
        print(result)


if __name__ == "__main__":
    asyncio.run(main())
