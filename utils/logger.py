import logging

def setup_logger(name: str = __name__) -> logging.Logger:
    """Setup and return a configured logger"""
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    return logging.getLogger(name)


