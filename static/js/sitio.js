/* CreeHaSer Web · interacciones del portal
   - Decoración navideña por fechas (luces, nieve, adornos, Nacimiento, bienvenida)
   - Menú de secciones con resaltado, menú móvil, botón volver arriba
   - Animaciones de aparición, carruseles y árbol de la portada */
(function () {
  "use strict";
  const $ = (s, el) => (el || document).querySelector(s);
  const $$ = (s, el) => Array.from((el || document).querySelectorAll(s));
  const reduceMotion = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const body = document.body;

  /* ---------- Temporada navideña ---------- */
  function enRango(d, desde, hasta) {
    const p = v => { const [dd, mm] = String(v || "").split("/").map(Number); return (mm || 0) * 100 + (dd || 0); };
    const x = (d.getMonth() + 1) * 100 + d.getDate(), a = p(desde), b = p(hasta);
    return a <= b ? x >= a && x <= b : x >= a || x <= b;
  }
  function esNavidad() {
    const m = body.dataset.deco || "auto";
    if (m === "on") return true;
    if (m === "off") return false;
    return enRango(new Date(), body.dataset.decoDesde || "01/11", body.dataset.decoHasta || "06/01");
  }
  const navidad = esNavidad();
  body.classList.toggle("xmas", navidad);

  /* ---------- Nieve ---------- */
  function nieve(canvas, cantidad, color) {
    if (!canvas || reduceMotion) return null;
    const ctx = canvas.getContext("2d"); let W, H, raf, activo = true;
    const dpr = window.devicePixelRatio || 1;
    const medir = () => { const r = canvas.getBoundingClientRect(); W = canvas.width = r.width * dpr; H = canvas.height = r.height * dpr; };
    medir(); addEventListener("resize", medir);
    const copos = Array.from({ length: cantidad }, () => ({ x: Math.random(), y: Math.random(), r: 1 + Math.random() * 2.6, v: .25 + Math.random() * .6, d: Math.random() * 6 }));
    const paso = t => {
      if (!activo) return;
      ctx.clearRect(0, 0, W, H); ctx.fillStyle = color;
      for (const f of copos) {
        f.y += f.v / H * dpr * 2.2; if (f.y > 1.02) { f.y = -.02; f.x = Math.random(); }
        const x = (f.x + Math.sin(t / 1800 + f.d) * .012) * W, y = f.y * H;
        ctx.globalAlpha = .55 + f.r / 8; ctx.beginPath(); ctx.arc(x, y, f.r * dpr, 0, 7); ctx.fill();
      }
      raf = requestAnimationFrame(paso);
    };
    raf = requestAnimationFrame(paso);
    return { parar() { activo = false; cancelAnimationFrame(raf); } };
  }

  /* ---------- Luces bajo la cabecera ---------- */
  function dibujarLuces() {
    const caja = $("#xLights"); if (!caja || !navidad) return;
    const w = Math.max(caja.clientWidth, 320), paso = 46, n = Math.ceil(w / paso) + 1;
    const colores = ["#d6312f", "#f4b73b", "#2a7fcf", "#2e8b3a", "#9b7fd1", "#f28c28"];
    let d = "M0 4", focos = "";
    for (let i = 0; i < n; i++) {
      const x = i * paso; d += ` Q${x + paso / 2} 16 ${x + paso} 4`;
      focos += `<g transform="translate(${x + paso / 2},10)"><rect x="-3" y="-2" width="6" height="5" rx="1" fill="#555"/><ellipse class="bulb" style="animation-delay:${(i * .37) % 1.6}s" cx="0" cy="9" rx="5" ry="7.5" fill="${colores[i % colores.length]}"/></g>`;
    }
    caja.innerHTML = `<svg width="${n * paso}" viewBox="0 0 ${n * paso} 26"><path d="${d}" fill="none" stroke="#3b4a3f" stroke-width="1.6"/>${focos}</svg>`;
  }

  function textoCuentaRegresiva() {
    const hoy = new Date(), m = hoy.getMonth(), d = hoy.getDate();
    if (m === 11 && d === 24) return "✨ ¡Hoy es Nochebuena!";
    if (m === 11 && d === 25) return "🎄 ¡Feliz Navidad!";
    if ((m === 11 && d > 25) || m === 0) return "🎆 ¡Feliz Año Nuevo!";
    const faltan = Math.ceil((new Date(hoy.getFullYear(), 11, 25) - new Date(hoy.getFullYear(), m, d)) / 864e5);
    return `🎅 Faltan ${faltan} día${faltan > 1 ? "s" : ""} para Navidad`;
  }

  /* ---------- Bienvenida animada ---------- */
  function intro() {
    const el = $("#intro"); if (!el) return;
    let vista = false;
    try { vista = sessionStorage.getItem("intro-vista") === "1"; sessionStorage.setItem("intro-vista", "1"); } catch (e) { }
    if (vista || reduceMotion || !navidad) { el.remove(); return; }
    const copos = nieve($("#introSnow"), 70, "#ffffff");
    const cerrar = () => {
      if (el.classList.contains("out")) return;
      el.classList.add("out");
      setTimeout(() => { copos && copos.parar(); el.remove(); }, 800);
    };
    el.addEventListener("click", cerrar);
    setTimeout(cerrar, 3300);
  }

  /* ---------- Árbol de la portada ---------- */
  const NIVELES = [[110, 330, 150], [220, 520, 240], [330, 800, 360]];
  const COLORES_REGALO = ["#d6312f", "#e0559a", "#2a7fcf", "#f28c28", "#9b7fd1", "#11807a"];
  function baseArbol(id) {
    let g = `<defs><linearGradient id="${id}" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#2f9a45"/><stop offset="1" stop-color="#1c6b2c"/></linearGradient></defs>`;
    g += `<rect x="365" y="790" width="70" height="70" rx="6" fill="#7a4b2a"/><ellipse cx="400" cy="868" rx="300" ry="22" fill="#e3d3b4"/>`;
    [...NIVELES].reverse().forEach(([a, b, hw]) => {
      const pts = []; for (let j = 0; j <= 9; j++) pts.push(`${400 - hw + j * (2 * hw / 9)},${b + (j % 2 ? 14 : 0)}`);
      g += `<polygon points="400,${a} ${pts.join(" ")}" fill="url(#${id})" stroke="#17592a" stroke-width="3" stroke-linejoin="round"/>`;
    });
    const lc = ["#f4b73b", "#d6312f", "#2a7fcf", "#fff", "#9b7fd1"];
    [[270, 120], [455, 210], [650, 300]].forEach(([y, hw], gi) => {
      g += `<path d="M${400 - hw},${y - 20} Q400,${y + 40} ${400 + hw},${y - 20}" fill="none" stroke="#f4d58a" stroke-width="3" stroke-dasharray="2 6" stroke-linecap="round"/>`;
      for (let i = 0; i <= 10; i++) {
        const t = i / 10, x = (1 - t) ** 2 * (400 - hw) + 2 * (1 - t) * t * 400 + t * t * (400 + hw), yy = (1 - t) ** 2 * (y - 20) + 2 * (1 - t) * t * (y + 40) + t * t * (y - 20);
        g += `<circle class="light" style="animation-delay:${(i * .23 + gi * .4) % 1.6}s" cx="${x}" cy="${yy}" r="5" fill="${lc[(i + gi) % 5]}"/>`;
      }
    });
    g += `<g class="star"><polygon points="400,40 414,82 458,82 422,108 436,150 400,124 364,150 378,108 342,82 386,82" fill="#f4b73b" stroke="#d99a1c" stroke-width="3" stroke-linejoin="round"/></g>`;
    [[230, 815, "#d6312f"], [290, 830, "#2a7fcf"], [500, 825, "#9b7fd1"], [560, 812, "#f28c28"]].forEach(([x, y, c]) => {
      g += `<rect x="${x}" y="${y}" width="50" height="40" rx="4" fill="${c}"/><rect x="${x + 21}" y="${y}" width="8" height="40" fill="#f4d58a"/>`;
    });
    return g;
  }
  function posiciones(n) {
    const filas = [], cuentas = [3, 4, 5, 6, 7, 8, 9]; let total = 0, r = 0;
    while (total < n) { const c = cuentas[Math.min(r, cuentas.length - 1)]; filas.push(c); total += c; r++; }
    const ancho = y => { let m = 0; NIVELES.forEach(([a, b, hw]) => { if (y >= a && y <= b) m = Math.max(m, (y - a) / (b - a) * hw); }); return m; };
    const pos = [];
    filas.forEach((c, i) => {
      const y = filas.length === 1 ? 500 : 250 + i * 500 / (filas.length - 1), hw = ancho(y) * .8, sp = c > 1 ? Math.min(74, 2 * hw / (c - 1)) : 0;
      for (let k = 0; k < c; k++) pos.push([400 + (k - (c - 1) / 2) * sp, y + (k % 2 ? 10 : -4)]);
    });
    return pos.slice(0, n);
  }
  function regalo(x, y, color, tomado) {
    const caja = tomado ? "#c9d3cd" : color, cinta = tomado ? "#e8eee9" : "#fff3c4";
    return `<g transform="translate(${x},${y})"><line x1="0" y1="-34" x2="0" y2="-18" stroke="#c9a24a" stroke-width="2"/>
      <rect x="-17" y="-12" width="34" height="30" rx="4" fill="${caja}"/><rect x="-3" y="-12" width="6" height="30" fill="${cinta}"/>
      <rect x="-20" y="-18" width="40" height="9" rx="3" fill="${caja}" stroke="rgba(0,0,0,.12)"/><rect x="-3" y="-18" width="6" height="9" fill="${cinta}"/>
      <ellipse cx="-7" cy="-21" rx="7" ry="4" fill="${cinta}"/><ellipse cx="7" cy="-21" rx="7" ry="4" fill="${cinta}"/>
      ${tomado ? '<text x="0" y="10" text-anchor="middle" font-size="13">💚</text>' : ""}</g>`;
  }
  function arbolPortada() {
    const svg = $("#miniTree"); if (!svg) return;
    const total = Math.min(parseInt(svg.dataset.total, 10) || 33, 60), tomados = parseInt(svg.dataset.tomados, 10) || 0;
    const pos = posiciones(total);
    // reparte los regalos con padrino de forma pareja por el árbol
    const marcados = new Set(); for (let i = 0; i < Math.min(tomados, total); i++) marcados.add(Math.floor(i * total / Math.max(tomados, 1)));
    let g = `<g transform="scale(.5)">${baseArbol("arbolPortada")}`;
    pos.forEach(([x, y], i) => { g += regalo(x, y, COLORES_REGALO[i % COLORES_REGALO.length], marcados.has(i)); });
    svg.innerHTML = g + "</g>";
  }

  window.CreeArbol = { baseArbol, posiciones, colores: COLORES_REGALO };

  /* ---------- Menú de secciones ---------- */
  const cabecera = $("header.top"), subnav = $("#subnav");
  function altoCabecera() { document.documentElement.style.setProperty("--hh", cabecera.offsetHeight + "px"); }
  function desplazamiento() { return cabecera.offsetHeight + (subnav ? subnav.offsetHeight : 0) + (navidad ? 26 : 0) + 8; }
  let bloqueoSpy = 0;
  function marcar(id) {
    $$("#subnav a").forEach(a => {
      const on = a.dataset.go === id;
      if (on && !a.classList.contains("on")) { a.classList.add("on"); a.scrollIntoView({ block: "nearest", inline: "center", behavior: "smooth" }); }
      else if (!on) a.classList.remove("on");
    });
  }
  function irA(id) {
    cerrarMenu();
    if (id === "top") { bloqueoSpy = Date.now() + 250; marcar("top"); scrollTo({ top: 0, behavior: scrollY > innerHeight * 1.2 ? "instant" : "smooth" }); return; }
    const el = document.getElementById(id); if (!el) return;
    const top = el.getBoundingClientRect().top + scrollY - desplazamiento();
    const lejos = Math.abs(top - scrollY) > innerHeight * 1.2;
    [el, ...$$(".reveal", el)].forEach(x => { if (lejos) { x.style.transition = "none"; setTimeout(() => { x.style.transition = ""; }, 50); } x.classList.add("in"); });
    bloqueoSpy = Date.now() + (lejos ? 250 : 900); marcar(id);
    if (lejos) { el.classList.add("jump"); scrollTo({ top, behavior: "instant" }); setTimeout(() => el.classList.remove("jump"), 600); }
    else scrollTo({ top, behavior: "smooth" });
  }
  function spy() {
    $("#totop").classList.toggle("on", scrollY > 600);
    if (!subnav || Date.now() < bloqueoSpy) return;
    const off = desplazamiento() + 52; let actual = "top";
    $$("section[data-sec]").forEach(s => { if (s.getBoundingClientRect().top - off <= 0) actual = s.id; });
    if (innerHeight + scrollY >= document.body.scrollHeight - 4) actual = "contacto";
    marcar(actual);
  }

  /* ---------- Menú móvil ---------- */
  const burger = $("#burger"), nav = $("#mainNav");
  function cerrarMenu() { nav.classList.remove("open"); burger.classList.remove("open"); burger.setAttribute("aria-expanded", "false"); }
  burger.addEventListener("click", () => {
    const abrir = !nav.classList.contains("open");
    nav.classList.toggle("open", abrir); burger.classList.toggle("open", abrir); burger.setAttribute("aria-expanded", String(abrir));
  });

  /* ---------- Arranque ---------- */
  intro();
  altoCabecera(); addEventListener("resize", () => { altoCabecera(); dibujarLuces(); });
  arbolPortada();
  if (navidad) {
    dibujarLuces();
    const c = $("#xCount"); if (c) c.textContent = textoCuentaRegresiva();
    nieve($("#pageSnow"), 28, "rgba(255,255,255,.95)");
    nieve($("#heroSnow"), 45, "#d9c9a6");
  }
  $$("[data-go]").forEach(a => a.addEventListener("click", e => { e.preventDefault(); irA(a.dataset.go); }));
  $("#totop").addEventListener("click", () => irA("top"));
  $$("[data-car]").forEach(b => b.addEventListener("click", () => {
    b.parentElement.querySelector(".track").scrollBy({ left: 330 * Number(b.dataset.car), behavior: "smooth" });
  }));
  addEventListener("scroll", spy, { passive: true }); spy();

  if (!reduceMotion && "IntersectionObserver" in window) {
    const io = new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); } }), { threshold: .12 });
    $$("section[data-sec], section[data-sec] .card, section[data-sec] .photo, section[data-sec] .ally").forEach((el, i) => {
      el.classList.add("reveal");
      if (el.matches(".card,.photo,.ally")) el.style.transitionDelay = (i % 4) * .08 + "s";
      io.observe(el);
    });
  }
})();
