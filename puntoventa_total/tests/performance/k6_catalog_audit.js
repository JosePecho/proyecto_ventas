// Carga de lectura: apuntar solo a un despliegue QA con catalogo sembrado.
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  vus: 5,
  duration: '20s',
  thresholds: {
    http_req_failed: ['rate==0'],
    checks: ['rate==1'],
    http_req_duration: ['p(95)<500'],
  },
};

export default function () {
  const base = __ENV.BASE_URL;
  if (!base) throw new Error('Defina BASE_URL de un entorno QA');
  const response = http.get(`${base}/catalogo/`);
  check(response, {
    'catalogo publico HTTP 200': (r) => r.status === 200,
    'pagina de catalogo, sin login': (r) => r.body.includes('producto') && !r.body.includes('name="password"'),
  });
  sleep(0.5);
}
