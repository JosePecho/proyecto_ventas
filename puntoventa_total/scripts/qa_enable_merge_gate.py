"""Agrega los checks de calidad a main preservando otras protecciones existentes."""
import argparse
import json
from pathlib import Path

import requests

from qa_github_status import github_context


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verified-head", required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    repo, headers, authenticated = github_context()
    if not authenticated:
        raise RuntimeError("Se requiere acceso autenticado al repositorio")
    base = "https://api.github.com/repos/" + repo
    required = {"quality (production-declared)", "quality (qa)"}
    response = requests.get(base + f"/commits/{args.verified_head}/check-runs", headers=headers, timeout=20)
    response.raise_for_status()
    successful = {check["name"] for check in response.json()["check_runs"] if check["conclusion"] == "success"}
    if not required <= successful:
        raise RuntimeError("El commit indicado no tiene aprobados ambos checks")
    url = base + "/branches/main/protection"
    response = requests.get(url, headers=headers, timeout=20)
    if response.status_code == 404:
        method = "PUT"
        proposal = {"required_status_checks": {"strict": True, "contexts": sorted(required)},
                    "enforce_admins": True, "required_pull_request_reviews": None, "restrictions": None,
                    "allow_force_pushes": False, "allow_deletions": False}
    else:
        response.raise_for_status()
        existing = response.json().get("required_status_checks") or {}
        checks = {item["context"]: {"context": item["context"], "app_id": item["app_id"]}
                  for item in existing.get("checks", [])}
        for context in set(existing.get("contexts", [])) | required:
            checks.setdefault(context, {"context": context})
        method, url = "PATCH", url + "/required_status_checks"
        proposal = {"strict": True, "checks": list(checks.values())}
    print(json.dumps({"repository": repo, "branch": "main", "method": method, "proposal": proposal}, indent=2))
    if args.apply:
        response = requests.request(method, url, headers=headers, json=proposal, timeout=20)
        if not response.ok:
            raise RuntimeError(f"GitHub rechazo la proteccion ({response.status_code}): " + response.json().get("message", ""))
        verification = requests.get(base + "/branches/main/protection/required_status_checks", headers=headers, timeout=20)
        verification.raise_for_status()
        state = verification.json()
        if not required <= set(state.get("contexts", [])):
            raise RuntimeError("La verificacion no contiene ambos checks requeridos")
        (Path(__file__).resolve().parents[1] / "reports/merge-gate.json").write_text(json.dumps(state, indent=2), encoding="utf-8")
        print("Verificado: ambos checks son obligatorios en main")


if __name__ == "__main__":
    main()
