/* Resolucion de conflictos: mismo producto/cobro registrado dos veces */
const ConflictResolver = {
  /*
   * Reglas:
   *  - Si el servidor ya tiene el mismo numero de ticket, se descarta la copia local.
   *  - Si el stock cambio entre la venta offline y la sincronizacion, prevalece el
   *    servidor y se notifica al cajero.
   */
  resolver(local, remoto) {
    if (!remoto) return local;
    if (local.numero_ticket === remoto.numero_ticket) {
      return { accion: "descartar_local", motivo: "ticket_duplicado" };
    }
    if (Number(local.total) !== Number(remoto.total)) {
      return { accion: "usar_remoto", motivo: "total_divergente", remoto };
    }
    return { accion: "usar_local", motivo: "sin_conflicto" };
  },

  async resolverVentaOffline(ventaLocal) {
    const respuesta = await fetch(`/pos/ventas/?ticket=${encodeURIComponent(ventaLocal.numero_ticket)}`);
    const remoto = respuesta.ok ? await respuesta.json() : null;
    const decision = this.resolver(ventaLocal, remoto.venta);

    if (decision.accion === "descartar_local") {
      await IndexedDB.abrir(); // limpieza logica del registro local
      PV.alerta("info", "La venta ya estaba registrada en el servidor");
    } else if (decision.accion === "usar_remoto") {
      PV.alerta("warning", "Los montos divergen: prevalece el registro del servidor");
    }
    return decision;
  },
};

