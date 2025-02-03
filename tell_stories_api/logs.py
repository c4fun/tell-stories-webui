#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
from datetime import datetime
from functools import partial
from pathlib import Path

from loguru import logger as _logger

from tell_stories_api.const import TELL_STORIES_API_ROOT


def define_log_level(print_level="INFO", logfile_level="DEBUG"):
    """Adjust the log level to above level"""
    current_date = datetime.now()
    formatted_date = current_date.strftime("%Y%m%d")

    _logger.remove()
    _logger.add(sys.stderr, level=print_level)
    logs_dir = Path(TELL_STORIES_API_ROOT, "logs")
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_file_path = logs_dir / f"{formatted_date}.log"
    # Use rotation to create a new log file each day
    _logger.add(log_file_path, level=logfile_level, rotation="00:00", retention="30 days")
    return _logger


logger = define_log_level()


def log_llm_stream(msg):
    _llm_stream_log(msg)


def set_llm_stream_logfunc(func):
    global _llm_stream_log
    _llm_stream_log = func


_llm_stream_log = partial(print, end="")
