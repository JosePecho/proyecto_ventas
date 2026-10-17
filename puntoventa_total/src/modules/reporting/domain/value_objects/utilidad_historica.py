from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP


def agrupar_utilidad(detalles):
    """Distribuye descuentos globales y conserva centavos/costos congelados."""
    por_venta = defaultdict(list)
    for detalle in detalles:
        por_venta[detalle["venta_id"]].append(detalle)
    productos = {}
    for lineas in por_venta.values():
        base = sum((Decimal(str(l["importe"])) for l in lineas), Decimal(0))
        total = Decimal(str(lineas[0]["total_venta"]))
        restante = total
        for indice, linea in enumerate(lineas):
            ingreso = restante if indice == len(lineas) - 1 else (
                Decimal(str(linea["importe"])) * total / base if base else Decimal(0)
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            ingreso = max(Decimal(0), min(restante, ingreso))
            restante -= ingreso
            fila = productos.setdefault(linea["producto_id"], {
                "producto_id": linea["producto_id"], "producto_nombre": linea["producto_nombre"],
                "unidades": 0, "ingresos": Decimal(0), "costo": Decimal(0), "estimado": False,
            })
            fila["unidades"] += linea["cantidad"]
            fila["ingresos"] += ingreso
            if linea["costo_unitario"] is None:
                fila["estimado"] = True
            else:
                fila["costo"] += Decimal(str(linea["costo_unitario"])) * linea["cantidad"]
    for fila in productos.values():
        fila["utilidad"] = round(fila["ingresos"] - fila["costo"], 2)
        for campo in ("ingresos", "costo", "utilidad"):
            fila[campo] = float(fila[campo])
    return sorted(productos.values(), key=lambda f: (-f["ingresos"], f["producto_id"]))
