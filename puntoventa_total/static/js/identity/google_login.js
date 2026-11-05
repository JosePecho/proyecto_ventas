(async () => {
const button = document.getElementById("google-login");
const errorBox = document.getElementById("google-login-error");
const errors = {
  "auth/popup-closed-by-user": "Se canceló el acceso con Google.",
  "auth/cancelled-popup-request": "Ya hay una ventana de Google abierta.",
  "auth/popup-blocked": "Permite las ventanas emergentes para acceder con Google.",
  "auth/unauthorized-domain": "Este dominio no está autorizado en Firebase. Contacta al administrador.",
  "auth/network-request-failed": "No se pudo conectar con Google. Comprueba tu conexión.",
};

try {
  const [{ initializeApp }, { getAuth, GoogleAuthProvider, signInWithPopup,
    setPersistence, inMemoryPersistence, signOut }] = await Promise.all([
    import("https://www.gstatic.com/firebasejs/13.2.0/firebase-app.js"),
    import("https://www.gstatic.com/firebasejs/13.2.0/firebase-auth.js"),
  ]);
  const config = JSON.parse(document.getElementById("firebase-config").textContent);
  const auth = getAuth(initializeApp(config));
  await setPersistence(auth, inMemoryPersistence);
  const provider = new GoogleAuthProvider();
  provider.setCustomParameters({ prompt: "select_account" });
  button.disabled = false;
  button.addEventListener("click", async () => {
    button.disabled = true;
    errorBox.textContent = "";
    let destination;
    try {
      const result = await signInWithPopup(auth, provider);
      const token = await result.user.getIdToken();
      const csrf = document.querySelector("input[name=csrfmiddlewaretoken]").value;
      const response = await fetch(button.dataset.endpoint, {
        method: "POST", credentials: "same-origin", cache: "no-store",
        headers: { "Content-Type": "application/json", "X-CSRFToken": csrf },
        body: JSON.stringify({ id_token: token, next: new URLSearchParams(location.search).get("next") || "" }),
      });
      const data = await response.json();
      if (!response.ok) {
        errorBox.textContent = data.error || "No se pudo iniciar sesión con Google.";
      } else {
        destination = new URL(data.redirect, location.origin);
        if (destination.origin !== location.origin) throw new Error("Invalid destination");
      }
    } catch (error) {
      errorBox.textContent = errors[error.code] || "No se pudo iniciar sesión con Google. Usa tu acceso tradicional.";
    } finally {
      try { await signOut(auth); } catch { /* La identidad solo persiste en memoria. */ }
      button.disabled = false;
    }
    if (destination) location.assign(destination.href);
  });
} catch {
  errorBox.textContent = "Google no está disponible. Puedes iniciar sesión con usuario y contraseña.";
}
})();
