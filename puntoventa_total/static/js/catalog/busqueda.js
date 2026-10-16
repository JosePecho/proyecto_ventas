/* Busqueda del catalogo con debounce */
(function () {
  const formulario = document.getElementById("form-busqueda");
  const entrada = formulario?.querySelector("input[name=q]");
  let temporizador = null;

  entrada?.addEventListener("input", () => {
    clearTimeout(temporizador);
    temporizador = setTimeout(() => formulario.submit(), 500);
  });
})();

