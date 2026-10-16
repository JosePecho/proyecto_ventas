from unittest.mock import Mock

import pytest

from src.modules.catalog.application.use_cases.listar_productos import ListarProductos
from src.modules.catalog.application.use_cases.filtrar_por_categoria import FiltrarPorCategoria
from src.modules.catalog.application.use_cases.consultar_disponibilidad import ConsultarDisponibilidad
from src.modules.catalog.application.ports.disponibilidad_port import DisponibilidadPort
from src.modules.catalog.domain.repositories.producto_repository import ProductoRepository
from src.modules.catalog.domain.exceptions.producto_exceptions import ProductoNoEncontrado

pytestmark = pytest.mark.unit


@pytest.mark.parametrize("pagina,esperada,offset", [(1, 1, 0), (2, 2, 20), (-1, 1, 0), (999, 3, 40)])
def test_paginacion_se_resuelve_en_repositorio(producto_faker, pagina, esperada, offset):
    repo = Mock(spec=ProductoRepository)
    repo.contar.return_value = 41
    repo.listar.return_value = [producto_faker()]
    resultado = ListarProductos(repo).ejecutar(pagina=pagina, termino="arroz", categoria_id="categoria")
    assert resultado.pagina == esperada
    assert len(resultado.items) == 1
    repo.listar.assert_called_once_with(incluir_inactivos=False, termino="arroz", categoria_id="categoria", limit=20, offset=offset)
    repo.contar.assert_called_once_with(incluir_inactivos=False, termino="arroz", categoria_id="categoria")


@pytest.mark.parametrize("tamano,esperado", [(0, 1), (-10, 1), (20, 20), (999, 100)])
def test_tamano_de_pagina_acotado(tamano, esperado):
    repo = Mock(spec=ProductoRepository)
    repo.contar.return_value = 0
    repo.listar.return_value = []
    pagina = ListarProductos(repo).ejecutar(pagina=99, por_pagina=tamano)
    assert pagina.pagina == 1 and pagina.total_paginas == 1
    assert pagina.por_pagina == esperado and not pagina.items


def test_filtro_categoria_utiliza_paginacion_completa():
    repo = Mock(spec=ProductoRepository)
    repo.contar.return_value = 45
    repo.listar.return_value = []
    FiltrarPorCategoria(repo).ejecutar("bebidas", pagina=2)
    assert repo.listar.call_args.kwargs["offset"] == 20
    assert repo.listar.call_args.kwargs["categoria_id"] == "bebidas"


@pytest.mark.parametrize("stock", [0, 1, 7])
def test_disponibilidad_actual_y_agotado(producto_faker, stock):
    repo, puerto = Mock(spec=ProductoRepository), Mock(spec=DisponibilidadPort)
    producto = producto_faker()
    repo.buscar_por_id.return_value = producto
    puerto.stock_disponible.return_value = stock
    puerto.tiene_stock_minimo.return_value = stock < 5
    resultado = ConsultarDisponibilidad(repo, puerto).ejecutar(str(producto.id))
    assert resultado["stock_disponible"] == stock
    assert resultado["vendible"] == (stock > 0)


def test_detalle_inexistente_rechazado_sin_consultar_stock():
    repo, puerto = Mock(spec=ProductoRepository), Mock(spec=DisponibilidadPort)
    repo.buscar_por_id.return_value = None
    with pytest.raises(ProductoNoEncontrado):
        ConsultarDisponibilidad(repo, puerto).ejecutar("inexistente")
    puerto.stock_disponible.assert_not_called()
