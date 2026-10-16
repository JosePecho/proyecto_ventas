/* Utilidades globales */
const PV = {
  _cookie(nombre) {
    const coincidencia = document.cookie.match(new RegExp("(?:^|;\\s*)" + nombre + "=([^;]*)"));
    return coincidencia ? decodeURIComponent(coincidencia[1]) : undefined;
  },

  csrf(token) {
    // 1) token explicito, 2) campo oculto del form, 3) cookie csrftoken.
    // Sin la 3ra opcion el POS (que no tiene <form>) enviaba "undefined" y
    // todos los POST del carrito caian en 403.
    return token || document.querySelector("[name=csrfmiddlewaretoken]")?.value || this._cookie("csrftoken");
  },

  async post(url, data = {}, token) {
    const cuerpo = new FormData();
    Object.entries(data).forEach(([k, v]) => cuerpo.append(k, v));
    const tokenCsrf = this.csrf(token);
    cuerpo.append("csrfmiddlewaretoken", tokenCsrf);
    const respuesta = await fetch(url, {
      method: "POST",
      body: cuerpo,
      headers: { "X-CSRFToken": tokenCsrf || "" },
    });
    if (!respuesta.ok) throw new Error("Error " + respuesta.status);
    return respuesta.json();
  },

  money(valor) {
    return "S/ " + Number(valor || 0).toFixed(2);
  },

  alerta(tipo, mensaje) {
    const cont = document.createElement("div");
    cont.className = `alert alert-${tipo} alert-dismissible fade show py-2`;
    cont.innerHTML = `${mensaje}<button type="button" class="btn-close" data-bs-dismiss="alert"></button>`;
    const main = document.querySelector("main");
    main.prepend(cont);
    setTimeout(() => cont.remove(), 5000);
  },
};

// Registro del service worker (PWA / modo offline)
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/static/js/offline/service_worker.js").catch(() => {});
  });
}

