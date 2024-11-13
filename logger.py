import logging


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        handlers=[
            logging.FileHandler("app_errors.log")
        ],
        format="%(asctime)s - %(name)s, - %(levelname)s - %(message)s"
    )
