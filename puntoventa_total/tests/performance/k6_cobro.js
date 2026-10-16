// Nivel 3 - Performance: carga sobre el flujo de cobro del POS (k6).
//
// Requisitos: instalar k6 (https://k6.io/docs/get-started/installation/)
//   Windows:  choco install k6    |  winget install k6
//   macOS:    brew install k6     |  Linux: sudo apt install k6
//
// Ejecucion (con la app levantada: python manage.py runserver):
//   k6 run tests/performance/k6_cobro.js --env BASE_URL=http://127.0.0.1:8000
//
// El script hace el flujo autentico: login -> apertura de caja -> escaneo
// del producto -> cobro. Si el login falla, la prueba aborta con error claro.

import http from "k6/http";
import { check, sleep, fail } from "k6";
import { Trend, Rate } from "k6/metrics";

const BASE = __ENV.BASE_URL || "http://127.0.0.1:8000";
const USERNAME = __ENV.PMV_USERNAME || "cajero_perf";
const PASSWORD = __ENV.PMV_PASSWORD || "Secreta123";
const CODIGO = __ENV.PMV_CODIGO || "7751234567890";

// Presupuestos de negocio (docs/testing/test_strategy.md):
// cobro < 100 ms, busqueda de catalogo < 200 ms
const TIEMPO_COBRO_MS = new Trend("tiempo_cobro_ms", true);
const TIEMPO_BUSQUEDA_MS = new Trend("tiempo_busqueda_ms", true);
const TASA_ERRORES = new Rate("tasa_errores_negocio");

export const options = {
  scenarios: {
    punto_de_venta: {
      executor: "ramping-vus",
      startVUs: 1,
      stages: [
        { duration: "1m", target: 10 },
        { duration: "2m", target: 10 },
        { duration: "30s", target: 0 },
      ],
      gracefulRampDown: "30s",
    },
  },
  thresholds: {
    // Quality gate: 95% de cobros por debajo de 500 ms y sin errores HTTP
    http_req_duration: ["p(95)<500"],
    http_req_failed: ["rate==0"],
    tiempo_cobro_ms: ["p(95)<100"],
    tasa_errores_negocio: ["rate==0"],
  },
};

function csrfDe(respuesta) {
  const cookies = respuesta.cookies;
  return cookies && cookies.csrftoken ? cookies.csrftoken[0].value : "";
}

export function setup() {
  const paginaLogin = http.get(`${BASE}/`);
  const token = csrfDe(paginaLogin);

  const login = http.post(
    `${BASE}/login/`,
    { username: USERNAME, password: PASSWORD, csrfmiddlewaretoken: token },
    { headers: { Referer: BASE }, redirects: 0 }
  );

  if (login.status !== 302) {
    fail(
      `Login fallido (status ${login.status}). Crea el usuario primero: ` +
        `python scripts/crear_admin.py --username ${USERNAME} --password ${PASSWORD}`
    );
  }
  return { token: token };
}

export default function (setup) {
  const encabezados = { Referer: BASE, "X-CSRFToken": setup.token };

  // 1. apertura de caja (ignora "TurnoYaAbierto": el cajero ya tiene turno)
  http.post(
    `${BASE}/caja/apertura/`,
    { monto_apertura: "100.00", csrfmiddlewaretoken: setup.token },
    { headers: encabezados, redirects: 0 }
  );

  // 2. abrir el POS (crea/carga la venta en sesion)
  const pos = http.get(`${BASE}/pos/`);
  check(pos, { "POS responde 200": (r) => r.status === 200 });

  // 3. busqueda por codigo de barras (presupuesto < 200 ms)
  const tBusqueda = Date.now();
  const busqueda = http.get(`${BASE}/pos/buscar/?q=${CODIGO}`);
  TIEMPO_BUSQUEDA_MS.add(Date.now() - tBusqueda);
  const resultados = busqueda.json("resultados") || [];
  check(busqueda, {
    "encuentra el producto": () => resultados.length === 1,
    "busqueda < 200ms": () => Date.now() - tBusqueda < 200,
  });
  if (resultados.length !== 1) {
    TASA_ERRORES.add(1);
    sleep(1);
    return;
  }

  const ventaMatch = pos.body.match(/Ticket en curso:\s*([0-9a-f-]{36})/);
  if (!ventaMatch) {
    TASA_ERRORES.add(1);
    sleep(1);
    return;
  }
  const ventaId = ventaMatch[1];
  const productoId = resultados[0].id;

  // 4. agregar producto al carrito
  const agregar = http.post(
    `${BASE}/pos/venta/${ventaId}/agregar/${productoId}/`,
    { cantidad: "1", csrfmiddlewaretoken: setup.token },
    { headers: encabezados }
  );
  check(agregar, { "agrega producto": (r) => r.status === 200 });

  const total = agregar.json("total");
  if (typeof total !== "number") {
    TASA_ERRORES.add(1);
    sleep(1);
    return;
  }

  // 5. cobro en efectivo (presupuesto < 100 ms)
  const tCobro = Date.now();
  const cobro = http.post(
    `${BASE}/pos/venta/${ventaId}/pago/`,
    {
      metodo: "EFECTIVO",
      monto: total.toFixed(2),
      monto_entregado: "20.00",
      csrfmiddlewaretoken: setup.token,
    },
    { headers: encabezados }
  );
  TIEMPO_COBRO_MS.add(Date.now() - tCobro);

  const ok = check(cobro, {
    "el cobro redirige al ticket": (r) => r.status === 302 && r.headers.Location.includes("/ticket/"),
  });
  TASA_ERRORES.add(ok ? 0 : 1);

  sleep(1);
}
