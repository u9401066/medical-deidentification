#!/usr/bin/env node
/**
 * Production frontend server with same-origin API proxy.
 *
 * The browser always calls /api on the frontend origin. This server proxies
 * those requests to the FastAPI backend, avoiding LAN IP/CORS/SameSite traps.
 */

import { createReadStream, existsSync, statSync } from 'node:fs';
import { createServer, request as proxyRequest } from 'node:http';
import { extname, join, normalize, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = fileURLToPath(new URL('.', import.meta.url));
const projectRoot = resolve(__dirname, '../..');
const defaultDistDir = join(projectRoot, 'web/frontend/dist');

const port = Number(process.env.MEDICAL_DEID_FRONTEND_PORT || 5173);
const host = process.env.MEDICAL_DEID_FRONTEND_HOST || '0.0.0.0';
const backendUrl = new URL(process.env.MEDICAL_DEID_FRONTEND_BACKEND_URL || 'http://127.0.0.1:8000');
const distDir = resolve(process.env.MEDICAL_DEID_FRONTEND_DIST || defaultDistDir);

const mimeTypes = {
  '.css': 'text/css; charset=utf-8',
  '.gif': 'image/gif',
  '.html': 'text/html; charset=utf-8',
  '.ico': 'image/x-icon',
  '.jpeg': 'image/jpeg',
  '.jpg': 'image/jpeg',
  '.js': 'application/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.svg': 'image/svg+xml',
  '.txt': 'text/plain; charset=utf-8',
  '.webp': 'image/webp',
};
const unsafeMethods = new Set(['POST', 'PUT', 'PATCH', 'DELETE']);

function send(res, statusCode, body, headers = {}) {
  res.writeHead(statusCode, headers);
  res.end(body);
}

function headerValue(value) {
  return Array.isArray(value) ? value[0] : value;
}

function frontendOrigin(req) {
  const forwardedProto = headerValue(req.headers['x-forwarded-proto']);
  const proto = forwardedProto || (req.socket.encrypted ? 'https' : 'http');
  const hostHeader = headerValue(req.headers.host) || `${host}:${port}`;
  return `${proto}://${hostHeader}`;
}

function requestOrigin(value) {
  if (!value || value === 'null') {
    return null;
  }
  try {
    const parsed = new URL(value);
    return `${parsed.protocol}//${parsed.host}`;
  } catch {
    return null;
  }
}

function validateBrowserOrigin(req, res) {
  const secFetchSite = headerValue(req.headers['sec-fetch-site']);
  if (secFetchSite === 'cross-site') {
    send(res, 403, JSON.stringify({ detail: 'Cross-site API request blocked' }), {
      'Content-Type': 'application/json; charset=utf-8',
    });
    return false;
  }

  if (!unsafeMethods.has((req.method || 'GET').toUpperCase())) {
    return true;
  }

  const expectedOrigin = frontendOrigin(req);
  const origin = requestOrigin(headerValue(req.headers.origin));
  const referer = requestOrigin(headerValue(req.headers.referer));
  const browserOrigin = origin || referer;

  if (browserOrigin && browserOrigin !== expectedOrigin) {
    send(res, 403, JSON.stringify({ detail: 'Invalid request origin' }), {
      'Content-Type': 'application/json; charset=utf-8',
    });
    return false;
  }

  return true;
}

function staticPathFor(urlPath) {
  let decodedPath = '/';
  try {
    decodedPath = decodeURIComponent(urlPath.split('?')[0] || '/');
  } catch {
    return null;
  }
  const safePath = normalize(decodedPath).replace(/^(\.\.(\/|\\|$))+/, '');
  let candidate = resolve(distDir, `.${safePath}`);

  if (!candidate.startsWith(distDir)) {
    candidate = join(distDir, 'index.html');
  }

  if (existsSync(candidate) && statSync(candidate).isDirectory()) {
    candidate = join(candidate, 'index.html');
  }

  if (!existsSync(candidate)) {
    candidate = join(distDir, 'index.html');
  }

  return candidate;
}

function serveStatic(req, res) {
  const filePath = staticPathFor(req.url || '/');
  if (!filePath) {
    send(res, 400, 'Bad request');
    return;
  }
  const ext = extname(filePath);
  const contentType = mimeTypes[ext] || 'application/octet-stream';
  const cacheControl = filePath.includes('/assets/')
    ? 'public, max-age=31536000, immutable'
    : 'no-cache';

  res.writeHead(200, {
    'Content-Type': contentType,
    'Cache-Control': cacheControl,
  });
  createReadStream(filePath).pipe(res);
}

function proxyApi(req, res) {
  if (!validateBrowserOrigin(req, res)) {
    return;
  }

  const target = new URL(req.url || '/', backendUrl);
  const headers = { ...req.headers };

  delete headers.host;
  delete headers.origin;
  delete headers.referer;
  delete headers.connection;
  delete headers['keep-alive'];
  delete headers['proxy-authenticate'];
  delete headers['proxy-authorization'];
  delete headers.te;
  delete headers.trailer;
  delete headers['transfer-encoding'];
  delete headers.upgrade;

  headers.host = backendUrl.host;
  headers['x-forwarded-host'] = req.headers.host || '';
  headers['x-forwarded-proto'] = headerValue(req.headers['x-forwarded-proto']) || (req.socket.encrypted ? 'https' : 'http');
  headers['x-forwarded-for'] = req.socket.remoteAddress || '';
  headers['x-medical-deid-frontend-proxy'] = '1';

  const upstream = proxyRequest(
    {
      protocol: backendUrl.protocol,
      hostname: backendUrl.hostname,
      port: backendUrl.port || (backendUrl.protocol === 'https:' ? 443 : 80),
      method: req.method,
      path: `${target.pathname}${target.search}`,
      headers,
    },
    (upstreamRes) => {
      const responseHeaders = { ...upstreamRes.headers };
      delete responseHeaders['transfer-encoding'];
      res.writeHead(upstreamRes.statusCode || 502, responseHeaders);
      upstreamRes.pipe(res);
    }
  );

  upstream.on('error', (error) => {
    send(
      res,
      502,
      JSON.stringify({
        detail: `Backend proxy failed: ${error.message}`,
      }),
      { 'Content-Type': 'application/json; charset=utf-8' }
    );
  });

  req.pipe(upstream);
}

const server = createServer((req, res) => {
  if (!existsSync(distDir)) {
    send(res, 500, `Frontend dist directory not found: ${distDir}`);
    return;
  }

  if ((req.url || '') === '/api' || (req.url || '').startsWith('/api/')) {
    proxyApi(req, res);
    return;
  }

  serveStatic(req, res);
});

server.listen(port, host, () => {
  console.log(`Frontend listening on http://${host}:${port}`);
  console.log(`Proxying /api to ${backendUrl.origin}`);
  console.log(`Serving static files from ${distDir}`);
});
