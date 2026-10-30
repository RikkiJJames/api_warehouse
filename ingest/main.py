import asyncio
import logging
import sys

from src.config.logs import logging_config
from src.pipelines.spotify.pipeline import SpotifyPipeline
from src.pipelines.hardcover.pipeline import HardcoverPipeline
from src.pipelines.football.pipeline import FootballPipeline
from src.pipelines.mma.pipeline import MmaPipeline
from src.pipelines.trakt.pipeline import TraktPipeline
from src.pipelines.google_health.pipeline import GoogleHealthPipeline


logger = logging.getLogger(__name__)


async def main() -> tuple[dict[str, object], list[str]]:
    logger.info("Starting ingest job")
    results: dict[str, object] = {}
    failed: list[str] = []

    for Pipeline in [SpotifyPipeline, HardcoverPipeline, GoogleHealthPipeline, TraktPipeline]:
    # for Pipeline in [TraktPipeline]:
        pipeline_name = Pipeline.__name__
        logger.info("Running pipeline: %s", pipeline_name)
        # One API's failure (expired token, outage, bad response) shouldn't
        # stop the others from ingesting — log it and move on.
        try:
            result = await Pipeline().run()
        except Exception:
            logger.exception("Pipeline failed: %s", pipeline_name)
            failed.append(pipeline_name)
            continue
        results[pipeline_name] = result
        logger.info("Pipeline finished: %s", pipeline_name)

    return results, failed


def run() -> int:
    try:
        results, failed = asyncio.run(main())
    except Exception:
        logger.exception("Ingest job failed")
        return 1

    logger.info("Results: %s", results)
    # Only fail the job when nothing succeeded — a non-zero exit stops the
    # ingest-then-dbt Workflow before dbt, and partial fresh data is still
    # worth transforming.
    if failed and not results:
        logger.error("Ingest job failed: every pipeline failed (%s)", ", ".join(failed))
        return 1
    if failed:
        logger.error("Ingest job completed with failed pipelines: %s", ", ".join(failed))
    else:
        logger.info("Ingest job completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(run())
