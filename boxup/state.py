"""State management for boxup installation."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

STATE_DIR = Path.home() / ".config" / "boxup"
STATE_FILE = STATE_DIR / "state.json"


def get_state_dir() -> Path:
    """Get the state directory path."""
    return STATE_DIR


def load_state() -> Dict[str, Any]:
    """
    Load state from state.json.
    
    Returns:
        dict with modules status and last_run timestamp
    """
    if not STATE_FILE.exists():
        return {
            "version": "1.0.0",
            "modules": {},
            "last_run": None,
        }
    
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {
            "version": "1.0.0",
            "modules": {},
            "last_run": None,
        }


def save_state(state: Dict[str, Any]) -> None:
    """Save state to state.json."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    
    state["last_run"] = datetime.now().isoformat()
    
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def is_module_installed(module_name: str) -> bool:
    """Check if a module is marked as installed."""
    state = load_state()
    return state.get("modules", {}).get(module_name, {}).get("installed", False)


def mark_module_installed(module_name: str, **kwargs) -> None:
    """Mark a module as installed with optional metadata."""
    state = load_state()
    
    if "modules" not in state:
        state["modules"] = {}
    
    state["modules"][module_name] = {
        "installed": True,
        "timestamp": datetime.now().isoformat(),
        **kwargs,
    }
    
    save_state(state)


def mark_module_failed(module_name: str, error: str) -> None:
    """Mark a module as failed."""
    state = load_state()
    
    if "modules" not in state:
        state["modules"] = {}
    
    state["modules"][module_name] = {
        "installed": False,
        "failed": True,
        "error": error,
        "timestamp": datetime.now().isoformat(),
    }
    
    save_state(state)


def reset_module(module_name: str) -> None:
    """Reset a module's state (for re-installation)."""
    state = load_state()
    
    if module_name in state.get("modules", {}):
        del state["modules"][module_name]
    
    save_state(state)


def get_module_state(module_name: str) -> Optional[Dict[str, Any]]:
    """Get the state of a specific module."""
    state = load_state()
    return state.get("modules", {}).get(module_name)