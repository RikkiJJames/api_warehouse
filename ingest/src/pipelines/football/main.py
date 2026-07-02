import asyncio

from src.pipelines.football.pipeline import FootballPipeline


async def main():
    pipeline = FootballPipeline()
    result = await pipeline.run()
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
