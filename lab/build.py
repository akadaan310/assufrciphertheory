# -*- coding: utf-8 -*-
"""بناء بيانات الأطلس والقارئ من مصدر واحد.

    python3 lab/build.py

بيشغّل التجارب، بيبني data/sites.json، بيسحب نص كل مرجع قرآني في اللآلئ من
تنزيل (ما في نص قرآني مكتوب باليد في السجل)، وبيكتب web/data.js.
الرسومات كلها بتقرا من web/data.js، فما في رسم بيحمل معلومة مختلفة عن السجل.
"""
import glob
import html
import itertools
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import experiments  # noqa: E402
import quran  # noqa: E402

PEARLS = os.path.join(quran.ROOT, "data", "pearls.json")
BRAND = os.path.join(quran.ROOT, "data", "brand.json")
WEB_DATA = os.path.join(quran.ROOT, "web", "data.js")
WEB_CHAPTERS = os.path.join(quran.ROOT, "web", "chapters.js")
CHAPTERS_DIR = os.path.join(quran.ROOT, "book", "chapters")

# الكوكبات: كل وحدة إلها قاعدة معلنة على حروف الافتتاحية (الوحدة الأولى).
CONSTELLATIONS = [
    {"id": "C-ALIF-LAM", "name": "عيلة ا ل", "rule": "الافتتاحية بتبدأ بـ«ال» (الم، المص، الر، المر)",
     "test": lambda L: L.startswith("ال")},
    {"id": "C-TA-SIN", "name": "عيلة طس", "rule": "الافتتاحية بتبدأ بـ«طس» (طس، طسم)",
     "test": lambda L: L.startswith("طس")},
    {"id": "C-HA-MIM", "name": "كوكبة حم", "rule": "الافتتاحية «حم» (السور السبع المتتالية ٤٠–٤٦)",
     "test": lambda L: L == "حم"},
    {"id": "C-SINGLE", "name": "الحرف المفرد", "rule": "الافتتاحية حرف واحد (ص، ق، ن)",
     "test": lambda L: len(L) == 1},
    {"id": "C-OTHER", "name": "نجوم منفردة", "rule": "كل اللي ما دخل بقاعدة من فوق (كهيعص، طه، يس)",
     "test": None},
]


def constellation_of(letters):
    for c in CONSTELLATIONS:
        if c["test"] and c["test"](letters):
            return c["id"]
    return "C-OTHER"


# ---------------------------------------------------------------------------
# فصول الكتاب: Markdown بسيط → HTML. النص القرآني بالفصول ما بينكتب باليد:
#   {{q:30:2}}  أو  {{q:30:1-3}}   → اقتباس قرآني من تنزيل مع المرجع
#   {{qi:30:2}}                    → نفس الشي جوّا السطر
#   [P-007]                        → رابط للؤلؤة
#   ::: box ... :::                → صندوق بحثي
# ---------------------------------------------------------------------------
_Q_BLOCK = re.compile(r"^\{\{q:(\d+):(\d+)(?:-(\d+))?\}\}$")
_Q_INLINE = re.compile(r"\{\{qi:(\d+):(\d+)\}\}")
_PEARL = re.compile(r"\[(P-\d{3})\]")
_BOLD = re.compile(r"\*\*(.+?)\*\*")
_CODE = re.compile(r"`([^`]+)`")
AR = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")


def _ref(q, s, a, b=None):
    span = f"{a}" if b is None else f"{a}–{b}"
    return f"{q.name(s)} {s}:{span}".translate(AR)


def _inline(q, text, pearl_ids):
    def qi(m):
        s, a = int(m.group(1)), int(m.group(2))
        return f'<span class="q">﴿{html.escape(q.verse(s, a))}﴾</span> <small>({_ref(q, s, a)})</small>'

    def pearl(m):
        pid = m.group(1)
        if pid not in pearl_ids:
            raise ValueError(f"الفصل بيشير للؤلؤة مش موجودة: {pid}")
        return f'<a class="pearl-ref" href="#pearl/{pid}">{pid}</a>'

    out = html.escape(text, quote=False)
    out = _Q_INLINE.sub(qi, out)
    out = _PEARL.sub(pearl, out)
    out = _BOLD.sub(r"<strong>\1</strong>", out)
    out = _CODE.sub(r"<code>\1</code>", out)
    return out


