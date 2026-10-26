"""Genera los recursos SVG locales del catalogo, sin servicios externos."""
from pathlib import Path


DESTINO = Path(__file__).resolve().parents[1] / "static" / "images" / "productos"


def generar():
    botella = '<path d="M142 55h36v35l20 26v118q-38 14-76 0V116l20-26z" fill="{color}"/><rect x="139" y="45" width="42" height="16" rx="4" fill="#334155"/><rect x="124" y="135" width="72" height="58" rx="8" fill="#fff" opacity=".92"/><path d="M134 113v15m0 76v18" stroke="#fff" stroke-width="6" stroke-linecap="round" opacity=".5"/>'
    bolsa = '<path d="M110 66h100l-9 32 16 134q-56 18-112 0l15-134z" fill="{color}"/><path d="M113 70h94M109 225h104" stroke="#fff" stroke-width="5" opacity=".5"/><rect x="119" y="116" width="82" height="75" rx="12" fill="#fff" opacity=".92"/><path d="M143 158q17-35 34 0q-17 34-34 0" fill="{color}"/>'
    lata = '<ellipse cx="160" cy="82" rx="53" ry="17" fill="#cbd5e1"/><path d="M107 82v132a53 17 0 0 0 106 0V82" fill="{color}"/><ellipse cx="160" cy="82" rx="53" ry="17" fill="#e2e8f0"/><ellipse cx="160" cy="82" rx="41" ry="10" fill="none" stroke="#94a3b8" stroke-width="2"/><rect x="109" y="116" width="102" height="73" fill="#fff" opacity=".92"/><path d="m142 150 24-15 22 15-22 15z" fill="{color}"/>'
    caja = '<path d="m117 85 31-32h41l22 32v148H117z" fill="{color}"/><path d="m148 53 18 32h45l-22-32z" fill="#fff" opacity=".35"/><path d="M166 85v148" stroke="#fff" opacity=".35"/><rect x="125" y="117" width="78" height="72" rx="8" fill="#fff" opacity=".95"/><path d="M161 129q-31 33 0 45q31-12 0-45" fill="{color}"/>'
    dibujos = {
        "aceite": ("#d5a51e", botella), "agua": ("#60b7dc", botella),
        "gaseosa": ("#944e36", botella), "jugo": ("#ec9831", caja),
        "yogur": ("#d9648d", botella), "leche": ("#548cc2", caja),
        "abarrotes": ("#bc8e57", bolsa), "fideos": ("#d7a434", bolsa),
        "snacks": ("#dd7940", bolsa), "conserva": ("#4c9a8d", lata),
        "limpieza": ("#5d9ca1", botella),
        "queso": ("#e6bd51", '<path d="m106 164 91-66 23 81-114 35z" fill="{color}"/><path d="m106 164 114 15v44l-114-9z" fill="#e5ac32"/><path d="m106 164 91-66 23 81z" fill="#f6d572"/><g fill="#d39b29"><circle cx="176" cy="151" r="9"/><circle cx="146" cy="166" r="7"/><circle cx="187" cy="201" r="8"/><circle cx="128" cy="193" r="6"/></g>'),
        "chocolate": ("#794633", '<rect x="105" y="65" width="110" height="173" rx="8" fill="{color}"/><path d="M141 72v100m37-100v100M111 103h98m-98 36h98" stroke="#a57150" stroke-width="5"/><path d="m100 161 120 12v69H100z" fill="#b85362"/><path d="m100 161 30 8 20-10 24 14 26-7 20 7" fill="none" stroke="#e2d7bf" stroke-width="8"/>'),
        "galletas": ("#c38b4c", '<rect x="90" y="77" width="140" height="157" rx="15" fill="#e7b56f"/><circle cx="160" cy="153" r="48" fill="{color}" stroke="#f6d49a" stroke-width="5"/><g fill="#68472f"><circle cx="140" cy="133" r="5"/><circle cx="177" cy="144" r="6"/><circle cx="150" cy="169" r="6"/><circle cx="179" cy="176" r="4"/><circle cx="129" cy="157" r="4"/></g>'),
        "papel": ("#9aabb9", '<rect x="91" y="92" width="140" height="128" rx="20" fill="#c2d9cf"/><path d="M108 120h43v83h-43zm61 0h43v83h-43z" fill="#fff"/><ellipse cx="129" cy="120" rx="22" ry="10" fill="#e2e8f0"/><ellipse cx="190" cy="120" rx="22" ry="10" fill="#e2e8f0"/><g fill="{color}"><ellipse cx="129" cy="120" rx="7" ry="4"/><ellipse cx="190" cy="120" rx="7" ry="4"/></g>'),
        "pasta": ("#4e9e96", '<path d="m128 65 74 10-22 136h-49z" fill="#f8fafc" stroke="#cbd5e1" stroke-width="2"/><path d="m125 104 70 8-10 70-58-8z" fill="{color}"/><rect x="132" y="211" width="47" height="24" rx="4" fill="{color}"/><path d="m130 69 68 9" stroke="{color}" stroke-width="9"/>'),
        "jabon": ("#d598a8", '<rect x="91" y="101" width="140" height="97" rx="35" fill="{color}"/><rect x="105" y="113" width="111" height="71" rx="28" fill="none" stroke="#fff" stroke-width="3" opacity=".6"/><g fill="#fff" opacity=".6"><circle cx="207" cy="72" r="12"/><circle cx="232" cy="95" r="8"/><circle cx="184" cy="59" r="6"/></g>'),
    }
    DESTINO.mkdir(parents=True, exist_ok=True)
    for tipo, (color, forma) in dibujos.items():
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 280">
<ellipse cx="160" cy="242" rx="70" ry="10" fill="#253041" opacity=".1"/>
{forma.format(color=color)}</svg>'''
        (DESTINO / f"{tipo}.svg").write_text(svg, encoding="utf-8")


if __name__ == "__main__":
    generar()
