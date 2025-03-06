# -*- coding: UTF-8 -*-
"""Import modules"""
import logging
import sys

# Configure logging with more robust settings
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Get logger instance
logger = logging.getLogger("mail-worker")

# Disable pika library logs to reduce noise
logging.getLogger("pika").setLevel(logging.WARNING)