def markdown(q, src, pearl_ids):
    lines = src.split("\n")
    out, para, i = [], [], 0

    def flush():
        if para:
            out.append("<p>" + _inline(q, " ".join(para), pearl_ids) + "</p>")
            para.clear()

    while i < len(lines):
        line = lines[i].rstrip()
        m = _Q_BLOCK.match(line.strip())
        if line.strip() == "{{sites}}":
            flush()
            sites = json.load(open(os.path.join(quran.ROOT, "data", "sites.json"), encoding="utf-8"))["sites"]
            rows = ["<tr><th>النجمة</th><th>السورة</th><th>الافتتاحية كما هي</th><th>حدّها</th><th>تصنيف المؤلف</th></tr>"]
            for st in sites:
                written = " ۝ ".join(html.escape(u["opening_as_written"]) for u in st["units"])
                where = " + ".join(("آية مستقلة" if u["standalone_ayah"] else "داخل آية") + f" ({u['ayah']})".translate(AR) for u in st["units"])
                rows.append(f"<tr><td>{st['id']}</td><td>{html.escape(st['sura_name'])} {str(st['sura']).translate(AR)}</td>"
                            f"<td class=\"q\">{written}</td><td>{where}</td><td>{html.escape(st['author_class'])}</td></tr>")
            out.append("<table>" + "".join(rows) + "</table>")
        elif m:
            flush()
            s, a = int(m.group(1)), int(m.group(2))
            b = int(m.group(3)) if m.group(3) else a
            body = " ".join(f"{html.escape(q.verse(s, k))} ﴿{str(k).translate(AR)}﴾" for k in range(a, b + 1))
            out.append(f'<blockquote class="quran">{body}<br><small>— {_ref(q, s, a, b if b != a else None)}</small></blockquote>')
        elif line.startswith("#"):
            flush()
            n = len(line) - len(line.lstrip("#"))
            out.append(f"<h{n}>{_inline(q, line[n:].strip(), pearl_ids)}</h{n}>")
        elif line.strip() == "::: box":
            flush()
            j = i + 1
            while lines[j].strip() != ":::":
                j += 1
            out.append('<div class="box">' + markdown(q, "\n".join(lines[i + 1:j]), pearl_ids) + "</div>")
            i = j
        elif line.startswith("> "):
            flush()
            block = []
            while i < len(lines) and lines[i].startswith(">"):
                block.append(lines[i][1:].strip())
                i += 1
            out.append("<blockquote>" + _inline(q, " ".join(block), pearl_ids) + "</blockquote>")
            continue
        elif line.startswith("- "):
            flush()
            items = []
            while i < len(lines) and lines[i].startswith("- "):
                items.append("<li>" + _inline(q, lines[i][2:], pearl_ids) + "</li>")
                i += 1
            out.append("<ul>" + "".join(items) + "</ul>")
            continue
        elif line.startswith("|"):
            flush()
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(set(c) <= set("-: ") for c in cells):
                    tag = "th" if not rows else "td"
                    rows.append("<tr>" + "".join(f"<{tag}>{_inline(q, c, pearl_ids)}</{tag}>" for c in cells) + "</tr>")
                i += 1
            out.append("<table>" + "".join(rows) + "</table>")
            continue
        elif not line.strip():
            flush()
        else:
            para.append(line.strip())
        i += 1
    flush()
    return "\n".join(out)


def build_chapters(q, pearl_ids):
    chapters = []
    for path in sorted(glob.glob(os.path.join(CHAPTERS_DIR, "*.md"))):
        src = open(path, encoding="utf-8").read()
        title = src.split("\n", 1)[0].lstrip("# ").strip()
        slug = os.path.splitext(os.path.basename(path))[0]
        chapters.append({"slug": slug, "title": title, "html": markdown(q, src, pearl_ids)})
    with open(WEB_CHAPTERS, "w", encoding="utf-8") as f:
        f.write("// مولَّد آليًا من lab/build.py — لا تعدّل باليد.\nwindow.CHAPTERS = ")
        json.dump(chapters, f, ensure_ascii=False)
        f.write(";\n")
    return chapters


def build():
    q = quran.load()
    results = {r["id"]: r for r in experiments.run_all()}
    sites = json.load(open(os.path.join(quran.ROOT, "data", "sites.json"), encoding="utf-8"))["sites"]
    by_sura = {s["sura"]: s for s in sites}
    for s in sites:
        s["constellation"] = constellation_of(s["units"][0]["letters"])

    pearls = json.load(open(PEARLS, encoding="utf-8"))
    edges = {}
    for p in pearls["pearls"]:
        p["texts"] = [{"sura": s, "ayah": a, "sura_name": by_sura[s]["sura_name"] if s in by_sura else q.name(s),
                       "text": q.verse(s, a)} for s, a in p["refs"]]
        touched = sorted({by_sura[s]["id"] for s, _ in p["refs"] if s in by_sura})
        p["sites"] = touched
        if p["id"] == "P-001":
            continue  # لؤلؤة القائمة نفسها بتلمس كل المواقع؛ مش حافة علاقة
        for a, b in itertools.combinations(touched, 2):
            e = edges.setdefault((a, b), {"from": a, "to": b, "pearls": [], "statuses": []})
            e["pearls"].append(p["id"])
            e["statuses"].append(p["status"])

    data = {
        "generated_by": "lab/build.py",
        "brand": json.load(open(BRAND, encoding="utf-8")),
        "text_source": "Tanzil Quran Text (Uthmani, Version 1.1) — tanzil.net — CC BY 3.0",
        "statuses": pearls["statuses"],
        "constellations": [{k: v for k, v in c.items() if k != "test"} for c in CONSTELLATIONS],
        "sites": sites,
        "pearls": pearls["pearls"],
        "edges": list(edges.values()),
        "experiments": {k: {"id": k, "question": r["question"], "finding": r["finding"], "status": r["status"]}
                        for k, r in results.items()},
    }
    os.makedirs(os.path.dirname(WEB_DATA), exist_ok=True)
    with open(WEB_DATA, "w", encoding="utf-8") as f:
        f.write("// مولَّد آليًا من lab/build.py — لا تعدّل باليد.\nwindow.LULU = ")
        json.dump(data, f, ensure_ascii=False)
        f.write(";\n")
    data["chapters"] = [c["slug"] for c in build_chapters(q, {p["id"] for p in pearls["pearls"]})]
    return data


if __name__ == "__main__":
    d = build()
    print(f"{len(d['sites'])} موقع، {len(d['pearls'])} لؤلؤة، {len(d['edges'])} حافة، {len(d['chapters'])} فصل → web/")
