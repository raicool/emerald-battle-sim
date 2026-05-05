from enum import IntEnum
from inspect import getframeinfo, stack
from colorama import Fore, Back, init
from typing import IO
from datetime import datetime

LOGGER_FILE_NAME = "recent.log"

class level(IntEnum):
    # storted by importance, increasing
    DEBUG = 0
    TRACE = 1
    WARNING = 2
    CRITICAL = 3
    FATAL = 4
    INFO = 5
    NONE = 6

current_file_buffer: IO[str] = IO()
log_level: int = level.TRACE

def __initLoggerFile():
    init()
    global current_file_buffer
    current_file_buffer = open(f"{LOGGER_FILE_NAME}", "w+")

def debug(msg: str):
    global log_level
    if (log_level <= level.DEBUG):
        __printlog(msg, Fore.MAGENTA)

def trace(msg: str):
    global log_level
    if (log_level <= level.TRACE):
        __printlog(msg, Fore.CYAN)

def warning(msg: str):
    global log_level
    if (log_level <= level.WARNING):
        __printlog(msg, Fore.YELLOW)

def critical(msg: str):
    global log_level
    if (log_level <= level.CRITICAL):
        __printlog(msg, Fore.RED)

def fatal(msg: str):
    global log_level
    if (log_level <= level.FATAL):
        __printlog(msg, Fore.WHITE, Back.RED)

def info(msg: str):
    global log_level
    if (log_level <= level.TRACE):
        __printlog(msg, Fore.GREEN)

def __printlog(msg: str, foreground_col: str, background_col: str = ""):
    global current_file_buffer
    caller = getframeinfo(stack()[2][0])

    color = foreground_col + background_col
    caller_det: str = color + "{}:{}".format(caller.filename, caller.lineno) + Fore.RESET
    caller_det_file: str = "{}:{}".format(caller.filename, caller.lineno)

    format: str = "{} {}: {!s}".format(
        datetime.now(),
        caller_det,
        msg
    )

    format_file_sink: str = "{} {}: {!s}\n".format(
        datetime.now(),
        caller_det_file,
        msg
    )
    
    print(format)
    current_file_buffer.write(format_file_sink)
    current_file_buffer.flush()