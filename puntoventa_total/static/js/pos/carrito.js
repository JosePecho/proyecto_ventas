/* Logica del carrito del POS contra los endpoints de sales */
const POS = {
  ventaId: null,

  init(ventaId) {
    this.ventaId = ventaId;
    const entrada = document.getElementById("buscador-pos");

    entrada?.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        this.buscar(entrada.value.trim());
      }
    });
    document.getElementById("btn-buscar")?.addEventListener("click", () => this.buscar(entrada.value.trim()));

    Scanner.init((codigo) => this.buscar(codigo));
    Shortcuts.init(this);
  },

  async buscar(termino) {
    if (!termino) return;
    const respuesta = await fetch(`/pos/buscar/?q=${encodeURIComponent(termino)}`);
    const datos = await respuesta.json();
    const contenedor = document.getElementById("resultados-busqueda");
    contenedor.innerHTML = "";

    datos.resultados.forEach((producto) => {
      const item = document.createElement("button");
      item.type = "button";
      item.className = "list-group-item list-group-item-action d-flex justify-content-between";
      const nombre = document.createElement("span");
      nombre.textContent = producto.nombre;
      const precio = document.createElement("span");
      precio.className = "fw-bold";
      precio.textContent = PV.money(producto.precio);
      item.append(nombre, precio);
      item.addEventListener("click", () => this.agregar(producto.id));
      contenedor.appendChild(item);
    });

    if (datos.resultados.length === 1) this.agregar(datos.resultados[0].id);
  },

  async agregar(productoId) {
    try {
      await PV.post(`/pos/venta/${this.ventaId}/agregar/${productoId}/`);
      PV.alerta("success", "Producto agregado");
      this.actualizarTotales();
    } catch (e) {
      PV.alerta("danger", "No se pudo agregar el producto");
    }
  },

  async cambiarCantidad(productoId, cantidad) {
    try {
      await PV.post(`/pos/venta/${this.ventaId}/cantidad/${productoId}/`, { cantidad });
      this.actualizarTotales();
    } catch (error) { PV.alerta("danger", "No se pudo cambiar la cantidad"); }
  },

  async eliminar(productoId) {
    try {
      await PV.post(`/pos/venta/${this.ventaId}/eliminar/${productoId}/`);
      this.actualizarTotales();
    } catch (error) { PV.alerta("danger", "No se pudo eliminar el producto"); }
  },

  async actualizarTotales() {
    // Sencillo: recarga liviana de la pagina de pago/totales
    window.location.reload();
  },
};

// Delegacion de eventos del carrito (botones +/- y eliminar)
document.addEventListener("click", (evento) => {
  const item = evento.target.closest("[data-producto]");
  if (!item) return;
  const productoId = item.dataset.producto;
  const cantidadInput = item.querySelector(".cantidad");

  if (evento.target.classList.contains("btn-mas")) {
    POS.cambiarCantidad(productoId, Number(cantidadInput.value) + 1);
  } else if (evento.target.classList.contains("btn-menos")) {
    const nueva = Number(cantidadInput.value) - 1;
    if (nueva > 0) POS.cambiarCantidad(productoId, nueva);
  } else if (evento.target.classList.contains("btn-eliminar")) {
    POS.eliminar(productoId);
  }
});

