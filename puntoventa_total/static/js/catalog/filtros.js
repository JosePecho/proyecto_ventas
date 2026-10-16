/* Filtro por categoria sin recarga completa */
(function () {
  document.querySelectorAll("a[data-categoria]").forEach((enlace) => {
    enlace.addEventListener("click", (evento) => {
      evento.preventDefault();
      const url = new URL(window.location.href);
      url.searchParams.set("categoria", enlace.dataset.categoria);
      url.searchParams.delete("pagina");
      window.location.href = url.toString();
    });
  });
})();

