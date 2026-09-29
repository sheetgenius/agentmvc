#!/usr/bin/env python3
"""Prove Python framework plumbing with a disposable, non-product probe app."""

import argparse
import hashlib
import json
import shutil
import subprocess
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STACK = ROOT / "stacks/python"
IMAGE = "agentmvc-python-toolchain:preflight"
PORT = 4111


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-build", action="store_true")
    args = parser.parse_args()
    stamp = str(int(time.time()))
    work = ROOT / ".work" / ("python-preflight-" + stamp)
    app = work / "app"
    work.mkdir(parents=True)
    log = (work / "commands.log").open("w")
    prefix = "agentmvc-python-preflight-" + stamp
    network, database, development, production = (
        prefix + suffix for suffix in ("-net", "-db", "-dev", "-prod")
    )
    prod_image = prefix + ":production"
    report = {
        "status": "running",
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "checks": {},
        "toolchain": IMAGE,
        "application_limits": {"cpus": 2, "memory": "1g"},
    }
    results = ROOT / "results/lanes/python/preflight.json"
    results.parent.mkdir(parents=True, exist_ok=True)
    launched = []

    def run(argv, *, check=True, timeout=600):
        log.write("$ " + " ".join(argv) + "\n")
        log.flush()
        proc = subprocess.run(
            argv,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
            check=False,
        )
        log.write(proc.stdout + "\n")
        log.flush()
        if check and proc.returncode:
            raise RuntimeError(
                f"command failed ({proc.returncode}): {argv[:4]}\n{proc.stdout[-4000:]}"
            )
        return proc.stdout.strip()

    def tool(*argv):
        return run(
            [
                "docker",
                "run",
                "--rm",
                "--network",
                network,
                "-v",
                f"{app}:/work/app",
                "-w",
                "/work/app",
                "-e",
                f"DATABASE_URL=postgres://agentmvc:agentmvc@{database}:5432/preflight",
                "-e",
                "SECRET_KEY_BASE=preflight-disposable-secret",
                IMAGE,
                *argv,
            ]
        )

    def shell(code):
        return tool("python", "manage.py", "shell", "-c", code)

    def ready(expected="ok", timeout=60):
        started = time.monotonic()
        last_error = None
        while time.monotonic() - started < timeout:
            try:
                with urllib.request.urlopen(
                    f"http://127.0.0.1:{PORT}/health", timeout=2
                ) as response:
                    if json.load(response)["status"] == expected:
                        return round(time.monotonic() - started, 3)
            except (OSError, ValueError, KeyError) as error:
                last_error = str(error)
            time.sleep(0.15)
        raise RuntimeError(f"health timed out: {expected}; {last_error}")

    def start_dev():
        run(
            [
                "docker",
                "run",
                "-d",
                "--name",
                development,
                "--cpus",
                "2",
                "--memory",
                "1g",
                "--network",
                network,
                "-p",
                f"127.0.0.1:{PORT}:{PORT}",
                "-v",
                f"{app}:/work/app",
                "-e",
                f"DATABASE_URL=postgres://agentmvc:agentmvc@{database}:5432/preflight",
                "-e",
                "SECRET_KEY_BASE=preflight-disposable-secret",
                "-e",
                f"PORT={PORT}",
                IMAGE,
                "bash",
                "bin/dev",
            ]
        )
        launched.append(development)
        ready()

    def socket(container):
        code = (
            "from websockets.sync.client import connect; import json; "
            f"s=connect('ws://127.0.0.1:{PORT}/_preflight/echo'); "
            "s.send(json.dumps({'text':'東京 café'})); "
            "assert json.loads(s.recv()) == {'text':'東京 café'}; s.close()"
        )
        run(["docker", "exec", container, "python", "-c", code])

    def queue(container):
        code = (
            "from django.db import transaction; from probe.models import Probe; "
            "from probe.tasks import mark; "
            "exec('with transaction.atomic():\\n p=Probe.objects.create()\\n mark.defer(pk=p.pk)'); "
            "print('PROBE_ID='+str(p.pk))"
        )
        output = run(
            ["docker", "exec", container, "python", "manage.py", "shell", "-c", code]
        )
        pk = int(output.split("PROBE_ID=")[-1].splitlines()[0])
        started = time.monotonic()
        while time.monotonic() - started < 20:
            output = run(
                [
                    "docker",
                    "exec",
                    container,
                    "python",
                    "manage.py",
                    "shell",
                    "-c",
                    f"from probe.models import Probe; print('DONE='+str(Probe.objects.get(pk={pk}).done))",
                ]
            )
            if "DONE=True" in output:
                return
            time.sleep(0.2)
        raise RuntimeError("job did not complete")

    try:
        shutil.copytree(
            STACK / "scaffold",
            app,
            ignore=shutil.ignore_patterns(
                ".venv", "__pycache__", ".ruff_cache", ".pytest_cache"
            ),
        )
        if not args.skip_build:
            print("Building Python toolchain", flush=True)
            run(
                [
                    "docker",
                    "build",
                    "-f",
                    str(STACK / "Dockerfile.toolchain"),
                    "-t",
                    IMAGE,
                    str(STACK),
                ]
            )
        report["toolchain_image_id"] = run(
            ["docker", "image", "inspect", IMAGE, "--format", "{{.Id}}"]
        )
        run(["docker", "network", "create", network])
        run(
            [
                "docker",
                "run",
                "-d",
                "--name",
                database,
                "--network",
                network,
                "-e",
                "POSTGRES_USER=agentmvc",
                "-e",
                "POSTGRES_PASSWORD=agentmvc",
                "-e",
                "POSTGRES_DB=preflight",
                "postgres:17",
            ]
        )
        launched.append(database)
        for _ in range(60):
            if "accepting connections" in run(
                ["docker", "exec", database, "pg_isready", "-U", "agentmvc"],
                check=False,
            ):
                break
            time.sleep(0.2)
        else:
            raise RuntimeError("PostgreSQL did not become ready")
        report["versions"] = json.loads(
            tool(
                "python",
                "-c",
                "import json,sys,importlib.metadata as m; print(json.dumps({'python':sys.version.split()[0], **{n:m.version(n) for n in ['Django','django-ninja','channels','procrastinate','psycopg','uvicorn','PyJWT']}}))",
            )
        )
        report["versions"]["uv"] = tool("uv", "--version")
        report["postgres_image_id"] = run(
            ["docker", "inspect", database, "--format", "{{.Image}}"]
        )
        tool("python", "manage.py", "check")
        tool("ruff", "check", ".")
        tool("ruff", "format", "--check", ".")
        report["checks"]["clean_scaffold"] = True
        probe = app / "probe"
        (probe / "migrations").mkdir(parents=True)
        (probe / "__init__.py").write_text("")
        (probe / "migrations/__init__.py").write_text("")
        (probe / "models.py").write_text(
            "from django.db import models\nclass Probe(models.Model):\n    done = models.BooleanField(default=False)\n"
        )
        (probe / "tasks.py").write_text(
            "from procrastinate.contrib.django import app\nfrom .models import Probe\n"
            "@app.task\ndef mark(pk):\n    Probe.objects.filter(pk=pk).update(done=True)\n"
        )
        (probe / "sockets.py").write_text(
            "from channels.generic.websocket import AsyncJsonWebsocketConsumer\n"
            "class Echo(AsyncJsonWebsocketConsumer):\n"
            "    async def connect(self):\n        await self.accept()\n"
            "    async def receive_json(self, content):\n        await self.send_json(content)\n"
        )
        with (app / "config/settings.py").open("a") as f:
            f.write('\nINSTALLED_APPS += ["probe"]\n')
        (app / "config/asgi.py").write_text(
            'import os\nos.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")\n'
            "from django.core.asgi import get_asgi_application\ndjango_application=get_asgi_application()\n"
            "from channels.routing import ProtocolTypeRouter, URLRouter\nfrom django.urls import path\n"
            'from probe.sockets import Echo\napplication=ProtocolTypeRouter({"http":django_application,'
            '"websocket":URLRouter([path("_preflight/echo", Echo.as_asgi())])})\n'
        )
        tool("python", "manage.py", "makemigrations", "probe")
        tool("python", "manage.py", "migrate", "--noinput")
        shell(
            "from django.db import transaction; from probe.models import Probe; from probe.tasks import mark; "
            "from procrastinate.contrib.django.models import ProcrastinateJob; "
            "before=ProcrastinateJob.objects.count(); "
            "exec('try:\\n with transaction.atomic():\\n  p=Probe.objects.create()\\n  mark.defer(pk=p.pk)\\n  raise ValueError()\\nexcept ValueError: pass'); "
            "assert Probe.objects.count()==0; assert ProcrastinateJob.objects.count()==before"
        )
        report["checks"]["migration_and_atomic_queue_rollback"] = True
        print("Verifying development, jobs, WebSocket and reload", flush=True)
        start_dev()
        socket(development)
        queue(development)
        report["checks"]["development_health_queue_socket"] = True
        urls = app / "config/urls.py"
        original = urls.read_text()
        urls.write_text(original.replace('"ok"', '"reloaded"'))
        report["reload_seconds"] = ready("reloaded")
        urls.write_text(original)
        ready()
        report["checks"]["hot_reload"] = True
        run(["docker", "rm", "-f", development])
        launched.remove(development)
        shell(
            "from probe.models import Probe; from probe.tasks import mark; "
            "p=Probe.objects.create(); mark.defer(pk=p.pk); print(p.pk)"
        )
        start_dev()
        shell(
            "import time; from probe.models import Probe; "
            "exec('for _ in range(50):\\n if not Probe.objects.filter(done=False).exists(): break\\n time.sleep(.1)'); "
            "assert not Probe.objects.filter(done=False).exists()"
        )
        report["checks"]["job_survives_worker_absence"] = True
        run(["docker", "rm", "-f", development])
        launched.remove(development)
        print("Building and checking fresh production image", flush=True)
        run(["docker", "build", "-t", prod_image, str(app)])
        run(["docker", "exec", database, "createdb", "-U", "agentmvc", "production"])
        run(
            [
                "docker",
                "run",
                "-d",
                "--name",
                production,
                "--cpus",
                "2",
                "--memory",
                "1g",
                "--network",
                network,
                "-p",
                f"127.0.0.1:{PORT}:{PORT}",
                "-e",
                f"DATABASE_URL=postgres://agentmvc:agentmvc@{database}:5432/production",
                "-e",
                "SECRET_KEY_BASE=preflight-production-secret",
                "-e",
                f"PORT={PORT}",
                prod_image,
            ]
        )
        launched.append(production)
        report["production_start_seconds"] = ready()
        socket(production)
        queue(production)
        run(
            [
                "docker",
                "exec",
                production,
                "python",
                "-c",
                (
                    "import os,importlib.util; assert os.getuid()!=0; assert importlib.util.find_spec('ruff') is None; "
                    "os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings'); "
                    "from django.contrib.auth.hashers import make_password,check_password; "
                    "import django; django.setup(); assert check_password('東京 café',make_password('東京 café'))"
                ),
            ],
            check=True,
        )
        report["checks"]["fresh_production_health_queue_socket_crypto_nonroot"] = True
        image_info = json.loads(run(["docker", "image", "inspect", prod_image]))[0]
        report["production_image"] = image_info["Id"]
        report["production_image_bytes"] = image_info["Size"]
        report["status"] = "passed"
        report["passed"] = True
    except Exception as error:
        report["status"] = "failed"
        report["passed"] = False
        report["error"] = str(error)
        raise
    finally:
        for name in reversed(launched):
            run(["docker", "logs", name], check=False)
            run(["docker", "rm", "-f", name], check=False)
        run(["docker", "network", "rm", network], check=False)
        report["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        files = {
            str(path.relative_to(STACK / "scaffold")): hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
            for path in sorted((STACK / "scaffold").rglob("*"))
            if path.is_file()
            and not {
                ".venv",
                "__pycache__",
                ".ruff_cache",
                ".pytest_cache",
            }.intersection(path.parts)
        }
        report["scaffold_files"] = files
        report["scaffold_sha256"] = hashlib.sha256(
            json.dumps(files, sort_keys=True).encode()
        ).hexdigest()
        report["command_log"] = str(results.with_suffix(".log").relative_to(ROOT))
        results.with_suffix(".log").write_text(
            (work / "commands.log").read_text().replace(str(ROOT), "<repo>")
        )
        results.write_text(json.dumps(report, indent=2) + "\n")
        log.close()
        print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    main()
