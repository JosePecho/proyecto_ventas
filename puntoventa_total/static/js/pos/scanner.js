/* Lectura de escaner de codigo de barras: detecta secuencias rapidas + Enter */
const Scanner = {
  buffer: "",
  ultimoTiempo: 0,
  INTERVALO_MAXIMO_MS: 50, // entre teclas de un escaner fisico

  init(callback) {
    document.addEventListener("keydown", (evento) => {
      const ahora = Date.now();
      if (evento.key === "Enter" && this.buffer.length >= 8) {
        evento.preventDefault();
        callback(this.buffer);
        this.buffer = "";
        return;
      }
      if (ahora - this.ultimoTiempo > this.INTERVALO_MAXIMO_MS) {
        this.buffer = "";
      }
      if (evento.key.length === 1) {
        this.buffer += evento.key;
      }
      this.ultimoTiempo = ahora;
    });
  },
};

