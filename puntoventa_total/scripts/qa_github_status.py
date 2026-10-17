"""Inspeccion read-only del acceso y workflows del remoto, sin imprimir secretos."""
import json
import argparse
import io
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import zipfile
import requests
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def github_context():
    remote = subprocess.check_output(["git", "remote", "get-url", "origin"], text=True).strip()
    if not remote.startswith("https://github.com/"):
        raise RuntimeError("Se requiere remoto HTTPS github.com")
    repo = remote.removeprefix("https://github.com/").removesuffix(".git")
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        env = dict(os.environ, GIT_TERMINAL_PROMPT="0", GCM_INTERACTIVE="never")
        result = subprocess.run(["git", "-c", "credential.interactive=never", "credential", "fill"],
            input=f"protocol=https\nhost=github.com\npath={repo}.git\n\n", capture_output=True,
            text=True, env=env, timeout=15)
        values = dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)
        token = values.get("password")
    headers = {"User-Agent": "PuntoVenta-QA", "Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    return repo, headers, bool(token)


def collect(branch=None):
    repo, headers, authenticated = github_context()
    evidence = {"repository": repo, "credential_available": authenticated}
    runs_endpoint = "/actions/runs?per_page=" + ("1&branch=" + branch if branch else "3")
    for endpoint in ("", "/actions/workflows", runs_endpoint):
        try:
            with urlopen(Request("https://api.github.com/repos/" + repo + endpoint, headers=headers), timeout=20) as response:
                data = json.load(response)
            if not endpoint:
                evidence.update(default_branch=data["default_branch"], permissions=data.get("permissions", {}))
            elif "workflows" in endpoint:
                evidence["workflows"] = [{"name": w["name"], "path": w["path"]} for w in data["workflows"]]
            else:
                evidence["runs"] = [{"name": r["name"], "status": r["status"], "conclusion": r["conclusion"],
                    "url": r["html_url"], "head_sha": r["head_sha"]} for r in data["workflow_runs"]]
                for run, item in zip(data["workflow_runs"], evidence["runs"]):
                    with urlopen(Request(run["jobs_url"], headers=headers), timeout=20) as response:
                        jobs = json.load(response)
                    item["jobs"] = [{"name": j["name"], "conclusion": j["conclusion"],
                        "active_steps": [s["name"] for s in j.get("steps", []) if s["status"] == "in_progress"],
                        "failed_steps": [s["name"] for s in j.get("steps", []) if s["conclusion"] == "failure"]}
                        for j in jobs["jobs"]]
                    if "--logs" in sys.argv:
                        for job, job_item in zip(jobs["jobs"], item["jobs"]):
                            if job["conclusion"] == "failure":
                                response = requests.get(job["url"] + "/logs", headers=headers, timeout=30)
                                job_item["failure_log_tail"] = [line for line in response.text.splitlines()
                                    if re.search(r"FAIL|Error:|E   |assert |THRESHOLD|checks|p\(95\)|passed|skipped|Traceback", line)][-100:] if response.ok else response.status_code
                    if "--artifacts" in sys.argv and run["status"] == "completed":
                        response = requests.get(run["artifacts_url"], headers=headers, timeout=30)
                        response.raise_for_status()
                        item["artifacts"] = []
                        for artifact in response.json()["artifacts"]:
                            directory = Path(__file__).resolve().parents[1] / "reports/remote" / str(run["id"]) / artifact["name"]
                            directory.resolve().relative_to((Path(__file__).resolve().parents[1] / "reports/remote").resolve())
                            response = requests.get(artifact["archive_download_url"], headers=headers, timeout=60)
                            response.raise_for_status()
                            directory.mkdir(parents=True, exist_ok=True)
                            with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
                                for member in archive.infolist():
                                    (directory / member.filename).resolve().relative_to(directory.resolve())
                                archive.extractall(directory)
                            item["artifacts"].append({"name": artifact["name"], "directory": str(directory)})
        except HTTPError as exc:
            evidence[endpoint or "repo_status"] = exc.code
    return evidence


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--branch")
    parser.add_argument("--watch", action="store_true")
    parser.add_argument("--logs", action="store_true")
    parser.add_argument("--head")
    parser.add_argument("--artifacts", action="store_true")
    args = parser.parse_args()
    for attempt in range(40 if args.watch else 1):
        result = collect(args.branch)
        path = Path(__file__).resolve().parents[1] / "reports/remote-ci.json"
        path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(json.dumps(result, indent=2), flush=True)
        runs = result.get("runs", [])
        if not args.watch or (runs and runs[0]["status"] == "completed" and
                              (not args.head or runs[0]["head_sha"].startswith(args.head))):
            break
        time.sleep(15)
