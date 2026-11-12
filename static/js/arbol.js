/* Árbol de regalos: selección de varios regalos y confirmación.
   La página solo conoce el estado de cada regalo; la asignación al azar la hace el servidor. */
(function () {
  "use strict";
  const svg = document.getElementById("tree");
  if (!svg || !window.CreeArbol) return;
  const { baseArbol, posiciones, colores } = window.CreeArbol;
  const slots = svg.dataset.slots || "";
  const logueado = svg.dataset.auth === "1";
  const maximo = parseInt(svg.dataset.max, 10) || 10;
  const minimo = parseInt(svg.dataset.min, 10) || 30;
  const previos = parseInt(svg.dataset.mios, 10) || 0;
  const sel = new Set();
  const $ = id => document.getElementById(id);

  function regalo(x, y, i, estado) {
    const mio = estado === "m", tomado = estado === "t", elegido = sel.has(i);
    const caja = mio ? "#f4b73b" : tomado ? "#c9d3cd" : colores[i % colores.length];
    const cinta = tomado ? "#e8eee9" : "#fff3c4";
    const clase = estado === "f" ? "free" + (elegido ? " sel" : "") : "taken" + (mio ? " mine" : "");
    const etiqueta = estado === "f" ? (elegido ? "Regalo seleccionado" : "Regalo disponible") : mio ? "Tu regalo" : "Ya tiene padrino";
    const icono = mio ? '<text x="0" y="10" text-anchor="middle" font-size="14">⭐</text>' : tomado ? '<text x="0" y="10" text-anchor="middle" font-size="13">💚</text>' : "";
    const interactivo = estado !== "t";
    return `<g class="gift ${clase}" transform="translate(${x},${y})" ${interactivo ? `data-i="${i}" tabindex="0" role="button"` : ""} aria-label="${etiqueta}"><g class="anim">
      ${elegido ? '<circle cx="0" cy="0" r="30" fill="#fff" stroke="#f4b73b" stroke-width="4"/>' : ""}
      <line x1="0" y1="-34" x2="0" y2="-18" stroke="#c9a24a" stroke-width="2"/>
      <rect class="box" x="-17" y="-12" width="34" height="30" rx="4" fill="${caja}"/><rect x="-3" y="-12" width="6" height="30" fill="${cinta}"/>
      <rect x="-20" y="-18" width="40" height="9" rx="3" fill="${caja}" stroke="rgba(0,0,0,.12)"/><rect x="-3" y="-18" width="6" height="9" fill="${cinta}"/>
      <ellipse cx="-7" cy="-21" rx="7" ry="4" fill="${cinta}" stroke="rgba(0,0,0,.15)"/><ellipse cx="7" cy="-21" rx="7" ry="4" fill="${cinta}" stroke="rgba(0,0,0,.15)"/>
      ${icono}${elegido ? '<g transform="translate(18,-24)"><circle r="10" fill="#2e8b3a"/><text y="5" text-anchor="middle" font-size="13" fill="#fff" font-weight="800">✓</text></g>' : ""}</g></g>`;
  }

  function dibujar() {
    const pos = posiciones(slots.length);
    let g = baseArbol("arbolGrande");
    for (let i = 0; i < slots.length; i++) g += regalo(pos[i][0], pos[i][1], i, slots[i]);
    svg.innerHTML = g;
    barra();
  }

  function barra() {
    const el = $("selbar"), n = sel.size;
    el.classList.toggle("on", n > 0);
    el.innerHTML = n ? `<div style="font-size:26px">🎁</div><div class="t">${n} regalo${n > 1 ? "s" : ""} seleccionado${n > 1 ? "s" : ""}<small>Mínimo ${n * minimo} $ en total</small></div>
      <button class="btn btn-ghost btn-sm" type="button" data-limpiar>Limpiar</button><button class="btn btn-red btn-sm" type="button" data-continuar>Continuar →</button>` : "";
  }

  function abrir(id) { $(id).classList.add("on"); }
  function cerrar() { document.querySelectorAll(".modal-bg.on").forEach(m => m.classList.remove("on")); }

  function tocar(i) {
    const estado = slots[i];
    if (estado === "m") { location.href = "/mi-panel/"; return; }
    if (!logueado) { abrir("mIngresar"); return; }
    if (sel.has(i)) sel.delete(i);
    else if (sel.size >= maximo) { alertaSuave(`Puedes elegir hasta ${maximo} regalos a la vez.`); return; }
    else sel.add(i);
    dibujar();
  }

  function alertaSuave(texto) {
    const t = document.createElement("div");
    t.className = "aviso aviso-info"; t.textContent = texto;
    let caja = document.querySelector(".avisos");
    if (!caja) { caja = document.createElement("div"); caja.className = "avisos"; document.body.appendChild(caja); }
    caja.appendChild(t); setTimeout(() => t.remove(), 4000);
  }

  function confirmar() {
    const n = sel.size; if (!n) return;
    $("cCantidad").value = n;
    $("cIconos").textContent = "🎁".repeat(Math.min(n, 5));
    $("cTitulo").textContent = n === 1 ? "¿Confirmas tu regalo?" : `¿Confirmas tus ${n} regalos?`;
    $("cTexto").innerHTML = `Te asignaremos <b>${n === 1 ? "un niño" : n + " niños"} al azar</b> y te comprometes a dar ${n === 1 ? "un regalo" : "un regalo a cada uno"} de <b>mínimo ${minimo} $</b>${n > 1 ? ` (<b>${n * minimo} $</b> en total)` : ""}.`;
    const p = $("cPrevios");
    if (previos) { p.style.display = ""; p.innerHTML = `Ya tienes <b>${previos}</b> niño(s) apadrinado(s). Con estos serían <b>${previos + n}</b> (mínimo <b>${(previos + n) * minimo} $</b> en total).`; }
    $("cOk").checked = false; $("cGo").disabled = true;
    abrir("mConfirmar");
  }

  svg.addEventListener("click", e => { const g = e.target.closest("[data-i]"); if (g) tocar(+g.dataset.i); });
  svg.addEventListener("keydown", e => { const g = e.target.closest("[data-i]"); if (g && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); tocar(+g.dataset.i); } });
  $("selbar").addEventListener("click", e => {
    if (e.target.closest("[data-limpiar]")) { sel.clear(); dibujar(); }
    if (e.target.closest("[data-continuar]")) confirmar();
  });
  $("cOk").addEventListener("change", e => { $("cGo").disabled = !e.target.checked; });
  $("cGo").closest("form").addEventListener("submit", e => {
    const f = e.target;
    f.querySelectorAll("input[name=slot]").forEach(x => x.remove());
    sel.forEach(i => { const h = document.createElement("input"); h.type = "hidden"; h.name = "slot"; h.value = i; f.appendChild(h); });
    $("cGo").disabled = true; $("cGo").textContent = "Asignando…";
  });
  document.querySelectorAll("[data-cerrar]").forEach(b => b.addEventListener("click", cerrar));
  document.querySelectorAll(".modal-bg").forEach(m => m.addEventListener("click", e => { if (e.target === m) cerrar(); }));
  document.addEventListener("keydown", e => { if (e.key === "Escape") cerrar(); });
  dibujar();
})();
