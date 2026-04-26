"""Apps module - installs Docker CE, VSCode, Opencode CLI, gentle-ai, and opencode config."""

import subprocess
import os
import shutil
from pathlib import Path

from boxup.utils.logger import info, success, warn, error, verbose
from boxup.state import mark_module_installed, is_module_installed
from boxup.system import detect_gui
from boxup.modules.brew import get_shellenv


GENTLE_AI_INSTALL_URL = "https://raw.githubusercontent.com/Gentleman-Programming/gentle-ai/main/install.sh"
OPENCODE_DOWNLOAD_URL = "https://github.com/opencode-ai/opencode/releases/download"


def install(force: bool = False) -> bool:
    """
    Install applications: Docker CE, VSCode (if GUI), Opencode CLI, gentle-ai.
    
    Also replicates user's opencode config from templates.
    """
    module_name = "apps"
    
    if is_module_installed(module_name) and not force:
        warn(f"{module_name}: already installed, skipping")
        return True
    
    info(f"Installing {module_name}...")
    
    results = []
    
    # Install Docker CE
    results.append(("docker", install_docker(force)))
    
    # Install VSCode if GUI detected
    if detect_gui():
        results.append(("vscode", install_vscode(force)))
    else:
        results.append(("vscode", {"status": "skipped", "reason": "no GUI detected"}))
    
    # Install Opencode CLI
    results.append(("opencode", install_opencode(force)))
    
    # Install gentle-ai
    results.append(("gentle-ai", install_gentle_ai(force)))
    
    # Replicate opencode config
    results.append(("opencode-config", replicate_opencode_config(force)))
    
    # Check if all succeeded
    all_success = all(r[1].get("status") == "success" for r in results)
    
    if all_success:
        mark_module_installed(
            module_name,
            vscode_installed=detect_gui(),
        )
        success(f"{module_name}: all applications installed successfully")
    else:
        failed = [r[0] for r in results if r[1].get("status") == "failed"]
        warn(f"{module_name}: some applications failed: {', '.join(failed)}")
    
    return True  # We don't fail the whole module if one sub-install fails


def install_docker(force: bool = False) -> dict:
    """Install Docker CE from official repository."""
    try:
        # Check if docker is already installed
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0 and not force:
            info(f"Docker already installed: {result.stdout.strip()}")
            return {"status": "success"}

        info("Installing Docker CE...")

        # Detect OS
        os_release = {}
        if os.path.exists("/etc/os-release"):
            with open("/etc/os-release") as f:
                for line in f:
                    if "=" in line:
                        key, val = line.strip().split("=", 1)
                        os_release[key] = val.strip('"')

        distro_id = os_release.get("ID", "")
        distro_version = os_release.get("VERSION_ID", "")
        is_debian = distro_id in ("debian", "pop", "linuxmint")
        is_ubuntu = distro_id == "ubuntu"

        # Add Docker's official GPG key
        subprocess.run(
            ["sudo", "apt", "update"],
            check=True,
            capture_output=True,
        )

        # Install prerequisites
        subprocess.run(
            ["sudo", "apt", "install", "-y", "ca-certificates", "curl", "gnupg"],
            check=True,
            capture_output=True,
        )

        # Add Docker GPG key
        subprocess.run(
            ["sudo", "install", "-m", "0755", "-d", "/etc/apt/keyrings"],
            check=True,
            capture_output=True,
        )

        # Use Ubuntu repo for both Ubuntu and Debian-based systems
        # Docker's Ubuntu repo works on Debian since they share base structure
        gpg_url = "https://download.docker.com/linux/ubuntu/gpg"
        repo_url = "https://download.docker.com/linux/ubuntu"

        subprocess.run(
            ["sudo", "curl", "-fsSL", gpg_url, "-o", "/etc/apt/keyrings/docker.asc"],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["sudo", "chmod", "a+r", "/etc/apt/keyrings/docker.asc"],
            check=True,
            capture_output=True,
        )

        # For Debian, use Debian repo if available, otherwise skip with warning
        if is_debian:
            # Use Debian's docker.io package (docker-compose-plugin is included)
            info("Debian detected, using docker.io from Debian repos...")
            subprocess.run(
                ["sudo", "apt", "install", "-y", "docker.io"],
                check=True,
                capture_output=True,
            )
        else:
            # Ubuntu path - use official Docker repo
            # Map Ubuntu codenames to stable (Docker supports these)
            distro_codename = subprocess.run(
                ["lsb_release", "-cs"],
                capture_output=True,
                text=True,
            ).stdout.strip()

            # Docker repo uses 'stable' not specific codenames for newer releases
            docker_distro = "jammy"  # Default to Ubuntu 22.04
            if distro_codename in ("focal", "jammy", "noble"):
                docker_distro = distro_codename

            with open("/etc/apt/sources.list.d/docker.list", "w") as f:
                f.write(f"deb [arch=amd64 signed-by=/etc/apt/keyrings/docker.asc] {repo_url} {docker_distro} stable\n")

            # Install Docker
            subprocess.run(
                ["sudo", "apt", "update"],
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["sudo", "apt", "install", "-y", "docker-ce", "docker-ce-cli", "containerd.io", "docker-buildx-plugin", "docker-compose-plugin"],
                check=True,
                capture_output=True,
            )

        # Add current user to docker group
        current_user = os.getenv("USER")
        subprocess.run(
            ["sudo", "usermod", "-aG", "docker", current_user],
            check=True,
            capture_output=True,
        )

        return {"status": "success"}

    except subprocess.CalledProcessError as e:
        error(f"Docker installation failed: {e}")
        return {"status": "failed", "error": str(e)}
    except Exception as e:
        error(f"Docker installation failed: {e}")
        return {"status": "failed", "error": str(e)}


