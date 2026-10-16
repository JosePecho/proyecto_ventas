"""Redis efimero real en localhost; sin servicios persistentes ni datos existentes."""
import argparse
from contextlib import contextmanager
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import tempfile
import time
from urllib.parse import quote

from redis import Redis


@contextmanager
def redis_temporal(binary):
    binary = Path(binary).resolve()
    if not binary.is_file():
        raise FileNotFoundError(binary)
    with socket.socket() as reserved:
        reserved.bind(("127.0.0.1", 0))
        port = reserved.getsockname()[1]
    password = secrets.token_urlsafe(32)
    with tempfile.TemporaryDirectory(prefix="puntoventa-redis-") as directory:
        config = Path(directory) / "redis.conf"
        config.write_text(f'bind 127.0.0.1\nport {port}\nprotected-mode yes\n'
                          f'requirepass {password}\nsave ""\nappendonly no\n', encoding="utf-8")
        with (Path(directory) / "redis.log").open("w", encoding="utf-8") as log:
            process = subprocess.Popen([str(binary), "redis.conf"], cwd=directory, stdout=log,
                stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
            url = f"redis://:{quote(password)}@127.0.0.1:{port}/15"
            client = Redis.from_url(url, socket_connect_timeout=1, socket_timeout=1)
            try:
                deadline = time.monotonic() + 20
                while True:
                    if process.poll() is not None:
                        raise RuntimeError("Redis no inicio: " + (Path(directory) / "redis.log").read_text())
                    try:
                        if client.ping():
                            break
                    except (ConnectionError, OSError):
                        pass
                    except Exception:
                        if time.monotonic() > deadline:
                            raise
                    if time.monotonic() > deadline:
                        raise TimeoutError("Redis no estuvo listo")
                    time.sleep(0.1)
                yield url, client.info("server")["redis_version"]
            finally:
                try:
                    client.shutdown(nosave=True)
                except Exception:
                    process.terminate()
                client.close()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", required=True)
    parser.add_argument("--mysql-basedir")
    parser.add_argument("--k6-binary")
    parser.add_argument("--target", action="append")
    parser.add_argument("--coverage", action="store_true")
    parser.add_argument("--report-prefix", default="full-validation")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    with redis_temporal(args.binary) as (url, version):
        env = dict(os.environ, QA_REDIS_URL=url)
        if args.k6_binary:
            env["QA_K6_BINARY"] = str(Path(args.k6_binary).resolve())
        if args.mysql_basedir:
            env["QA_REQUIRE_ALL_TESTS"] = "1"
            command = [sys.executable, "scripts/qa_inventory_mysql_native.py", "--basedir", args.mysql_basedir, "--full"]
            command += ["--report-prefix", args.report_prefix]
            if args.coverage:
                command.append("--coverage")
            if args.target:
                env.pop("QA_REQUIRE_ALL_TESTS", None)
                for target in args.target:
                    command += ["--target", target]
        else:
            command = [sys.executable, "-m", "pytest", "tests/integration/test_redis_celery_real.py", "-q", "-p", "no:cacheprovider"]
        result = subprocess.run(command, cwd=root, env=env)
        evidence = {"redis_version": version, "ephemeral": True, "exit_code": result.returncode,
                    "mysql_full": bool(args.mysql_basedir and not args.target), "k6": bool(args.k6_binary)}
        (root / "reports").mkdir(exist_ok=True)
        (root / "reports/redis-real.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
        print(json.dumps(evidence))
        return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
