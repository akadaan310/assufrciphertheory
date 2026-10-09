/* لؤلؤ العربية (لغة اللؤلؤ واللؤلؤة) — القارئ والأطلس. كل إشي هون بيقرا من window.LULU (مولَّد من lab/build.py). */
(function () {
  "use strict";
  const D = window.LULU;
  const CH = window.CHAPTERS || [];
  const NS = "http://www.w3.org/2000/svg";
  const svg = document.getElementById("sky");
  const panel = document.getElementById("panel");
  const sitesById = Object.fromEntries(D.sites.map(s => [s.id, s]));
  const siteBySura = Object.fromEntries(D.sites.map(s => [s.sura, s]));
  const pearlsById = Object.fromEntries(D.pearls.map(p => [p.id, p]));

  if (D.brand) {
    const set = (id, t) => { const e = document.getElementById(id); if (e) e.textContent = t; };
    set("brand-title", D.brand.title); set("brand-line", D.brand.brand);
    set("hero-title", D.brand.title); set("hero-sub", D.brand.subtitle); set("hero-brand", D.brand.brand);
    document.title = D.brand.full_title;
  }
  const ar = n => String(n).replace(/\d/g, d => "٠١٢٣٤٥٦٧٨٩"[d]);
  const SOLID = new Set(["VERIFIED TEXT", "OBSERVED STRUCTURE", "FORMALIZED RULE", "TESTED HYPOTHESIS", "VERIFIED RECITATIONAL FACT"]);
  const edgeKind = statuses => statuses.includes("COUNTEREXAMPLE FOUND") ? "bad"
    : statuses.some(s => SOLID.has(s)) ? "solid" : "dash";

  function el(tag, attrs, parent, text) {
    const e = document.createElementNS(NS, tag);
    for (const k in attrs || {}) e.setAttribute(k, attrs[k]);
    if (text != null) e.textContent = text;
    if (parent) parent.appendChild(e);
    return e;
  }
  function h(tag, attrs, html) {
    const e = document.createElement(tag);
    for (const k in attrs || {}) e.setAttribute(k, attrs[k]);
    if (html != null) e.innerHTML = html;
    return e;
  }
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const css = name => getComputedStyle(document.documentElement).getPropertyValue(name).trim();

  /* ---------------- لوحة التفاصيل ---------------- */
  function ayahBlock(t) {
    return `<div class="ayah">${esc(t.text)}<span class="ref">${esc(t.sura_name)} ${ar(t.sura)}:${ar(t.ayah)}</span></div>`;
  }
  function pearlHTML(p) {
    const st = D.statuses[p.status] || "";
    const list = a => a && a.length ? "<ul>" + a.map(x => `<li>${esc(x)}</li>`).join("") + "</ul>" : "—";
    const f = (k, v) => v ? `<dt>${k}</dt><dd>${v}</dd>` : "";
    return `<h3>${esc(p.title)}</h3>
      <span class="badge">${esc(p.id)} · ${esc(p.status)} · ${esc(st)}</span>
      ${p.texts.slice(0, 6).map(ayahBlock).join("")}${p.texts.length > 6 ? `<p class="hint">+ ${ar(p.texts.length - 6)} موضع ثاني</p>` : ""}
      <dl class="fields">
        ${f("ملاحظة المؤلف", esc(p.author_note))}
        ${f("السؤال", esc(p.question))}
        ${f("القاعدة", esc(p.rule))}
        ${f("العملية", esc(p.operation))}
        ${f("المتوقَّع", esc(p.expected))}
        ${f("الفعلي", esc(p.actual))}
        ${f("شواهد", list(p.supporting))}
        ${f("أمثلة مضادة", `<div class="counter">${list(p.counterexamples)}</div>`)}
        ${f("النص", esc(p.layers.text))}
        ${f("القراءة", esc(p.layers.reading))}
        ${f("التفسير", esc(p.layers.tafsir))}
        ${f("النموذج", esc(p.layers.model))}
        ${f("المصادر", list(p.sources))}
        ${p.source_check ? f("تحقق المصدر", esc(p.source_check)) : ""}
        ${f("التجربة", p.experiment ? `<code>${esc(p.experiment)}</code>` : "")}
        ${f("روابط", p.links.map(l => `<a href="#pearl/${l}">${l}</a>`).join(" · "))}
      </dl>`;
  }
  function showPearl(id) { const p = pearlsById[id]; if (p) panel.innerHTML = pearlHTML(p); }
  function showSite(s) {
    const touching = D.pearls.filter(p => p.sites.includes(s.id) && p.id !== "P-001");
    const con = D.constellations.find(c => c.id === s.constellation);
    panel.innerHTML = `<h3>${esc(s.sura_name)} — <span class="q">${esc(s.opening)}</span></h3>
      <span class="badge">${s.id} · سورة ${ar(s.sura)} · ${ar(s.sura_ayahs)} آية</span>
      ${s.units.map(u => `<div class="ayah">${esc(u.uthmani_ayah_text)}<span class="ref">${ar(s.sura)}:${ar(u.ayah)} · ${u.standalone_ayah ? "الافتتاحية آية مستقلة" : "الافتتاحية جوّا آية أطول"}</span></div>`).join("")}
      <dl class="fields">
        <dt>تصنيف المؤلف</dt><dd>${esc(s.author_class)} <span class="badge">${esc(s.author_class_status)}</span></dd>
        ${s.notes ? `<dt>ملاحظة</dt><dd>${esc(s.notes)}</dd>` : ""}
        <dt>الكوكبة</dt><dd>${esc(con.name)} — <small>${esc(con.rule)}</small></dd>
        <dt>لآلئ بتلمس هالموقع</dt><dd>${touching.length ? touching.map(p => `<a href="#" data-p="${p.id}">${p.id} ${esc(p.title)}</a>`).join("<br>") : "لسه ما في"}</dd>
      </dl>`;
    panel.querySelectorAll("[data-p]").forEach(a => a.onclick = e => { e.preventDefault(); showPearl(a.dataset.p); });
  }

  /* ---------------- أدوات الرسم ---------------- */
  function star(g, x, y, s, opts) {
    const r = opts.r || 5 + s.units[0].letters.length * 1.6;
    const grp = el("g", { class: "star", transform: `translate(${x},${y})`, tabindex: 0, role: "button", "aria-label": `${s.sura_name} ${s.opening}` }, g);
    const cls = s.author_class;
    if (cls === "طائرة") el("circle", { r: r * 2.2, fill: css("--gold"), opacity: .12 }, grp);
    el("circle", {
      r, fill: cls === "غير محسوم" ? "none" : cls === "مغوصة" ? css("--sand") : css("--pearl"),
      stroke: css("--gold"), "stroke-width": cls === "غير محسوم" ? 1.6 : 1, "stroke-dasharray": cls === "غير محسوم" ? "3 2" : "",
    }, grp);
    if (cls === "مغوصة") el("circle", { r: r * .45, fill: css("--sky") }, grp);
    if (opts.label !== false) {
      el("text", { y: -r - 6, "text-anchor": "middle", "font-size": 15, class: "q" }, grp, s.opening);
      el("text", { y: r + 15, "text-anchor": "middle", "font-size": 11, opacity: .75 }, grp, s.sura_name);
    }
    grp.style.cursor = "pointer";
    grp.addEventListener("click", ev => { ev.stopPropagation(); showSite(s); });
    grp.addEventListener("keydown", ev => { if (ev.key === "Enter") showSite(s); });
    return grp;
  }
  function link(g, a, b, kind, pearls, bend) {
    const mx = (a[0] + b[0]) / 2, my = (a[1] + b[1]) / 2;
    const cx = mx + (bend || 0) * (b[1] - a[1]), cy = my - (bend || 0) * (b[0] - a[0]);
    const color = kind === "bad" ? css("--bad") : kind === "dash" ? css("--dash") : css("--gold");
    const p = el("path", { d: `M${a[0]},${a[1]} Q${cx},${cy} ${b[0]},${b[1]}`, fill: "none", stroke: color, "stroke-width": 1.6, opacity: .8, "stroke-dasharray": kind === "dash" ? "6 5" : "" }, g);
    const hit = el("path", { d: p.getAttribute("d"), fill: "none", stroke: "transparent", "stroke-width": 12 }, g);
    hit.style.cursor = "pointer";
    hit.addEventListener("click", ev => { ev.stopPropagation(); if (pearls.length === 1) showPearl(pearls[0]); else listPearls(pearls); });
    el("title", {}, hit, pearls.join("، "));
    return p;
  }
  function listPearls(ids) {
    panel.innerHTML = "<h3>لآلئ هالوصلة</h3>" + ids.map(i => `<p><a href="#" data-p="${i}">${i} — ${esc(pearlsById[i].title)}</a></p>`).join("");
    panel.querySelectorAll("[data-p]").forEach(a => a.onclick = e => { e.preventDefault(); showPearl(a.dataset.p); });
  }
  function note(g, x, y, text, size, anchor, cls) {
    return el("text", { x, y, "font-size": size || 13, "text-anchor": anchor || "middle", fill: css("--ink-soft"), class: cls || "" }, g, text);
  }
  const LEG = {
    solid: '<span><i></i>علاقة متحقَّقة / بنية ملحوظة</span>',
    dash: '<span><i class="dash"></i>قراءة المؤلف / سؤال مفتوح</span>',
    bad: '<span><i class="bad"></i>ظهر مثال مضاد</span>',
    stars: '<span>● طائرة (حسب المؤلف)</span><span>◉ مغوصة (حسب المؤلف)</span><span>◌ غير محسوم</span>',
  };

  /* ---------------- الخرائط السبع ---------------- */
  const MAPS = [
    {
      id: "sites", name: "١ · خريطة المواقع",
      caption: "كل نقطة موقع من التسعة والعشرين، مرتّبة حول الدائرة حسب رقم السورة (١١٤ علامة). الوصلات من سجلّ اللآلئ بس.",
      legend: ["stars", "solid", "dash", "bad"],
      draw(g) {
        const C = [500, 360], R = 280, pos = {};
        for (let i = 1; i <= 114; i++) {
          const t = -Math.PI / 2 + (i - 1) / 114 * 2 * Math.PI;
          const inner = siteBySura[i] ? R - 14 : R - 6;
          el("line", { x1: C[0] + inner * Math.cos(t), y1: C[1] + inner * Math.sin(t), x2: C[0] + R * Math.cos(t), y2: C[1] + R * Math.sin(t), stroke: css("--line") }, g);
        }
        el("circle", { cx: C[0], cy: C[1], r: R, fill: "none", stroke: css("--line") }, g);
        D.sites.forEach(s => {
          const t = -Math.PI / 2 + (s.sura - 1) / 114 * 2 * Math.PI;
          const r = R - 70;
          pos[s.id] = [C[0] + r * Math.cos(t), C[1] + r * Math.sin(t)];
        });
        const eg = el("g", {}, g);
        D.edges.forEach(e => link(eg, pos[e.from], pos[e.to], edgeKind(e.statuses), e.pearls, .25));
        D.sites.forEach(s => star(g, pos[s.id][0], pos[s.id][1], s, {}));
        note(g, C[0], C[1] - 6, "مواقع النجوم", 22);
        note(g, C[0], C[1] + 20, "٢٩ موقعًا · ٣٠ وحدة افتتاحية", 13);
      },
    },
    {
      id: "constellations", name: "٢ · الكوكبات",
      caption: "كل كوكبة إلها قاعدة معلنة على حروف الافتتاحية. الخطوط داخل الكوكبة بتمشي حسب ترتيب المصحف.",
      legend: ["stars"],
      draw(g) {
        const centers = { "C-ALIF-LAM": [720, 250], "C-TA-SIN": [300, 170], "C-HA-MIM": [300, 470], "C-SINGLE": [720, 560], "C-OTHER": [520, 640] };
        D.constellations.forEach(c => {
          const members = D.sites.filter(s => s.constellation === c.id);
          const [cx, cy] = centers[c.id];
          const rr = 40 + members.length * 9;
          el("circle", { cx, cy, r: rr + 30, fill: css("--gold"), opacity: .04 }, g);
          const pts = members.map((s, i) => {
            const t = -Math.PI / 2 + i / members.length * 2 * Math.PI;
            return [cx + rr * Math.cos(t), cy + rr * Math.sin(t), s];
          });
          if (pts.length > 1) el("polyline", { points: pts.map(p => p[0] + "," + p[1]).join(" ") + (pts.length > 2 ? " " + pts[0][0] + "," + pts[0][1] : ""), fill: "none", stroke: css("--gold-soft"), opacity: .5 }, g);
          pts.forEach(([x, y, s]) => star(g, x, y, s, {}));
          note(g, cx, cy - 4, c.name, 17);
          note(g, cx, cy + 16, c.rule.length > 34 ? c.rule.slice(0, 34) + "…" : c.rule, 10);
        });
      },
    },
    {
      id: "order", name: "٣ · ترتيب المصحف",
      caption: "خط السور من ١ (يمين) إلى ١١٤ (يسار) حسب ترتيب المصحف — مش ترتيب النزول. الأقواس بتبيّن السلاسل المتتالية.",
      legend: ["stars"],
      draw(g) {
        const x = n => 960 - (n - 1) / 113 * 920, Y = 380;
        el("line", { x1: 40, y1: Y, x2: 960, y2: Y, stroke: css("--line"), "stroke-width": 2 }, g);
        for (let i = 1; i <= 114; i++) el("line", { x1: x(i), y1: Y - (i % 10 === 0 ? 8 : 3), x2: x(i), y2: Y + (i % 10 === 0 ? 8 : 3), stroke: css("--line") }, g);
        [1, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 114].forEach(i => note(g, x(i), Y + 26, ar(i), 11));
        const runs = [[10, 15, "الر ×٥ + المر (١٠–١٥)"], [26, 28, "طسم · طس · طسم"], [29, 32, "الم ×٤ (٢٩–٣٢)"], [40, 46, "حم ×٧ (٤٠–٤٦)"]];
        runs.forEach(([a, b, t], k) => {
          const y = Y - 150 - (k % 2) * 40;
          el("path", { d: `M${x(a) + 6},${Y - 30} L${x(a) + 6},${y} L${x(b) - 6},${y} L${x(b) - 6},${Y - 30}`, fill: "none", stroke: css("--gold-soft"), opacity: .7 }, g);
          note(g, (x(a) + x(b)) / 2, y - 8, t, 12);
        });
        D.sites.forEach((s, i) => star(g, x(s.sura), Y - 60 - (i % 2) * 0, s, { r: 6, label: false }));
        D.sites.forEach((s, i) => {
          const up = i % 2 === 0;
          el("text", { x: x(s.sura), y: up ? Y + 60 + (i % 4) * 14 : Y + 120 + (i % 4) * 14, "text-anchor": "middle", "font-size": 12, class: "q" }, g, s.opening);
        });
        note(g, 500, 640, "انتبه: الرعد (١٣) بتقع جوّا سلسلة الر، وافتتاحيتها المر — هون بالضبط غاصت الميم.", 13);
      },
    },
    {
      id: "rum", name: "٤ · هندسة الروم والرعد",
      caption: "حروف ا ل م ر والعمليات بينها. الأسهم = إضافة/حذف حرف على الهيكل. «الرم» محسوبة كملتقى للم والر بس غايبة عن النص.",
      legend: ["solid", "dash"],
      draw(g) {
        const N = {
          L: [500, 70, "ا · ل · م · ر", "letters"],
          alm: [680, 200, "الم", "op"], alr: [320, 200, "الر", "op"],
          almr: [680, 360, "المر", "op"], alrm: [320, 360, "الرم", "absent"],
          amr: [800, 510, "الامر", "word"], rum: [320, 510, "الروم", "word"], irm: [140, 510, "ارم", "word"],
          almS: [880, 260, "المص", "op"],
        };
        const E = [["alm", "almr", "+ ر"], ["alr", "almr", "+ م"], ["alm", "alrm", "+ ر"], ["alr", "alrm", "+ م"],
          ["almr", "amr", "+ ا (همزة)"], ["alrm", "rum", "+ و"], ["alrm", "irm", "− ل"], ["alm", "almS", "+ ص"], ["alm", "alr", "م ↔ ر"]];
        E.forEach(([a, b, t]) => {
          const A = N[a], B = N[b], dashed = a === "alrm" || b === "alrm";
          el("line", { x1: A[0], y1: A[1], x2: B[0], y2: B[1], stroke: dashed ? css("--dash") : css("--gold"), "stroke-dasharray": dashed ? "6 5" : "", opacity: .8 }, g);
          note(g, (A[0] + B[0]) / 2 + 14, (A[1] + B[1]) / 2 - 6, t, 12);
        });
        ["L", "alm", "alr"].forEach(k => el("line", { x1: N.L[0], y1: N.L[1] + 18, x2: N[k][0], y2: N[k][1] - 22, stroke: css("--line") }, g));
        Object.entries(N).forEach(([k, [x, y, t, kind]]) => {
          const grp = el("g", { transform: `translate(${x},${y})` }, g);
          el("rect", { x: -58, y: -24, width: 116, height: 44, rx: 12, fill: kind === "absent" ? "none" : css("--sky-2"), stroke: kind === "absent" ? css("--dash") : css("--gold"), "stroke-dasharray": kind === "absent" ? "5 4" : "" }, grp);
          el("text", { y: 7, "text-anchor": "middle", "font-size": 22, class: "q" }, grp, t);
        });
        note(g, N.alm[0], N.alm[1] + 40, "البقرة، آل عمران، العنكبوت، الروم، لقمان، السجدة", 11);
        note(g, N.alr[0], N.alr[1] + 40, "يونس، هود، يوسف، إبراهيم، الحجر", 11);
        note(g, N.almr[0], N.almr[1] + 40, "الرعد ١٣ — هون غاصت الميم", 12);
        note(g, N.alrm[0], N.alrm[1] + 40, "ملتقى محسوب، مش موجود بالنص", 11);
        el("circle", { cx: N.almr[0] + 6, cy: N.almr[1] + 2, r: 13, fill: "none", stroke: css("--sand"), "stroke-width": 2 }, g);
        note(g, 500, 610, "الم في الروم (٣٠) مش حالة الغوص. الغوص المقترح للميم = المر في الرعد (١٣).", 14);
        const lb = link(g, [600, 660], [400, 660], "solid", ["P-007", "P-008"], .25);
        lb.setAttribute("stroke-width", 2.4);
        note(g, 640, 665, "الرعد", 13); note(g, 360, 665, "الروم", 13);
        note(g, 500, 700, "لله الأمر (١٣:٣١، ٣٠:٤) · يريكم البرق خوفا (١٣:١٢، ٣٠:٢٤)", 12);
      },
    },
    {
      id: "hamim", name: "٥ · كوكبة حم",
      caption: "السور السبع المتتالية ٤٠–٤٦. عسق نجمة منفصلة تحت الشورى. الطبقات السبع (إذا فعّلتها) تمثيل افتراضي، مش وصف للصرح.",
      legend: ["stars", "solid"],
      layers: false,
      draw(g) {
        const xs = i => 880 - i * 125, Y = 380;
        const chain = D.sites.filter(s => s.constellation === "C-HA-MIM");
        if (this.layers) {
          for (let k = 0; k < 7; k++) el("rect", { x: 70, y: 70 + k * 30, width: 860, height: 24, rx: 6, fill: css("--dash"), opacity: .05 + k * .02 }, g);
          note(g, 500, 300, "تمثيل افتراضي لفحص فرضية: ٧ طبقات ↔ ٧ سور. النص ما بيقول إن الصرح سبع طبقات.", 13);
        }
        el("polyline", { points: chain.map((s, i) => xs(i) + "," + Y).join(" "), fill: "none", stroke: css("--gold-soft") }, g);
        chain.forEach((s, i) => star(g, xs(i), Y, s, { r: 11 }));
        const shura = chain.find(s => s.sura === 42), si = chain.indexOf(shura);
        el("line", { x1: xs(si), y1: Y + 30, x2: xs(si), y2: Y + 92, stroke: css("--gold"), "stroke-dasharray": "2 3" }, g);
        el("circle", { cx: xs(si), cy: Y + 110, r: 10, fill: "none", stroke: css("--gold"), "stroke-dasharray": "3 2" }, g);
        el("text", { x: xs(si), y: Y + 145, "text-anchor": "middle", "font-size": 17, class: "q" }, g, "عسق");
        note(g, xs(si), Y + 165, "٤٢:٢ — آية منفصلة", 11);
        const box = (i, lines, y) => { lines.forEach((t, k) => note(g, xs(i), y + k * 18, t, k ? 11 : 13)); };
        box(0, ["٤٠:٣٦–٣٧", "صرحًا … أسباب السماوات"], Y - 110);
        box(1, ["٤١:١٢", "سبع سماوات … أمرها"], Y - 110);
        link(g, [xs(0), Y - 75], [xs(1), Y - 75], "solid", ["P-016"], .4);
        box(6, ["٤٦:٣٥", "ولا تستعجل لهم"], Y - 110);
      },
    },
    {
      id: "paths", name: "٦ · مسارات الآيات",
      caption: "كل نقطة آية من سجلّ اللآلئ؛ الوصلة بين آيتين معناها لؤلؤة بتجمعهم. اضغط الوصلة عشان تقرا تفسيرها.",
      legend: ["solid", "dash", "bad"],
      draw(g) {
        const refs = new Map();
        D.pearls.filter(p => p.id !== "P-001").forEach(p => p.texts.forEach(t => refs.set(t.sura + ":" + t.ayah, t)));
        const keys = [...refs.keys()].sort((a, b) => { const [s1, a1] = a.split(":").map(Number), [s2, a2] = b.split(":").map(Number); return s1 - s2 || a1 - a2; });
        const C = [500, 360], R = 290, pos = {};
        keys.forEach((k, i) => { const t = -Math.PI / 2 + i / keys.length * 2 * Math.PI; pos[k] = [C[0] + R * Math.cos(t), C[1] + R * Math.sin(t), t]; });
        const pairs = new Map();
        D.pearls.filter(p => p.id !== "P-001").forEach(p => {
          const ks = [...new Set(p.texts.map(t => t.sura + ":" + t.ayah))];
          for (let i = 0; i < ks.length - 1; i++) {
            const id = ks[i] + "|" + ks[i + 1];
            if (!pairs.has(id)) pairs.set(id, { a: ks[i], b: ks[i + 1], pearls: [], statuses: [] });
            pairs.get(id).pearls.push(p.id); pairs.get(id).statuses.push(p.status);
          }
        });
        pairs.forEach(e => link(g, pos[e.a], pos[e.b], edgeKind(e.statuses), e.pearls, .15));
        keys.forEach(k => {
          const [x, y, t] = pos[k], ref = refs.get(k);
          const isSite = siteBySura[ref.sura] ? 1 : 0;
          const c = el("circle", { cx: x, cy: y, r: 5, fill: isSite ? css("--pearl") : css("--sand"), stroke: css("--gold") }, g);
          const lx = C[0] + (R + 22) * Math.cos(t), ly = C[1] + (R + 22) * Math.sin(t);
          el("text", { x: lx, y: ly + 4, "text-anchor": "middle", "font-size": 10 }, g, ar(k));
          c.style.cursor = "pointer";
          c.addEventListener("click", ev => { ev.stopPropagation(); panel.innerHTML = ayahBlock(ref) + "<p class='hint'>لآلئ:</p>" + D.pearls.filter(p => p.texts.some(t => t.sura === ref.sura && t.ayah === ref.ayah)).map(p => `<p><a href="#" data-p="${p.id}">${p.id} ${esc(p.title)}</a></p>`).join(""); panel.querySelectorAll("[data-p]").forEach(a => a.onclick = e => { e.preventDefault(); showPearl(a.dataset.p); }); });
        });
        note(g, C[0], C[1], "نقطة فاتحة = آية من سورة موقع · رملية = آية من سورة ثانية", 12);
      },
    },
    {
      id: "zero", name: "٧ · الصفر والفراغ والحدود",
      caption: "أربع حالات مختلفة ما لازم نخلط بينها. ولا لون ولا حجم هون بيوحي بأهمية ما ثبتت.",
      legend: [],
      draw(g) {
        const cols = [
          ["موجود", "وحدة افتتاحية ظاهرة بالنص", ["الم", "المر", "حم", "عسق"], "solid"],
          ["غائب محسوب", "النموذج بيتوقعه، والنص ما فيه", ["الرم"], "dash"],
          ["محذوف بعملية", "ناتج عملية حذف معرّفة", ["الر = المر − م", "ارم = الرم − ل"], "solid"],
          ["غير محسوم", "تصنيف ما حكم فيه المؤلف لسه", ["طسم", "يس", "حم ×٧", "عسق"], "dash"],
        ];
        cols.forEach(([t, sub, items, kind], i) => {
          const x = 860 - i * 240;
          el("rect", { x: x - 100, y: 90, width: 200, height: 470, rx: 16, fill: "none", stroke: kind === "dash" ? css("--dash") : css("--gold-soft"), "stroke-dasharray": kind === "dash" ? "6 5" : "" }, g);
          note(g, x, 130, t, 19);
          note(g, x, 155, sub, 11);
          items.forEach((it, k) => el("text", { x, y: 220 + k * 70, "text-anchor": "middle", "font-size": 22, class: "q" }, g, it));
        });
        note(g, 500, 620, "الغياب بيصير معلومة بس لما يكون في نموذج بيقول شو المتوقَّع، وفحص بيقول إنه مش موجود —", 13);
        note(g, 500, 645, "مثل «وتفقد الطير … أم كان من الغائبين» (٢٧:٢٠): التفقّد فحص، والغياب نتيجته.", 13);
      },
    },
  ];

  /* ---------------- تكبير وتحريك ---------------- */
  let vb = [0, 0, 1000, 720];
  const setVB = () => svg.setAttribute("viewBox", vb.join(" "));
  svg.addEventListener("wheel", e => {
    e.preventDefault();
    const k = e.deltaY > 0 ? 1.1 : 0.9, r = svg.getBoundingClientRect();
    const mx = vb[0] + (e.clientX - r.left) / r.width * vb[2], my = vb[1] + (e.clientY - r.top) / r.height * vb[3];
    vb = [mx - (mx - vb[0]) * k, my - (my - vb[1]) * k, vb[2] * k, vb[3] * k]; setVB();
  }, { passive: false });
  let drag = null;
  svg.addEventListener("pointerdown", e => { drag = [e.clientX, e.clientY, vb[0], vb[1]]; });
  window.addEventListener("pointerup", () => { drag = null; });
  svg.addEventListener("pointermove", e => {
    if (!drag) return; const r = svg.getBoundingClientRect();
    vb[0] = drag[2] - (e.clientX - drag[0]) / r.width * vb[2]; vb[1] = drag[3] - (e.clientY - drag[1]) / r.height * vb[3]; setVB();
  });
  svg.addEventListener("dblclick", () => { vb = [0, 0, 1000, 720]; setVB(); });

  let current = MAPS[0];
  function drawMap(m) {
    current = m;
    svg.innerHTML = "";
    vb = [0, 0, 1000, 720]; setVB();
    m.draw(el("g", {}, svg));
    document.getElementById("caption").textContent = m.caption + " (عجلة الماوس للتكبير، اسحب للتحريك، دبل كليك للرجوع.)";
    const lg = document.getElementById("legend");
    lg.innerHTML = m.legend.map(k => LEG[k]).join("");
    if (m.id === "hamim") {
      const b = h("button", { type: "button" }, m.layers ? "إخفاء التمثيل الافتراضي" : "عرض ٧ طبقات (تمثيل افتراضي)");
      b.className = "maps-toggle"; b.style.cssText = "font:inherit;font-size:.8rem;background:none;color:inherit;border:1px dashed currentColor;border-radius:8px;cursor:pointer";
      b.onclick = () => { m.layers = !m.layers; drawMap(m); };
      lg.appendChild(b);
    }
    document.querySelectorAll(".maps button").forEach(b => b.classList.toggle("on", b.dataset.id === m.id));
  }
  const tabs = document.querySelector(".maps");
  MAPS.forEach(m => { const b = h("button", { type: "button", "data-id": m.id, role: "tab" }, m.name); b.onclick = () => drawMap(m); tabs.appendChild(b); });

  /* ---------------- الكتاب ---------------- */
  const toc = document.getElementById("toc"), chapter = document.getElementById("chapter");
  CH.forEach(c => { const li = h("li"); li.appendChild(h("a", { href: "#book/" + c.slug }, esc(c.title))); toc.appendChild(li); });
  function openChapter(slug) {
    const c = CH.find(x => x.slug === slug) || CH[0];
    if (!c) { chapter.innerHTML = "<p>لسه ما في فصول.</p>"; return; }
    chapter.innerHTML = c.html;
    toc.querySelectorAll("a").forEach(a => a.classList.toggle("on", a.getAttribute("href") === "#book/" + c.slug));
    window.scrollTo(0, 0);
  }

  /* ---------------- سجلّ اللآلئ ---------------- */
  const list = document.getElementById("pearl-list"), filters = document.getElementById("filters");
  let filter = null;
  function renderPearls(focus) {
    list.innerHTML = "";
    D.pearls.filter(p => !filter || p.status === filter).forEach(p => {
      const c = h("article", { class: "pearl-card", id: "card-" + p.id });
      c.innerHTML = focus === p.id ? pearlHTML(p) : `<span class="id">${p.id}</span><h3>${esc(p.title)}</h3><span class="badge">${esc(p.status)} · ${esc(D.statuses[p.status])}</span><p>${esc(p.actual)}</p><a href="#pearl/${p.id}">افتح اللؤلؤة كاملة</a>`;
      list.appendChild(c);
    });
    if (focus) { const t = document.getElementById("card-" + focus); if (t) t.scrollIntoView({ block: "start" }); }
  }
  const allBtn = h("button", { type: "button", class: "on" }, "الكل");
  allBtn.onclick = () => { filter = null; filters.querySelectorAll("button").forEach(b => b.classList.toggle("on", b === allBtn)); renderPearls(); };
  filters.appendChild(allBtn);
  Object.entries(D.statuses).forEach(([k, v]) => {
    const n = D.pearls.filter(p => p.status === k).length; if (!n) return;
    const b = h("button", { type: "button" }, `${esc(v)} (${ar(n)})`);
    b.onclick = () => { filter = k; filters.querySelectorAll("button").forEach(x => x.classList.toggle("on", x === b)); renderPearls(); };
    filters.appendChild(b);
  });

  /* ---------------- التوجيه ---------------- */
  function route() {
    const hash = location.hash.slice(1) || "atlas";
    const [view, arg] = hash.split("/");
    const v = view === "pearl" ? "pearls" : (["atlas", "book", "pearls"].includes(view) ? view : "atlas");
    document.querySelectorAll(".view").forEach(s => { s.hidden = s.id !== "view-" + v; });
    document.querySelectorAll(".top nav a").forEach(a => a.classList.toggle("on", a.dataset.view === v));
    if (v === "book") openChapter(arg);
    if (v === "pearls") renderPearls(view === "pearl" ? arg : null);
    if (v === "atlas") drawMap(current);
  }
  window.addEventListener("hashchange", route);

  /* ---------------- الوضع ---------------- */
  const root = document.documentElement;
  try { const t = localStorage.getItem("lulu-theme"); if (t) root.dataset.theme = t; } catch (e) { /* بلا تخزين */ }
  document.getElementById("theme").onclick = () => {
    const dark = root.dataset.theme ? root.dataset.theme === "dark" : !matchMedia("(prefers-color-scheme: light)").matches;
    root.dataset.theme = dark ? "light" : "dark";
    try { localStorage.setItem("lulu-theme", root.dataset.theme); } catch (e) { /* بلا تخزين */ }
    if (!document.getElementById("view-atlas").hidden) drawMap(current);
  };

  route();
})();
