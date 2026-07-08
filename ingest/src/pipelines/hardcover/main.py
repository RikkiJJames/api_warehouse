import asyncio

from src.pipelines.hardcover.pipeline import HardcoverPipeline


async def main():
    pipeline = HardcoverPipeline()
    result = await pipeline.run()
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
