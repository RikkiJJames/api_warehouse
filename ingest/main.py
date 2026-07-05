import asyncio
import logging
import sys

from src.config.logs import logging_config
from src.pipelines.spotify.pipeline import SpotifyPipeline
from src.pipelines.football.pipeline import FootballPipeline
from src.pipelines.mma.pipeline import MmaPipeline
from src.pipelines.trakt.pipeline import TraktPipeline


logger = logging.getLogger(__name__)


async def main() -> dict[str, object]:
    logger.info("Starting ingest job")
    results: dict[str, object] = {}

    for Pipeline in [SpotifyPipeline, TraktPipeline]:
        pipeline_name = Pipeline.__name__
        logger.info("Running pipeline: %s", pipeline_name)
        result = await Pipeline().run()
        results[pipeline_name] = result
        logger.info("Pipeline finished: %s", pipeline_name)

    return results


def run() -> int:
    try:
        results = asyncio.run(main())
        logger.info("Ingest job completed successfully")
        logger.info("Results: %s", results)
        return 0
    except Exception:
        logger.exception("Ingest job failed")
        return 1


if __name__ == "__main__":
    sys.exit(run())
