import http from 'k6/http';
import { check } from 'k6';

export const options = {
  scenarios: { clientes: { executor: 'per-vu-iterations', vus: 2, iterations: 5, maxDuration: '30s' } },
  thresholds: { checks: ['rate==1'], http_req_failed: ['rate==0'], http_req_duration: ['p(95)<500'] },
};

const clientes = JSON.parse(__ENV.QA_PEDIDOS_CLIENTES);
const expected = http.expectedStatuses(200, 404);

export default function () {
  const propio = clientes[__VU - 1];
  const otro = clientes[__VU % 2];
  const params = { headers: { Cookie: propio.cookie }, redirects: 0, responseCallback: expected };
  const detalle = http.get(__ENV.BASE_URL + propio.ruta, params);
  check(detalle, {
    'cliente ve su pedido Pendiente': r => r.status === 200 && r.body.includes(propio.numero) && r.body.includes('Pendiente'),
  });
  const ajeno = http.get(__ENV.BASE_URL + otro.ruta, params);
  check(ajeno, { 'pedido ajeno protegido': r => r.status === 404 && !r.body.includes(otro.numero) });
}
