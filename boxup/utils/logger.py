"""Structured logging with colored output."""

import sys
from typing import Optional

from boxup.utils.colors import RESET, RED, GREEN, YELLOW, WHITE, BOLD

# Global verbose flag
VERBOSE = False


def set_verbose(verbose: bool) -> None:
    """Set verbose mode."""
    global VERBOSE
    VERBOSE = verbose


def _prefix(level: str, color: str) -> str:
    """Create a colored prefix."""
    return f"{color}[{level}]{RESET}"


def info(message: str) -> None:
    """General progress info."""
    print(f"{_prefix('INFO', WHITE)} {message}")
    if VERBOSE:
        sys.stdout.flush()


def success(message: str) -> None:
    """Successful installation."""
    print(f"{_prefix('OK', GREEN)} {message}")


def warn(message: str) -> None:
    """Non-critical warning."""
    print(f"{_prefix('WARN', YELLOW)} {message}")


def error(message: str) -> None:
    """Failure error."""
    print(f"{_prefix('ERR', RED)} {message}", file=sys.stderr)


def verbose(message: str) -> None:
    """Verbose debug info."""
    if VERBOSE:
        print(f"{_prefix('DBG', RESET + DIM)} {message}")