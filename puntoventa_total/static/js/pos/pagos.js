/* Calculo de vuelto y validacion del formulario de cobro */
(function () {
  const monto = document.querySelector("[name=monto]");
  const entregado = document.querySelector("[name=monto_entregado]");
  const metodo = document.querySelector("[name=metodo]");

  function recalcularVuelto() {
    let cont = document.getElementById("vuelto-calculado");
    if (!cont) {
      cont = document.createElement("div");
      cont.id = "vuelto-calculado";
      cont.className = "alert alert-success mt-2 fw-bold";
      entregado?.closest(".mb-3")?.appendChild(cont);
    }
    const diferencia = Number(entregado.value) - Number(monto.value);
    cont.textContent = diferencia >= 0 ? `Vuelto: ${PV.money(diferencia)}` : "";
    cont.style.display = diferencia >= 0 ? "block" : "none";
  }

  metodo?.addEventListener("change", () => {
    const esEfectivo = metodo.value === "EFECTIVO";
    if (entregado) {
      entregado.disabled = !esEfectivo;
      entregado.closest(".mb-3").style.display = esEfectivo ? "block" : "none";
    }
  });

  entregado?.addEventListener("input", recalcularVuelto);
  monto?.addEventListener("input", recalcularVuelto);
})();

