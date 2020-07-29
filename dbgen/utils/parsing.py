from typing import Optional, Tuple
from re import finditer, MULTILINE, search, DOTALL
from distutils.util import strtobool
from argparse import ArgumentParser
import logging

################################################################################
def parse_line(string: str, substr: str, index: int = 0) -> Optional[str]:
    """
    Returns the n'th line containing substring
    Any negative index will return last one.
    """
    iter = finditer(substr + ".*$", string, MULTILINE)
    found = False

    for match in iter:
        if index == 0:
            return match[0]
        else:
            index -= 1
            found = True
    if found:
        return match[0]  # negative input for index
    else:
        return None


def btw(s: str, begin: str, end: str, off: int = 0) -> Tuple[str, int]:
    result = search("%s(.*?)%s" % (begin, end), s[off:], DOTALL)
    if result:
        if result.group(1) is None:
            import pdb

            pdb.set_trace()
        return result.group(1), result.end() + off
    else:
        return "", 0


def input_to_level(logging_level: str) -> int:
    log_map = {
        "INFO": logging.INFO,
        "DEBUG": logging.DEBUG,
        "WARNING": logging.WARNING,
        "CRITICAL": logging.CRITICAL,
    }
    if logging_level in log_map:
        return log_map[logging_level]
    raise ValueError("Please provide a valid logging level")


########
# Command line parsing
parser = ArgumentParser(description="Run a DBG update", allow_abbrev=True)

parser.add_argument(
    "--nuke",
    default="",
    type=str,
    help="Reset the DB - needed if you make schema changes",
)

parser.add_argument(
    "--add",
    action="store_true",
    help="Try to add columns (if you make benign schema additions)",
)

parser.add_argument(
    "--only", default="", help="Run only the (space separated) actions/tags"
)

parser.add_argument(
    "--xclude", type=str, default="", help="Run only the (space separated) actions/tags"
)

parser.add_argument("--start", default="", help="Start at the designed Generator")

parser.add_argument("--until", default="", help="Stop at the designed Generator")

parser.add_argument(
    "--retry", action="store_true", help="Ignore repeat checking",
)

parser.add_argument(
    "--serial",
    default=False,
    type=lambda x: bool(strtobool(x)),
    help='Ignore any "parallel" flags',
)

parser.add_argument(
    "--clean",
    default=False,
    help="Clean the database of the deleted column!DOESN't DELETE DELETED ROWS YET!",
)

parser.add_argument(
    "--skip-row-count", action="store_true", help="Skip Row count for large queries",
)

parser.add_argument(
    "--batch", default=None, type=lambda x: int(float(x)), help="Set default batch_size"
)

parser.add_argument(
    "--write-logs", action="store_true", help="write logs to local file",
)

parser.add_argument(
    "--log-level",
    default=logging.DEBUG,
    type=input_to_level,
    help="Set default batch_size",
)

parser.add_argument(
    "--log-path", default=None, help="Set path of output log file",
)
