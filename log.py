from enum import IntEnum
from inspect import getframeinfo, stack
from colorama import Fore, Back, Style, init
from typing import IO
from datetime import datetime

LOGGER_FILE_NAME = "recent.log"

class level(IntEnum):
    # storted by importance, increasing
    DEBUG = 0
    TRACE = 1
    CRITICAL = 2
    FATAL = 3
    INFO = 4
    NONE = 5

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
    caller_det_console: str = "{}:{}".format(caller.filename, caller.lineno)

    format: str = "{} {}: {!s}".format(
        datetime.now(),
        caller_det,
        msg
    )

    format_console: str = "{} {}: {!s}".format(
        datetime.now(),
        caller_det_console,
        msg
    )
    
    
    print(format)
    current_file_buffer.write(format_console)
    current_file_buffer.flush()