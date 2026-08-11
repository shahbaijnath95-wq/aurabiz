const http = require("http");
const fs = require("fs");
const path = require("path");

// Landing page runs on 3003 (does not collide with the Next.js frontend on 3001).
// Auth/dashboard routes redirect to the real frontend on 3001.
const PORT = 3003;

const server = http.createServer((req, res) => {
  // Serve the landing page
  if (req.url === "/" || req.url === "/index.html") {
    const html = `<!DOCTYPE html>
<html lang="hi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AuraBiz - AI WhatsApp Business Assistant</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',system-ui,sans-serif;background:linear-gradient(135deg,#fffbeb,#fff7ed);color:#1a1a1a;min-height:100vh}
.nav{max-width:1200px;margin:0 auto;padding:1.2rem 2rem;display:flex;align-items:center;justify-content:space-between}
.logo{font-size:1.5rem;font-weight:800}.logo span{color:#e67a00}
.nav-links{display:flex;gap:2rem;align-items:center}
.nav-links a{color:#5e564a;text-decoration:none;font-weight:500;font-size:0.9rem;transition:color 0.2s}
.nav-links a:hover{color:#e67a00}
.btn{background:linear-gradient(135deg,#ffb24d,#e67a00);color:#fff;padding:0.6rem 1.5rem;border-radius:0.75rem;font-weight:600;text-decoration:none;font-size:0.9rem;box-shadow:0 4px 12px rgba(230,122,0,0.2);transition:transform 0.2s}
.btn:hover{transform:translateY(-1px)}
.btn-ghost{background:transparent;color:#3a342b;border:1px solid #e8e2d9;padding:0.6rem 1.5rem;border-radius:0.75rem;font-weight:600;text-decoration:none;font-size:0.9rem}
.hero{max-width:1200px;margin:0 auto;padding:4rem 2rem;text-align:center}
.badge{display:inline-flex;align-items:center;gap:0.5rem;background:#fff;border:1px solid #fef3c7;border-radius:9999px;padding:0.4rem 1rem;font-size:0.85rem;margin-bottom:2rem;box-shadow:0 2px 8px rgba(0,0,0,0.04)}
.badge span{width:8px;height:8px;background:#10b981;border-radius:50%;animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:0.5}}
h1{font-size:3.5rem;font-weight:800;line-height:1.1;margin-bottom:1.5rem;letter-spacing:-0.02em}
h1 .gradient{background:linear-gradient(135deg,#ffb24d,#e67a00);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.subtitle{font-size:1.2rem;color:#5e564a;max-width:600px;margin:0 auto 2.5rem;line-height:1.7}
.cta{display:flex;gap:1rem;justify-content:center;flex-wrap:wrap}
.btn-lg{padding:1rem 2.5rem;font-size:1.1rem;border-radius:1rem}
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:2rem;max-width:600px;margin:3rem auto 0}
.stat{padding:1.5rem;background:#fff;border-radius:1.25rem;border:1px solid #fef3c7;box-shadow:0 4px 12px rgba(0,0,0,0.04)}
.stat .value{font-size:2rem;font-weight:800}
.stat .label{color:#8b8275;font-size:0.85rem;margin-top:0.25rem}
.phone{position:relative;max-width:380px;margin:3rem auto 0;border-radius:2.5rem;border:8px solid #1a1a1e;background:#fff;box-shadow:0 25px 50px -12px rgba(0,0,0,0.15);overflow:hidden;min-height:500px}
.phone-header{background:#075e54;padding:1rem;display:flex;align-items:center;gap:0.75rem}
.phone-header .avatar{width:36px;height:36px;border-radius:50%;background:rgba(255,255,255,0.2);display:flex;align-items:center;justify-content:center}
.phone-header .name{color:#fff;font-weight:600;font-size:0.9rem}
.phone-header .status{color:#a8e6c9;font-size:0.7rem}
.chat{padding:1rem;min-height:350px;background:#ece5dd;display:flex;flex-direction:column;gap:0.5rem}
.msg{max-width:80%;padding:0.6rem 1rem;border-radius:1rem;font-size:0.85rem}
.msg.in{background:#fff;align-self:flex-start;border-bottom-left-radius:0.25rem}
.msg.out{background:#dcf8c6;align-self:flex-end;border-bottom-right-radius:0.25rem}
.msg .time{font-size:0.6rem;color:#8b8275;text-align:right;margin-top:0.25rem}
.footer{text-align:center;padding:3rem 2rem;color:#8b8275;font-size:0.85rem}
@media(max-width:768px){h1{font-size:2.5rem}.stats{grid-template-columns:1fr}}
</style>
</head>
<body>
<nav class="nav">
  <div class="logo">Aura<span>Biz</span></div>
  <div class="nav-links">
    <a href="#features">Features</a>
    <a href="#pricing">Pricing</a>
    <a href="/login">Login</a>
    <a href="/register" class="btn">Free Trial →</a>
  </div>
</nav>

<section class="hero">
  <div class="badge"><span></span> 500+ businesses already using</div>
  <h1>Aapka WhatsApp,<br><span class="gradient">ab AI Salesman</span></h1>
  <p class="subtitle">Customers ko Hinglish mein smart jawab do — billing, inventory, orders sab automate ho jayega. Seedha WhatsApp se apna business chalao.</p>
  <div class="cta">
    <a href="/register" class="btn btn-lg">Start Free Trial →</a>
    <a href="#features" class="btn-ghost btn-lg">See Features</a>
  </div>

  <div class="stats">
    <div class="stat"><div class="value">50K+</div><div class="label">Messages/day</div></div>
    <div class="stat"><div class="value">4.9★</div><div class="label">Customer Rating</div></div>
    <div class="stat"><div class="value">2 min</div><div class="label">Setup Time</div></div>
  </div>

  <div class="phone">
    <div class="phone-header">
      <div class="avatar">🤖</div>
      <div><div class="name">AuraBiz Assistant</div><div class="status">● online</div></div>
    </div>
    <div class="chat">
      <div class="msg in">Hi! Aapke paas red kurta hai kya? 🛍️<div class="time">10:41 AM</div></div>
      <div class="msg out">Haan ji! Red Silk Kurta size M — ₹1,299, stock mein 12 hain. Book karun? 😊<div class="time">10:41 AM</div></div>
      <div class="msg in">Haan, 1 order karo!<div class="time">10:42 AM</div></div>
      <div class="msg out">Done! ✅ Order #4821 confirm. Payment link bhej raha hoon 👇<div class="time">10:42 AM</div></div>
    </div>
  </div>
</section>

<div class="footer">© 2026 AuraBiz. Made with ❤️ for Indian businesses 🇮🇳</div>

<script>
// Redirect to dashboard app for auth pages
if(window.location.pathname.startsWith('/login')||window.location.pathname.startsWith('/register')||window.location.pathname.startsWith('/dashboard')||window.location.pathname.startsWith('/setup')){
  window.location.href='http://localhost:3001'+window.location.pathname;
}
</script>
</body>
</html>`;
    res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
    res.end(html);
  } else {
    // Redirect all other routes to the dashboard app (3001)
    res.writeHead(302, { "Location": `http://localhost:3001${req.url}` });
    res.end();
  }
});

server.listen(PORT, () => {
  console.log(`Landing page server running on http://localhost:${PORT}`);
});