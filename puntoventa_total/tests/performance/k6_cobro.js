// Solo QA. Crear un cajero por VU: PMV_USERNAME_PREFIX1, PREFIX2, etc.
// Sembrar producto con stock >= VUS*ITERATIONS. No reutilizar usuarios productivos.
// k6 run -e BASE_URL=http://127.0.0.1:8000 -e PMV_USERNAME_PREFIX=qa_cajero_ \
//   -e PMV_PASSWORD=... -e PMV_CODIGO=7751234567890 tests/performance/k6_cobro.js
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend, Rate } from 'k6/metrics';

const BASE = (__ENV.BASE_URL || '').replace(/\/$/, '');
const TIEMPO_COBRO = new Trend('tiempo_cobro_ms', true);
const TIEMPO_BUSQUEDA = new Trend('tiempo_busqueda_ms', true);
const ERRORES = new Rate('tasa_errores_negocio');
let sesionPreparada = false; // El runtime JS y el cookie jar son propios de cada VU.

export const options = {
  noCookiesReset: true,
  scenarios: {
    punto_de_venta: {
      executor: 'per-vu-iterations', vus: Number(__ENV.VUS || 2),
      iterations: Number(__ENV.ITERATIONS || 5), maxDuration: '2m',
    },
  },
  thresholds: {
    checks: ['rate==1'], http_req_failed: ['rate==0'], http_req_duration: ['p(95)<500'],
    tiempo_cobro_ms: ['p(95)<100'], tiempo_busqueda_ms: ['p(95)<200'],
    tasa_errores_negocio: ['rate==0'],
  },
};

function token() {
  const values = http.cookieJar().cookiesForURL(`${BASE}/`).csrftoken;
  if (!values || !values.length) throw new Error('No se recibio cookie CSRF');
  return values[0];
}

function post(path, data) {
  // Django rota el token al iniciar sesion: leer siempre la cookie actual del VU.
  const csrf = token();
  return http.post(`${BASE}${path}`, { ...data, csrfmiddlewaretoken: csrf }, {
    headers: { Referer: `${BASE}/`, 'X-CSRFToken': csrf }, redirects: 0,
  });
}

function exigir(response, nombre, assertion) {
  if (!check(response, { [nombre]: assertion })) throw new Error(nombre);
}

export default function () {
  let ok = false;
  try {
    if (!BASE || !__ENV.PMV_USERNAME_PREFIX || !__ENV.PMV_PASSWORD || !__ENV.PMV_CODIGO) {
      throw new Error('Defina BASE_URL, PMV_USERNAME_PREFIX, PMV_PASSWORD y PMV_CODIGO de QA');
    }
    if (!sesionPreparada) {
      http.cookieJar().clear(`${BASE}/`);
      const loginPage = http.get(`${BASE}/login/`, { redirects: 0 });
      exigir(loginPage, 'formulario login', (r) => r.status === 200);
      const login = post('/login/', {
        username: `${__ENV.PMV_USERNAME_PREFIX}${__VU}`, password: __ENV.PMV_PASSWORD,
      });
      exigir(login, 'login aceptado', (r) => r.status === 302 && r.headers.Location === '/catalogo/');
      const apertura = post('/caja/apertura/', { monto_apertura: '100.00' });
      exigir(apertura, 'caja abierta', (r) => r.status === 302 && r.headers.Location === '/pos/');
      sesionPreparada = true;
    }
    const pos = http.get(`${BASE}/pos/`, { redirects: 0 });
    exigir(pos, 'POS autenticado', (r) => r.status === 200 && r.body.includes('Ticket en curso:'));
    const match = pos.body.match(/Ticket en curso:\s*([0-9a-f-]{36})/);
    if (!match) throw new Error('El POS no contiene venta activa');
    const ventaId = match[1];
    const busqueda = http.get(`${BASE}/pos/buscar/?q=${encodeURIComponent(__ENV.PMV_CODIGO)}`, { redirects: 0 });
    TIEMPO_BUSQUEDA.add(busqueda.timings.duration);
    exigir(busqueda, 'busqueda correcta', (r) => r.status === 200);
    const productos = busqueda.json('resultados');
    if (!Array.isArray(productos) || productos.length !== 1) throw new Error('Producto QA no encontrado');
    const agregar = post(`/pos/venta/${ventaId}/agregar/${productos[0].id}/`, { cantidad: '1' });
    exigir(agregar, 'producto agregado', (r) => r.status === 200);
    const total = agregar.json('total');
    if (typeof total !== 'number' || !Number.isFinite(total) || total <= 0) throw new Error('Total invalido');
    const cobro = post(`/pos/venta/${ventaId}/pago/`, {
      metodo: 'EFECTIVO', monto: total.toFixed(2), monto_entregado: total.toFixed(2),
    });
    TIEMPO_COBRO.add(cobro.timings.duration);
    exigir(cobro, 'cobro redirige al ticket', (r) =>
      r.status === 302 && r.headers.Location === `/pos/venta/${ventaId}/ticket/`);
    const ticket = http.get(`${BASE}${cobro.headers.Location}`, { redirects: 0 });
    exigir(ticket, 'ticket PDF emitido', (r) =>
      r.status === 200 && r.headers['Content-Type'].includes('application/pdf') && r.body.startsWith('%PDF'));
    ok = true;
  } finally {
    ERRORES.add(ok ? 0 : 1);
    sleep(0.5);
  }
}
