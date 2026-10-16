"""Inspeccion read-only del acceso y workflows del remoto, sin imprimir secretos."""
import json
import os
import subprocess
import sys
import requests
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def main():
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
    evidence = {"repository": repo, "credential_available": bool(token)}
    for endpoint in ("", "/actions/workflows", "/actions/runs?per_page=3"):
        try:
            with urlopen(Request("https://api.github.com/repos/" + repo + endpoint, headers=headers), timeout=20) as response:
                data = json.load(response)
            if not endpoint:
                evidence.update(default_branch=data["default_branch"], permissions=data.get("permissions", {}))
            elif "workflows" in endpoint:
                evidence["workflows"] = [{"name": w["name"], "path": w["path"]} for w in data["workflows"]]
            else:
                evidence["runs"] = [{"name": r["name"], "status": r["status"], "conclusion": r["conclusion"],
                    "url": r["html_url"]} for r in data["workflow_runs"]]
                for run, item in zip(data["workflow_runs"], evidence["runs"]):
                    with urlopen(Request(run["jobs_url"], headers=headers), timeout=20) as response:
                        jobs = json.load(response)
                    item["jobs"] = [{"name": j["name"], "conclusion": j["conclusion"],
                        "failed_steps": [s["name"] for s in j.get("steps", []) if s["conclusion"] == "failure"]}
                        for j in jobs["jobs"]]
                    if "--logs" in sys.argv:
                        for job, job_item in zip(jobs["jobs"], item["jobs"]):
                            if job["conclusion"] == "failure":
                                response = requests.get(job["url"] + "/logs", headers=headers, timeout=30)
                                job_item["failure_log_tail"] = response.text.splitlines()[-85:] if response.ok else response.status_code
        except HTTPError as exc:
            evidence[endpoint or "repo_status"] = exc.code
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
