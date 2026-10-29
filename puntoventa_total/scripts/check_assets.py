"""Compila todas las plantillas; opcionalmente valida JavaScript en Chromium."""
import argparse
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.testing")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--javascript", action="store_true")
    args = parser.parse_args()
    import django
    django.setup()
    from django.template.loader import get_template
    errores = []
    plantillas = list((ROOT / "templates").rglob("*.html"))
    for archivo in plantillas:
        try:
            get_template(archivo.relative_to(ROOT / "templates").as_posix())
        except Exception as exc:
            errores.append(f"{archivo.relative_to(ROOT)}: {exc}")
    print(f"Templates compilados: {len(plantillas) - len(errores)}/{len(plantillas)}")
    if args.javascript:
        from playwright.sync_api import sync_playwright
        scripts = list((ROOT / "static/js").rglob("*.js"))
        fallos_js = 0
        with sync_playwright() as motor:
            browser = motor.chromium.launch()
            try:
                page = browser.new_page()
                for archivo in scripts:
                    try:
                        page.evaluate("source => { new Function(source); return true; }", archivo.read_text(encoding="utf-8-sig"))
                    except Exception as exc:
                        errores.append(f"{archivo.relative_to(ROOT)}: {exc}")
                        fallos_js += 1
            finally:
                browser.close()
        print(f"JavaScript compilado: {len(scripts) - fallos_js}/{len(scripts)}")
    for error in errores:
        print(error)
    return 1 if errores else 0


if __name__ == "__main__":
    raise SystemExit(main())
