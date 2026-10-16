/* Persistencia local de productos y carrito para modo offline */
const IndexedDB = {
  NOMBRE: "puntoventa_offline",
  VERSION: 1,

  abrir() {
    return new Promise((resolver, rechazar) => {
      const solicitud = indexedDB.open(this.NOMBRE, this.VERSION);
      solicitud.onupgradeneeded = (evento) => {
        const db = evento.target.result;
        if (!db.objectStoreNames.contains("productos")) {
          db.createObjectStore("productos", { keyPath: "id" });
        }
        if (!db.objectStoreNames.contains("cola_envios")) {
          const cola = db.createObjectStore("cola_envios", { keyPath: "uuid", autoIncrement: false });
          cola.createIndex("url", "url", { unique: false });
        }
      };
      solicitud.onsuccess = () => resolver(solicitud.result);
      solicitud.onerror = () => rechazar(solicitud.error);
    });
  },

  async guardarProductos(productos) {
    const db = await this.abrir();
    const transaccion = db.transaction("productos", "readwrite");
    const almacen = transaccion.objectStore("productos");
    productos.forEach((p) => almacen.put(p));
    return new Promise((resolver) => (transaccion.oncomplete = resolver));
  },

  async buscarProducto(codigo) {
    const db = await this.abrir();
    const almacen = db.transaction("productos", "readonly").objectStore("productos");
    return new Promise((resolver) => {
      const indice = almacen.index("codigo_barras");
      const solicitud = indice.get(codigo);
      solicitud.onsuccess = () => resolver(solicitud.result || null);
    });
  },

  async obtenerProductos() {
    const db = await this.abrir();
    return new Promise((resolver) => {
      const solicitud = db.transaction("productos", "readonly").objectStore("productos").getAll();
      solicitud.onsuccess = () => resolver(solicitud.result);
    });
  },
};

