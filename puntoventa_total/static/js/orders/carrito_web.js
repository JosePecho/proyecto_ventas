/* Carrito web: cantidades y confirmacion de pedido */
(function () {
  document.querySelectorAll("form[data-cantidad]").forEach((formulario) => {
    const entrada = formulario.querySelector("input[name=cantidad]");
    formulario.querySelector(".btn-mas")?.addEventListener("click", () => {
      entrada.value = Number(entrada.value) + 1;
    });
    formulario.querySelector(".btn-menos")?.addEventListener("click", () => {
      if (Number(entrada.value) > 1) entrada.value = Number(entrada.value) - 1;
    });
  });

  document.getElementById("form-checkout")?.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    const boton = evento.target.querySelector("button[type=submit]");
    boton.disabled = true;
    boton.textContent = "Confirmando...";
    evento.target.submit();
  });
})();

