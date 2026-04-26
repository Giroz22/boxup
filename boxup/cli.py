"""CLI module - handles module execution."""

import importlib
from typing import List, Dict, Any, Optional

import typer

from boxup.utils.logger import info, success, warn, error
from boxup.state import is_module_installed, mark_module_failed

app = typer.Typer(help="Boxup - Terminal Development Environment Bootstrap")


# Module execution order
MODULE_ORDER = [
    "base",
    "brew",
    "zsh",
    "tmux",
    "fastfetch",
    "nvm",
    "apps",
]


def run_modules(modules: Optional[List[str]] = None, force: bool = False) -> Dict[str, Dict[str, Any]]:
    """
    Run specified modules or all modules in dependency order.
    
    Args:
        modules: List of module names to run, or None for all
        force: Force re-installation even if already installed
    
    Returns:
        Dict mapping module names to results
    """
    results = {}
    
    # Determine which modules to run
    if modules:
        # Validate module names
        valid_modules = set(MODULE_ORDER)
        requested = set(modules)
        invalid = requested - valid_modules
        
        if invalid:
            error(f"Unknown modules: {', '.join(invalid)}")
            error(f"Valid modules: {', '.join(valid_modules)}")
            return results
        
        to_run = [m for m in MODULE_ORDER if m in requested]
    else:
        to_run = MODULE_ORDER
    
    info(f"Running modules: {' -> '.join(to_run)}")
    
    for module_name in to_run:
        result = run_single_module(module_name, force=force)
        results[module_name] = result
        
        if result.get("status") == "failed":
            warn(f"Module {module_name} failed, continuing with next...")
    
    return results


def run_single_module(module_name: str, force: bool = False) -> Dict[str, Any]:
    """
    Run a single module by name.
    
    Args:
        module_name: Name of the module to run
        force: Force re-installation even if already installed
    
    Returns:
        Dict with status and optional details
    """
    try:
        # Import the module
        module = importlib.import_module(f"boxup.modules.{module_name}")
        
        # Check if install function exists
        if not hasattr(module, "install"):
            return {
                "status": "failed",
                "error": f"Module {module_name} has no install() function",
            }
        
        # Run the install function
        success_result = module.install(force=force)
        
        if success_result:
            return {"status": "success"}
        else:
            return {"status": "failed", "error": "install() returned False"}
            
    except ImportError as e:
        error(f"Failed to import module {module_name}: {e}")
        return {"status": "failed", "error": str(e)}
    except Exception as e:
        error(f"Module {module_name} raised exception: {e}")
        return {"status": "failed", "error": str(e)}


def uninstall_boxup(restore: bool = False, force: bool = False) -> None:
    """Uninstall all boxup components."""
    from boxup.modules.uninstall import uninstall_boxup as do_uninstall
    do_uninstall(restore=restore, force=force)


@app.command()
def main(
    modules: List[str] = typer.Argument(None, help="Modules to run (default: all)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without applying"),
    force: bool = typer.Option(False, "--force", help="Force re-installation"),
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Verbose output"),
    uninstall: bool = typer.Option(False, "--uninstall", help="Uninstall boxup"),
    restore: bool = typer.Option(False, "--restore", help="Restore backups during uninstall"),
) -> None:
    """Boxup - Terminal Development Environment Bootstrap"""
    if uninstall:
        uninstall_boxup(restore=restore, force=force)
        return
    
    if dry_run:
        info("Dry run mode - no changes will be made")
    
    results = run_modules(modules=modules if modules else None, force=force)
    
    # Print summary
    success_count = sum(1 for r in results.values() if r.get("status") == "success")
    failed_count = sum(1 for r in results.values() if r.get("status") == "failed")
    
    info(f"\nSummary: {success_count} succeeded, {failed_count} failed")


if __name__ == "__main__":
    app()