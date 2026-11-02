(() => {
  const editor = document.getElementById('combo-editor');
  if (!editor) return;
  const form = editor.closest('form');
  const tipo = form.querySelector('[name="tipo"]');
  const productos = JSON.parse(document.getElementById('combo-catalogo').textContent);
  const filas = document.getElementById('combo-filas');
  function agregar(inicial = {}) {
    const fila = document.createElement('div');
    const producto = document.createElement('select');
    producto.name = 'combo_producto';
    producto.setAttribute('aria-label', 'Producto del combo');
    producto.add(new Option('Seleccione producto', ''));
    for (const p of productos) producto.add(new Option(p.nombre, p.id));
    producto.value = inicial.producto_id || '';
    const cantidad = document.createElement('input');
    cantidad.type = 'number'; cantidad.min = '1'; cantidad.step = '1';
    cantidad.name = 'combo_cantidad'; cantidad.value = inicial.cantidad || 1;
    cantidad.setAttribute('aria-label', 'Cantidad del combo');
    const quitar = document.createElement('button');
    quitar.type = 'button'; quitar.textContent = 'Quitar';
    quitar.addEventListener('click', () => fila.remove());
    fila.append(producto, cantidad, quitar); filas.append(fila);
    actualizar();
  }
  function actualizar() {
    const activo = tipo.value === 'COMBO';
    editor.hidden = !activo;
    filas.querySelectorAll('select,input').forEach(campo => { campo.disabled = !activo; campo.required = activo; });
  }
  let iniciales = [];
  try { iniciales = JSON.parse(form.querySelector('[name="componentes"]').value || '[]'); } catch (_) { /* Validación en servidor. */ }
  (Array.isArray(iniciales) && iniciales.length ? iniciales : [{}, {}]).forEach(agregar);
  document.getElementById('combo-agregar').addEventListener('click', () => agregar());
  tipo.addEventListener('change', actualizar);
  actualizar();
})();
