from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ..domain.models import PreviewDeploymentStatus


ROOT = Path(__file__).resolve().parents[4]


@dataclass
class PreviewRuntime:
    process: subprocess.Popen[bytes]
    workspace_path: Path
    log_path: Path
    url: str


class LocalPreviewManager:
    def __init__(self) -> None:
        self._previews: dict[str, PreviewRuntime] = {}
        self._artifacts_root = ROOT / "artifacts" / "previews"

    def launch(self, project_id: str, source_root: str) -> PreviewDeploymentStatus:
        source = Path(source_root).expanduser().resolve()
        if not source.exists():
            raise FileNotFoundError(f"Preview source path does not exist: {source}")

        existing = self._previews.get(project_id)
        if existing is not None and existing.process.poll() is None:
            self._terminate(project_id)

        workspace = self._prepare_workspace(project_id, source)
        log_path = workspace.parent / "preview.log"
        port = self._find_open_port()
        command = self._resolve_preview_command(workspace, port)

        with log_path.open("w", encoding="utf-8") as log_file:
            log_file.write(f"$ {' '.join(command)}\n")
            log_file.write(f"workspace={workspace}\n")

        environment = os.environ.copy()
        environment.setdefault("HOST", "127.0.0.1")
        environment["PORT"] = str(port)
        environment.setdefault("BROWSER", "none")
        environment.setdefault("CI", "1")

        with log_path.open("a", encoding="utf-8") as log_file:
            if not (workspace / "node_modules").exists():
                self._install_dependencies(workspace, log_file, environment)

            process = subprocess.Popen(
                command,
                cwd=workspace,
                env=environment,
                stdout=log_file,
                stderr=subprocess.STDOUT,
            )

        runtime = PreviewRuntime(
            process=process,
            workspace_path=workspace,
            log_path=log_path,
            url=f"http://127.0.0.1:{port}",
        )
        self._previews[project_id] = runtime
        return self._wait_until_ready(project_id)

    def get_status(
        self,
        project_id: str,
        current: PreviewDeploymentStatus | None,
    ) -> PreviewDeploymentStatus | None:
        runtime = self._previews.get(project_id)
        if runtime is None:
            return current

        now = datetime.now(tz=UTC)
        if runtime.process.poll() is None:
            if self._check_http(runtime.url):
                return PreviewDeploymentStatus(
                    status="running",
                    supported=True,
                    summary="The local preview is live from the working copy and ready to review in the cockpit.",
                    url=runtime.url,
                    health_summary="Healthy HTTP response from the preview server.",
                    workspace_path=str(runtime.workspace_path),
                    log_tail=self._tail(runtime.log_path),
                    updated_at=now,
                )
            return PreviewDeploymentStatus(
                status="running",
                supported=True,
                summary="The preview process is still starting. Logs are streaming from the working copy.",
                url=runtime.url,
                health_summary="Waiting for the preview HTTP endpoint to become healthy.",
                workspace_path=str(runtime.workspace_path),
                log_tail=self._tail(runtime.log_path),
                updated_at=now,
            )

        return PreviewDeploymentStatus(
            status="failed",
            supported=True,
            summary="The local preview process exited before staying healthy.",
            url=runtime.url,
            health_summary=f"Process exited with code {runtime.process.returncode}.",
            workspace_path=str(runtime.workspace_path),
            log_tail=self._tail(runtime.log_path),
            updated_at=now,
        )

    def _wait_until_ready(self, project_id: str, timeout_seconds: int = 45) -> PreviewDeploymentStatus:
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            status = self.get_status(project_id, None)
            if status is None:
                break
            if status.status == "running" and status.health_summary == "Healthy HTTP response from the preview server.":
                return status
            if status.status == "failed":
                return status
            time.sleep(1)

        status = self.get_status(project_id, None)
        if status is not None:
            return status

        raise RuntimeError("Preview process did not publish status.")

    def _prepare_workspace(self, project_id: str, source: Path) -> Path:
        preview_root = self._artifacts_root / project_id
        workspace = preview_root / "workspace"
        if workspace.exists():
            shutil.rmtree(workspace)
        preview_root.mkdir(parents=True, exist_ok=True)
        shutil.copytree(
            source,
            workspace,
            ignore=shutil.ignore_patterns(
                ".git",
                ".next",
                "dist",
                "build",
                "coverage",
                "artifacts",
                "__pycache__",
                ".pytest_cache",
            ),
            dirs_exist_ok=True,
        )

        source_node_modules = source / "node_modules"
        workspace_node_modules = workspace / "node_modules"
        if source_node_modules.exists() and not workspace_node_modules.exists():
            workspace_node_modules.symlink_to(source_node_modules)

        return workspace

    def _resolve_preview_command(self, workspace: Path, port: int) -> list[str]:
        package_manager = self._detect_package_manager(workspace)
        root_package = self._read_package_json(workspace / "package.json")
        apps_web = workspace / "apps" / "web" / "package.json"
        if apps_web.exists():
            if package_manager == "npm":
                return ["npm", "run", "dev", "-w", "apps/web", "--", "--hostname", "127.0.0.1", "--port", str(port)]
            if package_manager == "pnpm":
                return ["pnpm", "--dir", "apps/web", "dev", "--", "--host", "127.0.0.1", "--port", str(port)]
            return ["yarn", "--cwd", "apps/web", "dev", "--host", "127.0.0.1", "--port", str(port)]

        scripts = root_package.get("scripts", {})
        for script_name in ("preview", "dev", "start"):
            if script_name in scripts:
                if package_manager == "npm":
                    return ["npm", "run", script_name]
                if package_manager == "pnpm":
                    return ["pnpm", script_name]
                return ["yarn", script_name]

        raise RuntimeError("No supported preview command was found. Expected a Node web app or monorepo.")

    def _install_dependencies(self, workspace: Path, log_file, environment: dict[str, str]) -> None:
        package_manager = self._detect_package_manager(workspace)
        if package_manager == "pnpm":
            command = ["pnpm", "install", "--frozen-lockfile"]
        elif package_manager == "yarn":
            command = ["yarn", "install", "--immutable"]
        elif (workspace / "package-lock.json").exists():
            command = ["npm", "ci"]
        else:
            command = ["npm", "install"]

        log_file.write(f"$ {' '.join(command)}\n")
        log_file.flush()
        subprocess.run(
            command,
            cwd=workspace,
            env=environment,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            check=True,
            timeout=900,
        )

    @staticmethod
    def _read_package_json(path: Path) -> dict[str, object]:
        if not path.exists():
            raise RuntimeError(f"Expected package.json at {path}")
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def _detect_package_manager(workspace: Path) -> str:
        if (workspace / "pnpm-lock.yaml").exists():
            return "pnpm"
        if (workspace / "yarn.lock").exists():
            return "yarn"
        return "npm"

    @staticmethod
    def _find_open_port() -> int:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 0))
            return int(sock.getsockname()[1])

    @staticmethod
    def _check_http(url: str) -> bool:
        request = Request(url, method="GET")
        try:
            with urlopen(request, timeout=2) as response:
                return response.status < 500
        except (HTTPError, URLError, TimeoutError):
            return False

    @staticmethod
    def _tail(path: Path, line_count: int = 12) -> list[str]:
        if not path.exists():
            return []
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        return lines[-line_count:]

    def _terminate(self, project_id: str) -> None:
        runtime = self._previews.get(project_id)
        if runtime is None:
            return
        if runtime.process.poll() is None:
            runtime.process.terminate()
            try:
                runtime.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                runtime.process.kill()

