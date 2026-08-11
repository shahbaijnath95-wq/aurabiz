/**
 * AuraBiz Frontend — Simple Static File Server
 * Serves the pre-built Next.js static export
 */
const http = require("http");
const fs = require("fs");
const path = require("path");

const PORT = process.env.PORT || 3003;
const STATIC_DIR = path.join(__dirname, "out");

const MIME_TYPES = {
  ".html": "text/html",
  ".css": "text/css",
  ".js": "application/javascript",
  ".json": "application/json",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".gif": "image/gif",
  ".svg": "image/svg+xml",
  ".ico": "image/x-icon",
  ".woff": "font/woff",
  ".woff2": "font/woff2",
  ".ttf": "font/ttf",
  ".map": "application/json",
};

const server = http.createServer((req, res) => {
  let filePath = path.join(STATIC_DIR, req.url === "/" ? "index.html" : req.url);
  
  // Remove query string
  filePath = filePath.split("?")[0];
  
  // Check if file exists
  if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
    const ext = path.extname(filePath);
    const contentType = MIME_TYPES[ext] || "application/octet-stream";
    res.writeHead(200, { "Content-Type": contentType });
    fs.createReadStream(filePath).pipe(res);
  } else {
    // SPA fallback — serve index.html for all routes
    const indexPath = path.join(STATIC_DIR, "index.html");
    if (fs.existsSync(indexPath)) {
      res.writeHead(200, { "Content-Type": "text/html" });
      fs.createReadStream(indexPath).pipe(res);
    } else {
      res.writeHead(404);
      res.end("Not Found");
    }
  }
});

server.listen(PORT, "127.0.0.1", () => {
  console.log(`[AuraBiz Frontend] Running on http://127.0.0.1:${PORT}`);
});

process.on("SIGTERM", () => {
  server.close(() => process.exit(0));
});
