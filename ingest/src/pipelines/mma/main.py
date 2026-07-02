import asyncio

from src.pipelines.mma.pipeline import MmaPipeline


async def main():
    pipeline = MmaPipeline()
    result = await pipeline.run()
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
