"""Guarda el HTML de páginas de cartas como fixtures, para preparar un gestor nuevo.
Uso: python scripts/probe.py id=https://... id2=https://...
Respeta robots.txt con el mismo user agent que la revisión semanal."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from update import Fetcher  # noqa: E402

out = pathlib.Path(__file__).resolve().parent.parent / "tests" / "fixtures"
out.mkdir(parents=True, exist_ok=True)
f = Fetcher()
for arg in sys.argv[1:]:
    mid, url = arg.split("=", 1)
    try:
        html, final = f.get(mid, url)
        (out / f"{mid}.html").write_text(html, encoding="utf-8")
        print(f"OK   {mid}: {len(html)} bytes from {final}")
    except Exception as e:
        print(f"FAIL {mid}: {e}")
