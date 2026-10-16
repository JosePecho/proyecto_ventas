/* Cola de acciones pendientes cuando no hay conexion */
const ColaOffline = {
  async encolar(url, datos) {
    const db = await IndexedDB.abrir();
    const transaccion = db.transaction("cola_envios", "readwrite");
    transaccion.objectStore("cola_envios").put({
      uuid: crypto.randomUUID(),
      url,
      datos,
      fecha: new Date().toISOString(),
      intentos: 0,
    });
    return new Promise((resolver) => (transaccion.oncomplete = resolver));
  },

  async pendientes() {
    const db = await IndexedDB.abrir();
    return new Promise((resolver) => {
      const solicitud = db.transaction("cola_envios", "readonly").objectStore("cola_envios").getAll();
      solicitud.onsuccess = () => resolver(solicitud.result || []);
    });
  },

  async quitar(uuid) {
    const db = await IndexedDB.abrir();
    const transaccion = db.transaction("cola_envios", "readwrite");
    transaccion.objectStore("cola_envios").delete(uuid);
    return new Promise((resolver) => (transaccion.oncomplete = resolver));
  },

  async incrementarIntento(uuid) {
    const db = await IndexedDB.abrir();
    const transaccion = db.transaction("cola_envios", "readwrite");
    const almacen = transaccion.objectStore("cola_envios");
    const solicitud = almacen.get(uuid);
    solicitud.onsuccess = () => {
      const registro = solicitud.result;
      registro.intentos += 1;
      almacen.put(registro);
    };
    return new Promise((resolver) => (transaccion.oncomplete = resolver));
  },
};

// Intercepta POST mientras se esta offline
window.interceptarPost = async function (url, datos) {
  if (navigator.onLine) {
    return PV.post(url, datos);
  }
  await ColaOffline.encolar(url, datos);
  PV.alerta("warning", "Sin conexion: accion encolada y se sincronizara automaticamente");
  return { encolado: true };
};

