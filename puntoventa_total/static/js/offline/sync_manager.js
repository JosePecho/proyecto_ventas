/* Sincroniza la cola local contra el servidor al recuperar conexion */
const SyncManager = {
  MAX_INTENTOS: 5,

  init() {
    window.addEventListener("online", () => this.sincronizar());
    document.addEventListener("visibilitychange", () => {
      if (!document.hidden && navigator.onLine) this.sincronizar();
    });
  },

  async sincronizar() {
    const pendientes = await ColaOffline.pendientes();
    if (pendientes.length === 0) return;

    PV.alerta("info", `Sincronizando ${pendientes.length} acciones pendientes...`);

    // Orden por fecha para respetar la secuencia de cobros
    for (const accion of pendientes.sort((a, b) => a.fecha.localeCompare(b.fecha))) {
      try {
        await PV.post(accion.url, accion.datos);
        await ColaOffline.quitar(accion.uuid);
      } catch (error) {
        await ColaOffline.incrementarIntento(accion.uuid);
        if (accion.intentos >= this.MAX_INTENTOS) {
          console.error("Accion descartada tras varios intentos:", accion);
          await ColaOffline.quitar(accion.uuid);
        }
        break; // si falla una, se reintenta todo despues
      }
    }
    PV.alerta("success", "Sincronizacion completada");
  },
};

SyncManager.init();

