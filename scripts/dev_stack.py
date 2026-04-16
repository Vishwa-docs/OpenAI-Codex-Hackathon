from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
UV_CACHE_DIR = ROOT / ".uv-cache"
VENV_PYTHON = ROOT / ".venv" / "bin" / "python"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dev_stack",
        description="Launch the full local Cloud Migration Cockpit stack.",
    )
    parser.add_argument("--skip-infra", action="store_true", help="Do not start postgres, redis, and minio.")
    parser.add_argument("--api-port", type=int, default=8000, help="Port for the FastAPI control plane.")
    parser.add_argument("--worker-port", type=int, default=8001, help="Port for the worker service.")
    parser.add_argument("--web-port", type=int, default=3000, help="Port for the Next.js app.")
    return parser


def start_infra() -> None:
    subprocess.run(
        ["docker", "compose", "up", "-d", "postgres", "redis", "minio"],
        cwd=ROOT,
        check=True,
    )


def select_python() -> str:
    candidates = [VENV_PYTHON, Path(sys.executable)]
    for candidate in candidates:
        if not candidate.exists():
            continue
        probe = subprocess.run(
            [str(candidate), "-c", "import uvicorn"],
            cwd=ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if probe.returncode == 0:
            return str(candidate)
    return str(Path(sys.executable))


def spawn_processes(api_port: int, worker_port: int, web_port: int) -> list[tuple[str, subprocess.Popen]]:
    processes: list[tuple[str, subprocess.Popen]] = []
    UV_CACHE_DIR.mkdir(exist_ok=True)
    python_bin = select_python()

    api_env = os.environ.copy()
    api_env.setdefault("PYTHONUNBUFFERED", "1")
    api_env["UV_CACHE_DIR"] = str(UV_CACHE_DIR)
    processes.append(
        (
            "api",
            subprocess.Popen(
                [
                    python_bin,
                    "-m",
                    "uvicorn",
                    "services.api.app.main:app",
                    "--reload",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(api_port),
                ],
                cwd=ROOT,
                env=api_env,
            ),
        )
    )

    worker_env = os.environ.copy()
    worker_env.setdefault("PYTHONUNBUFFERED", "1")
    worker_env["UV_CACHE_DIR"] = str(UV_CACHE_DIR)
    processes.append(
        (
            "worker",
            subprocess.Popen(
                [
                    python_bin,
                    "-m",
                    "uvicorn",
                    "services.worker.app.main:app",
                    "--reload",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(worker_port),
                ],
                cwd=ROOT,
                env=worker_env,
            ),
        )
    )

    web_env = os.environ.copy()
    web_env["NEXT_PUBLIC_API_BASE_URL"] = f"http://127.0.0.1:{api_port}/api/v1"
    web_env["NEXT_PUBLIC_WORKER_BASE_URL"] = f"http://127.0.0.1:{worker_port}"
    web_env["PORT"] = str(web_port)
    processes.append(
        (
            "web",
            subprocess.Popen(
                ["npm", "run", "dev", "-w", "apps/web", "--", "--hostname", "127.0.0.1", "--port", str(web_port)],
                cwd=ROOT,
                env=web_env,
            ),
        )
    )

    return processes


def terminate_processes(processes: list[tuple[str, subprocess.Popen]]) -> None:
    for _, process in processes:
        if process.poll() is None:
            process.terminate()
    for _, process in processes:
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if not args.skip_infra:
        start_infra()

    processes = spawn_processes(args.api_port, args.worker_port, args.web_port)
    print(
        "\n".join(
            [
                "Cloud Migration Cockpit local stack is starting:",
                f"  marketing + cockpit UI: http://127.0.0.1:{args.web_port}",
                f"  control plane API:     http://127.0.0.1:{args.api_port}/api/v1",
                f"  worker service:        http://127.0.0.1:{args.worker_port}",
                "Press Ctrl+C to stop all local services.",
            ]
        ),
        flush=True,
    )

    def handle_signal(signum: int, _frame) -> None:
        print(f"Received signal {signum}; stopping local stack...", flush=True)
        terminate_processes(processes)
        raise SystemExit(0)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    exit_code = 0
    try:
        while True:
            for name, process in processes:
                status = process.poll()
                if status is not None:
                    print(f"{name} exited with code {status}; stopping remaining services.", flush=True)
                    exit_code = status
                    raise SystemExit(status)
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    except SystemExit as exc:
        exit_code = int(exc.code) if isinstance(exc.code, int) else 0
    finally:
        terminate_processes(processes)

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
