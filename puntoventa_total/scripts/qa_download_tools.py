"""Descarga herramientas portables QA; verifica digest SHA256 publicado por GitHub."""
import argparse
import hashlib
import json
from pathlib import Path
import tempfile
from urllib.request import Request, urlopen
import zipfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tool", choices=["k6", "redis"])
    parser.add_argument("--asset")
    args = parser.parse_args()
    repo = {"k6": "grafana/k6", "redis": "redis-windows/redis-windows"}[args.tool]
    request = Request(f"https://api.github.com/repos/{repo}/releases/latest", headers={"User-Agent": "PuntoVenta-QA"})
    with urlopen(request, timeout=30) as response:
        release = json.load(response)
    if not args.asset:
        print(json.dumps({"tag": release["tag_name"], "assets": [a["name"] for a in release["assets"]]}, indent=2))
        return
    asset = next(a for a in release["assets"] if a["name"] == args.asset)
    digest = asset.get("digest", "")
    if not digest.startswith("sha256:"):
        raise RuntimeError("La publicacion no proporciona SHA256; no se ejecutara sin verificar")
    directory = Path(tempfile.gettempdir()) / "puntoventa-qa-tools" / args.tool / release["tag_name"]
    directory.mkdir(parents=True, exist_ok=True)
    archive = directory / asset["name"]
    if not archive.exists() or hashlib.sha256(archive.read_bytes()).hexdigest() != digest.split(":", 1)[1]:
        with urlopen(asset["browser_download_url"], timeout=60) as response:
            archive.write_bytes(response.read())
    if hashlib.sha256(archive.read_bytes()).hexdigest() != digest.split(":", 1)[1]:
        raise RuntimeError("SHA256 no coincide")
    with zipfile.ZipFile(archive) as bundle:
        for member in bundle.infolist():
            (directory / member.filename).resolve().relative_to(directory.resolve())
        bundle.extractall(directory)
    (directory / "source.json").write_text(json.dumps({"repository": repo, "tag": release["tag_name"],
        "asset": asset["name"], "digest": digest}, indent=2), encoding="utf-8")
    print(directory)


if __name__ == "__main__":
    main()
