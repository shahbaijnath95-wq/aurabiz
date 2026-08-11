/**
 * AuraBiz Tenant App — Port 3004
 * Proxies all requests to frontend (3003) EXCEPT "/" which redirects to /login
 * Desktop app loads this port — tenants ko landing page nahi dikhta
 */
const http = require("http");
const PORT = 3004;
const UPSTREAM = "http://localhost:3003";

const server = http.createServer((req, res) => {
  const url = new URL(req.url, UPSTREAM);

  // Block landing page — redirect to login
  if (url.pathname === "/" || url.pathname === "") {
    res.writeHead(302, { Location: "/login" });
    res.end();
    return;
  }

  // Proxy everything else to frontend
  const proxyReq = http.request(
    {
      hostname: "localhost",
      port: 3003,
      path: req.url,
      method: req.method,
      headers: { ...req.headers, host: "localhost:3003" },
    },
    (proxyRes) => {
      res.writeHead(proxyRes.statusCode, proxyRes.headers);
      proxyRes.pipe(res);
    }
  );

  proxyReq.on("error", (e) => {
    res.writeHead(502, { "Content-Type": "text/plain" });
    res.end("Frontend (3003) is down: " + e.message);
  });

  req.pipe(proxyReq);
});

server.listen(PORT, () => {
  console.log(`Tenant App running at http://localhost:${PORT}`);
  console.log(`Landing page blocked — / redirects to /login`);
  console.log(`All other requests proxied to ${UPSTREAM}`);
});
