import argparse
import logging
from pathlib import Path

from eval.config import load_eval_config
from eval.runner import run

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")


def main():
    parser = argparse.ArgumentParser(
        description="Run evaluation scenarios against the AI Contact Centre",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--config",
        "-c",
        type=Path,
        default=Path("config.yaml"),
        help="Path to eval config YAML file",
    )
    parser.add_argument(
        "--concurrency",
        "-n",
        type=int,
        default=None,
        help="Override concurrency level from config",
    )

    args = parser.parse_args()
    config = load_eval_config(args.config)

    if args.concurrency is not None:
        config.execution.concurrency = args.concurrency

    run(config)


if __name__ == "__main__":
    main()