def install_vscode(force: bool = False) -> dict:
    """Install VSCode from Microsoft repository."""
    try:
        info("Installing VSCode...")
        
        # Add Microsoft GPG key
        subprocess.run(
            ["sudo", "apt", "update"],
            check=True,
            capture_output=True,
        )
        
        # Install prerequisites
        subprocess.run(
            ["sudo", "apt", "install", "-y", "wget", "apt-transport-https"],
            check=True,
            capture_output=True,
        )
        
        # Add Microsoft GPG key
        subprocess.run(
            ["/bin/bash", "-c",
             "wget -qO- https://packages.microsoft.com/keys/microsoft.asc | sudo gpg --dearmor -o /usr/share/keyrings/microsoft.gpg"],
            check=True,
            capture_output=True,
        )
        
        # Add VSCode repository
        distro = subprocess.run(
            ["lsb_release", "-cs"],
            capture_output=True,
            text=True,
        ).stdout.strip()
        
        with open("/etc/apt/sources.list.d/vscode.list", "w") as f:
            f.write(f"deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft.gpg] https://packages.microsoft.com/repos/code stable main\n")
        
        # Install VSCode
        subprocess.run(
            ["sudo", "apt", "update"],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["sudo", "apt", "install", "-y", "code"],
            check=True,
            capture_output=True,
        )
        
        return {"status": "success"}
        
    except subprocess.CalledProcessError as e:
        error(f"VSCode installation failed: {e}")
        return {"status": "failed", "error": str(e)}
    except Exception as e:
        error(f"VSCode installation failed: {e}")
        return {"status": "failed", "error": str(e)}


def install_opencode(force: bool = False) -> dict:
    """Install Opencode CLI binary."""
    try:
        info("Installing Opencode CLI...")
        
        # Get latest release info
        result = subprocess.run(
            ["curl", "-s", "https://api.github.com/repos/opencode-ai/opencode/releases/latest"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        
        if result.returncode != 0:
            return {"status": "failed", "error": "Failed to fetch release info"}
        
        import json
        try:
            release_info = json.loads(result.stdout)
            version = release_info.get("tag_name", "").lstrip("v")
            assets = release_info.get("assets", [])
        except json.JSONDecodeError:
            return {"status": "failed", "error": "Failed to parse release JSON"}
        
        # Find the Linux binary
        download_url = None
        for asset in assets:
            if "linux-amd64" in asset["name"]:
                download_url = asset["browser_download_url"]
                break
        
        if not download_url:
            return {"status": "failed", "error": "Could not find Linux binary"}
        
        # Download binary
        target = Path.home() / ".local" / "bin" / "opencode"
        target.parent.mkdir(parents=True, exist_ok=True)
        
        subprocess.run(
            ["curl", "-fsSL", "-o", str(target), download_url],
            check=True,
            capture_output=True,
            timeout=120,
        )
        
        # Make executable
        os.chmod(target, 0o755)
        
        return {"status": "success", "version": version}
        
    except subprocess.CalledProcessError as e:
        error(f"Opencode installation failed: {e}")
        return {"status": "failed", "error": str(e)}
    except Exception as e:
        error(f"Opencode installation failed: {e}")
        return {"status": "failed", "error": str(e)}


def install_gentle_ai(force: bool = False) -> dict:
    """Install gentle-ai from GitHub."""
    try:
        info("Installing gentle-ai...")
        
        # Check if already installed
        gentle_ai_path = Path.home() / ".local" / "bin" / "gentle-ai"
        if gentle_ai_path.exists() and not force:
            info("gentle-ai already installed, skipping download")
            return {"status": "success", "reason": "already installed"}
        
        # Run the official installer
        result = subprocess.run(
            ["/bin/bash", "-c",
             f'curl -fsSL {GENTLE_AI_INSTALL_URL} | sh'],
            capture_output=True,
            text=True,
            timeout=180,
        )
        
        if result.returncode != 0:
            error(f"gentle-ai installation failed: {result.stderr}")
            return {"status": "failed", "error": result.stderr}
        
        # Verify installation
        if not gentle_ai_path.exists():
            return {"status": "failed", "error": "gentle-ai binary not found after install"}
        
        return {"status": "success"}
        
    except subprocess.TimeoutExpired:
        error("gentle-ai installation timed out")
        return {"status": "failed", "error": "timeout"}
    except Exception as e:
        error(f"gentle-ai installation failed: {e}")
        return {"status": "failed", "error": str(e)}


def replicate_opencode_config(force: bool = False) -> dict:
    """Replicate user's opencode/gentle-ai config to target system."""
    try:
        info("Replicating opencode config...")
        
        # Source templates are in boxup/configs/opencode/
        configs_dir = Path(__file__).parent.parent / "configs" / "opencode"
        
        # Target directory
        target_dir = Path.home() / ".config" / "opencode"
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Files to replicate
        files = ["AGENTS.md.template", "opencode.json.template"]
        
        for file in files:
            source = configs_dir / file
            if source.exists():
                # Remove .template suffix for target
                target_name = file.replace(".template", "")
                target = target_dir / target_name
                shutil.copy2(source, target)
                verbose(f"Replicated {file} -> {target}")
        
        return {"status": "success"}
        
    except Exception as e:
        error(f"opencode config replication failed: {e}")
        return {"status": "failed", "error": str(e)}