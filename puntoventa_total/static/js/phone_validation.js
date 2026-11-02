/* Celulares peruanos: validar sin recortar ni enviar un numero incorrecto. */
(() => {
  const selector = "input[data-phone-peru]";
  const dialogo = document.getElementById("phone-warning");
  let campoPendiente = null;

  function errorTelefono(campo, valor = campo.value) {
    if (!valor) return campo.required ? "Ingresa tu teléfono: debe tener exactamente 9 dígitos." : "";
    if (!/^[0-9]+$/.test(valor)) {
      return "El teléfono solo debe contener números, sin espacios, guiones ni +51. Ejemplo: 987654321.";
    }
    if (valor.length !== 9) {
      const diferencia = Math.abs(9 - valor.length);
      const verbo = valor.length < 9 ? "Falta" : "Sobra";
      const detalle = `${verbo}${diferencia === 1 ? "" : "n"} ${diferencia}`;
      return `El teléfono debe tener exactamente 9 dígitos. Ingresaste ${valor.length}. ${detalle}. Ejemplo: 987654321.`;
    }
    if (!valor.startsWith("9")) return "El celular peruano debe comenzar con 9. Ejemplo: 987654321.";
    return "";
  }

  function validar(campo) {
    const mensaje = errorTelefono(campo);
    campo.setCustomValidity(mensaje);
    if (mensaje) campo.setAttribute("aria-invalid", "true");
    else campo.removeAttribute("aria-invalid");
    return mensaje;
  }

  function advertir(campo, mensaje) {
    campoPendiente = campo;
    if (!dialogo) {
      window.alert(mensaje);
      campo.focus();
      return;
    }
    document.getElementById("phone-warning-message").textContent = mensaje;
    if (!dialogo.open) dialogo.showModal();
  }

  dialogo?.addEventListener("close", () => campoPendiente?.focus());
  document.querySelectorAll(selector).forEach(validar);
  document.addEventListener("reset", (evento) => {
    queueMicrotask(() => evento.target.querySelectorAll(selector).forEach(validar));
  });

  document.addEventListener("input", (evento) => {
    if (evento.target.matches(selector)) validar(evento.target);
  });

  // La validacion nativa ocurre antes de submit; invalid requiere captura.
  document.addEventListener("invalid", (evento) => {
    const campo = evento.target;
    if (!campo.matches(selector)) return;
    const mensaje = validar(campo);
    if (mensaje) {
      evento.preventDefault();
      advertir(campo, mensaje);
    }
  }, true);

  document.addEventListener("submit", (evento) => {
    for (const campo of evento.target.querySelectorAll(selector)) {
      if (!campo.willValidate) continue;
      const mensaje = validar(campo);
      if (mensaje) {
        evento.preventDefault();
        evento.stopImmediatePropagation();
        advertir(campo, mensaje);
        break;
      }
    }
  }, true);

  function comprobarInsercion(evento, texto) {
    const campo = evento.target;
    if (!campo.matches(selector) || !texto) return;
    const inicio = campo.selectionStart ?? campo.value.length;
    const fin = campo.selectionEnd ?? inicio;
    const propuesto = campo.value.slice(0, inicio) + texto + campo.value.slice(fin);
    // maxlength recorta silenciosamente: avisar antes y conservar el valor anterior.
    if (propuesto.length > 9) {
      evento.preventDefault();
      advertir(campo, errorTelefono(campo, propuesto));
    }
  }

  document.addEventListener("beforeinput", (evento) => {
    if (evento.inputType?.startsWith("insert")) comprobarInsercion(evento, evento.data);
  });
  document.addEventListener("paste", (evento) => {
    comprobarInsercion(evento, evento.clipboardData?.getData("text"));
  });
})();
