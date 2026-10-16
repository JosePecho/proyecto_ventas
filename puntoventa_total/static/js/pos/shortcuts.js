/* Atajos de teclado del cajero */
const Shortcuts = {
  init(pos) {
    document.addEventListener("keydown", (evento) => {
      if (!evento.altKey) return;
      switch (evento.key) {
        case "F2": // enfocar buscador
          evento.preventDefault();
          document.getElementById("buscador-pos")?.focus();
          break;
        case "F8": // cobrar
          evento.preventDefault();
          document.getElementById("btn-cobrar")?.click();
          break;
        case "Escape": // limpiar busqueda
          evento.preventDefault();
          document.getElementById("buscador-pos").value = "";
          document.getElementById("resultados-busqueda").innerHTML = "";
          break;
      }
    });
  },
};

