import http from 'k6/http';
import { check } from 'k6';
export const options = {
  scenarios: { roles: { executor: 'per-vu-iterations', vus: 2, iterations: 3, maxDuration: '30s' } },
  thresholds: { checks: ['rate==1'], http_req_failed: ['rate==0'], http_req_duration: ['p(95)<500'] },
};
const sesiones = JSON.parse(__ENV.QA_REPORTES_SESIONES);
export default function () {
  const sesion = sesiones[__VU - 1];
  for (const ruta of ['/reportes/ventas/', '/reportes/utilidad/']) {
    const r = http.get(__ENV.BASE_URL + ruta, {headers: {Cookie: sesion.cookie}, redirects: 0,
      responseCallback: http.expectedStatuses(200, 302)});
    check(r, {'acceso y datos según rol': r => sesion.admin ? r.status === 200 && r.body.includes('37') :
      r.status === 302 && r.headers.Location.endsWith('/catalogo/') && !r.body.includes('Total gastado')});
  }
}
