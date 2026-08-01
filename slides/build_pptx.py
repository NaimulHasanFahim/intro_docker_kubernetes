#!/usr/bin/env python3
"""
Renders slides/content.py into BOTH deliverables:

    slides/docker-k8s-intro.pptx   -> upload to Google Slides
    slides/deck.md                 -> Marp markdown

    python3 slides/build_pptx.py

No third-party packages. The .pptx is written as OOXML into a zip directly, so
this runs anywhere Python 3 does -- no pip install, no Node.

Design follows the SUST CSE Carnival 2026 site: warm cream page, deep forest
green ink, sage-green pills and rules, uppercase monospace labels, and faint
scattered code tokens behind the title and divider slides.
"""

import os
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from content import SLIDES  # noqa: E402

# ── geometry (EMU: 914400 per inch, 12700 per point) ──────────────────────────
EMU_IN = 914400
PT = 12700
W = 12192000          # 13.333in -> 16:9
H = 6858000           # 7.5in
MARGIN = 640080       # 0.7in
BODY_W = W - 2 * MARGIN
TOP = 384048
CONTENT_TOP = 1188720
BOTTOM = H - 431800

# ── palette (SUST CSE Carnival 2026) ──────────────────────────────────────────
CREAM = "F6F3E7"        # page background
INK = "1D3A1C"          # headings and body -- deep forest green
MUTED = "5C6B52"        # footnotes -- sage grey
ACCENT = "3E6B33"       # lead lines -- mid forest green
SAGE = "7F9169"         # nav-bar green: pills, rules, kickers
CODE_BG = "EAE6D5"      # code blocks -- a shade darker than the page
FAINT = "DEDACA"        # background code tokens -- barely there
DARK_BG = "1D3A1C"      # dividers -- inverted
DARK_TEXT = "F6F3E7"
DARK_SUB = "AFC0A0"
DARK_FAINT = "2A4D28"
TBL_HEAD_BG = "1D3A1C"
TBL_HEAD_FG = "F6F3E7"
TBL_ROW_A = "FCFAF2"
TBL_ROW_B = "EFEBDC"
SANS = "Arial"
MONO = "Courier New"

# ── background code tokens ────────────────────────────────────────────────────
# The carnival site scatters faint code fragments behind its hero. Ours do the
# same, but they are not random: the pool walks a SPECTRUM across the deck.
#
#   early slides  ->  systems and Docker vocabulary
#   later slides  ->  Kubernetes vocabulary
#
# and within a single slide the same drift happens bottom-to-top, so tokens near
# the floor read Docker-ish and tokens near the ceiling read Kubernetes-ish.

_FOUNDATION = [
    "syscall", "shared kernel", "namespaces", "cgroups", "PID 1", "chroot",
    "unshare(CLONE_NEWNS)", "/proc/self/ns", "union filesystem",
    "copy-on-write", "hypervisor", "guest OS", "glibc vs musl", "$PATH",
    "uname -r", "ECONNREFUSED", "127.0.0.1:5432", "0X3F3F3F3F", "O(N LOG N)",
    "SHA-256", "#!/BIN/BASH", "EXIT 0", "GIT COMMIT",
]
_DOCKER = [
    "docker build .", "FROM node:18-alpine", "WORKDIR /app",
    "COPY package.json", "RUN npm install --omit=dev", 'CMD ["node"]',
    "EXPOSE 3000", "USER node", "docker run -p 8080:3000", "docker ps -a",
    "docker exec -it sh", "docker logs -f", "layer cached", ".dockerignore",
    "multi-stage build", "docker compose up -d", "docker compose down -v",
    "image: postgres:16-alpine", "depends_on:", "healthcheck:",
    "bridge network", "named volume", "OCI image spec", "containerd", "runc",
    "overlayfs", "docker push ghcr.io/", "sha256:9f2b...", ":latest is a lie",
]
_KUBERNETES = [
    "kubectl apply -f k8s/", "apiVersion: apps/v1", "kind: Deployment",
    "metadata.labels", "selector: app=api", "replicas: 3", "spec vs status",
    "desired state", "reconcile loop", "kubectl get pods -w",
    "kubectl describe pod", "kubectl logs -f deploy/api", "ReplicaSet",
    "ClusterIP", "NodePort 30080", "svc.cluster.local", "kube-proxy",
    "kubelet", "kube-scheduler", "etcd", "controller-manager",
    "readinessProbe", "livenessProbe", "maxUnavailable: 0", "rollout undo",
    "ConfigMap", "Secret (base64!)", "PersistentVolumeClaim", "StorageClass",
    "CrashLoopBackOff", "ImagePullBackOff", "OOMKilled", "StatefulSet",
    "DaemonSet", "kubectl scale --replicas=5", "cpu: 50m", "memory: 256Mi",
]
SPECTRUM = _FOUNDATION + _DOCKER + _KUBERNETES

# (x_frac, y_frac, size_pt). Dividers and gag slides have room for a real
# scatter; content slides get three, tucked into the gutters only.
SPOTS_BIG = [
    (0.02, 0.04, 11), (0.22, 0.08, 10), (0.45, 0.03, 11), (0.66, 0.07, 10),
    (0.84, 0.03, 11), (0.01, 0.29, 10), (0.86, 0.31, 10), (0.02, 0.46, 11),
    (0.83, 0.49, 11), (0.01, 0.63, 10), (0.85, 0.66, 10), (0.04, 0.88, 11),
    (0.26, 0.93, 10), (0.48, 0.88, 11), (0.68, 0.93, 10), (0.86, 0.88, 11),
]
SPOTS_CONTENT = [(0.74, 0.012, 10), (0.05, 0.952, 10), (0.60, 0.952, 10)]

NS = ('xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
      'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
      'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"')
XML_HEAD = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'


def esc(t):
    return (str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


# ── shape builders ────────────────────────────────────────────────────────────
def run(text, size, bold=False, italic=False, color=INK, font=SANS, spc=None):
    """font=None omits the typeface, which lets emoji render in the system font."""
    face = (f'<a:latin typeface="{font}"/><a:cs typeface="{font}"/>') if font else ""
    space = f' spc="{spc}"' if spc else ""
    return (f'<a:r><a:rPr lang="en-US" sz="{size}" b="{1 if bold else 0}" '
            f'i="{1 if italic else 0}"{space} dirty="0">'
            f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill>{face}</a:rPr>'
            f'<a:t>{esc(text)}</a:t></a:r>')


def para(text, size, bold=False, italic=False, color=INK, font=SANS,
         align="l", bullet=False, spacing=100, space_before=0, spc=None):
    props = f'<a:lnSpc><a:spcPct val="{spacing * 1000}"/></a:lnSpc>'
    if space_before:
        props += f'<a:spcBef><a:spcPts val="{space_before}"/></a:spcBef>'
    if bullet:
        indent = ' marL="228600" indent="-228600"'
        props += (f'<a:buClr><a:srgbClr val="{SAGE}"/></a:buClr>'
                  '<a:buSzPct val="95000"/><a:buFont typeface="Arial"/>'
                  '<a:buChar char="▪"/>')
    else:
        indent = ' marL="0" indent="0"'
        props += '<a:buNone/>'
    body = run(text, size, bold, italic, color, font, spc) if text else ''
    return f'<a:p><a:pPr algn="{align}"{indent}>{props}</a:pPr>{body}</a:p>'


def textbox(sid, x, y, cx, cy, paras, fill=None, anchor="t"):
    fill_xml = (f'<a:solidFill><a:srgbClr val="{fill}"/></a:solidFill>'
                if fill else '<a:noFill/>')
    return (f'<p:sp><p:nvSpPr><p:cNvPr id="{sid}" name="TextBox {sid}"/>'
            f'<p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
            f'<p:spPr><a:xfrm><a:off x="{int(x)}" y="{int(y)}"/>'
            f'<a:ext cx="{int(cx)}" cy="{int(cy)}"/></a:xfrm>'
            f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>{fill_xml}</p:spPr>'
            f'<p:txBody><a:bodyPr wrap="square" lIns="91440" tIns="68580" '
            f'rIns="91440" bIns="68580" anchor="{anchor}"><a:noAutofit/></a:bodyPr>'
            f'<a:lstStyle/>{"".join(paras)}</p:txBody></p:sp>')


def bar(sid, x, y, cx, cy=41148, color=SAGE, shape="rect"):
    return (f'<p:sp><p:nvSpPr><p:cNvPr id="{sid}" name="Bar {sid}"/>'
            f'<p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
            f'<p:spPr><a:xfrm><a:off x="{int(x)}" y="{int(y)}"/>'
            f'<a:ext cx="{int(cx)}" cy="{int(cy)}"/></a:xfrm>'
            f'<a:prstGeom prst="{shape}"><a:avLst/></a:prstGeom>'
            f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill>'
            f'<a:ln><a:noFill/></a:ln></p:spPr>'
            f'<p:txBody><a:bodyPr/><a:lstStyle/><a:p/></p:txBody></p:sp>')


def pill(sid, x, y, cx, cy, text, bg=SAGE, fg="12250F"):
    """Rounded label, like the site's nav bar and buttons."""
    return (f'<p:sp><p:nvSpPr><p:cNvPr id="{sid}" name="Pill {sid}"/>'
            f'<p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
            f'<p:spPr><a:xfrm><a:off x="{int(x)}" y="{int(y)}"/>'
            f'<a:ext cx="{int(cx)}" cy="{int(cy)}"/></a:xfrm>'
            f'<a:prstGeom prst="roundRect"><a:avLst>'
            f'<a:gd name="adj" fmla="val 50000"/></a:avLst></a:prstGeom>'
            f'<a:solidFill><a:srgbClr val="{bg}"/></a:solidFill>'
            f'<a:ln><a:noFill/></a:ln></p:spPr>'
            f'<p:txBody><a:bodyPr lIns="0" rIns="0" tIns="0" bIns="0" '
            f'anchor="ctr"><a:noAutofit/></a:bodyPr><a:lstStyle/>'
            f'{para(text, 900, bold=True, color=fg, font=MONO, align="ctr", spc="180")}'
            f'</p:txBody></p:sp>')


def decor(sid, spots, progress, index, dark=False, faint=None):
    """Faint scattered code tokens, drifting Docker -> Kubernetes.

    `progress` is the slide's position through the deck (0.0 to 1.0). It picks a
    window into SPECTRUM; the spots are then filled bottom-to-top so the words
    climb from systems/Docker vocabulary at the floor towards Kubernetes at the
    ceiling. A small deterministic jitter stops neighbouring slides repeating.
    """
    out = []
    color = faint or (DARK_FAINT if dark else FAINT)
    n = len(SPECTRUM)
    span = max(10, int(n * 0.20))              # how wide a slice one slide shows
    # Slide the window so it stays fully inside the spectrum: without this the
    # first and last slides clamp against the ends and repeat the same token.
    center = span / 2 + progress * (n - 1 - span)
    k = len(spots)
    stride = span / max(1, k - 1) if k > 1 else 0

    ordered = sorted(enumerate(spots), key=lambda p: -p[1][1])  # bottom first
    for rank, (i, (fx, fy, size)) in enumerate(ordered):
        jitter = ((index * 7 + i * 13) % 5) - 2
        idx = int(round(center + (rank - (k - 1) / 2) * stride + jitter))
        tok = SPECTRUM[max(0, min(n - 1, idx))]
        out.append(textbox(sid + i, W * fx, H * fy, 3400000, 260000,
                           [para(tok, size * 100, color=color, font=MONO,
                                 spc="120")]))
    return "".join(out), sid + k


# ── flowchart primitives ──────────────────────────────────────────────────────
# Real vector boxes and arrows rather than ASCII art. Three kinds cover the
# whole deck: "flow" (ranks of boxes joined by arrows), "compare" (two labelled
# stacks side by side) and "cycle" (a loop).

BOX_FILL = "FFFFFF"
BOX_ALT = "EFEBDC"
BOX_LINE = "9BAA8B"


def box(sid, x, y, cx, cy, text, sub=None, fill=BOX_FILL, fg=INK,
        line=BOX_LINE, size=1150):
    ps = [para(text, size, bold=True, color=fg, align="ctr", spacing=95)]
    if sub:
        ps.append(para(sub, max(800, size - 250), color=fg, align="ctr",
                       spacing=95, italic=True))
    return (f'<p:sp><p:nvSpPr><p:cNvPr id="{sid}" name="Box {sid}"/>'
            f'<p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
            f'<p:spPr><a:xfrm><a:off x="{int(x)}" y="{int(y)}"/>'
            f'<a:ext cx="{int(cx)}" cy="{int(cy)}"/></a:xfrm>'
            f'<a:prstGeom prst="roundRect"><a:avLst>'
            f'<a:gd name="adj" fmla="val 12000"/></a:avLst></a:prstGeom>'
            f'<a:solidFill><a:srgbClr val="{fill}"/></a:solidFill>'
            f'<a:ln w="12700"><a:solidFill><a:srgbClr val="{line}"/>'
            f'</a:solidFill></a:ln></p:spPr>'
            f'<p:txBody><a:bodyPr lIns="45720" rIns="45720" tIns="27432" '
            f'bIns="27432" anchor="ctr"><a:noAutofit/></a:bodyPr><a:lstStyle/>'
            f'{"".join(ps)}</p:txBody></p:sp>')


def line(sid, x1, y1, x2, y2, color=SAGE, w=19050, arrow=True):
    x, y = min(x1, x2), min(y1, y2)
    cx, cy = abs(x2 - x1), abs(y2 - y1)
    flip = ''
    if x2 < x1:
        flip += ' flipH="1"'
    if y2 < y1:
        flip += ' flipV="1"'
    head = '<a:tailEnd type="triangle" w="med" len="med"/>' if arrow else ''
    return (f'<p:sp><p:nvSpPr><p:cNvPr id="{sid}" name="Conn {sid}"/>'
            f'<p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
            f'<p:spPr><a:xfrm{flip}><a:off x="{int(x)}" y="{int(y)}"/>'
            f'<a:ext cx="{int(cx)}" cy="{int(cy)}"/></a:xfrm>'
            f'<a:prstGeom prst="line"><a:avLst/></a:prstGeom>'
            f'<a:ln w="{w}"><a:solidFill><a:srgbClr val="{color}"/>'
            f'</a:solidFill>{head}</a:ln></p:spPr>'
            f'<p:txBody><a:bodyPr/><a:lstStyle/><a:p/></p:txBody></p:sp>')


def caption(sid, x, y, cx, text, size=1000, color=MUTED, align="ctr"):
    return textbox(sid, x, y, cx, 260000,
                   [para(text, size, color=color, align=align, italic=True)])


def _emph(spec):
    """Per-box styling shortcuts used by the diagram specs."""
    style = spec.get("s")
    if style == "ink":
        return dict(fill=INK, fg=DARK_TEXT, line=INK)
    if style == "sage":
        return dict(fill=SAGE, fg="12250F", line=SAGE)
    if style == "alt":
        return dict(fill=BOX_ALT, fg=INK, line=BOX_LINE)
    return {}


def draw_flow(sid, d, x, y, cx, max_h):
    """Ranks of boxes joined by arrows. dir 'down' (default) or 'right'."""
    out = []
    ranks = d["ranks"]
    labels = d.get("labels", [])
    horizontal = d.get("dir") == "right"
    note_w = int(cx * 0.26) if any(r.get("note") for r in ranks) else 0

    if horizontal:
        gap = int(cx * 0.055)
        n = len(ranks)
        bw = int((cx - gap * (n - 1)) / n)
        bh = min(int(max_h * 0.42), 640080)
        top = y + int((min(max_h, bh + 320040) - bh) / 2)
        geo = []
        for i, r in enumerate(ranks):
            bx = x + i * (bw + gap)
            b = r["boxes"][0]
            out.append(box(sid, bx, top, bw, bh, b["t"], b.get("sub"),
                           size=d.get("size", 1150), **_emph(b)))
            sid += 1
            geo.append((bx, bw))
        for i in range(len(geo) - 1):
            x1 = geo[i][0] + geo[i][1] + 27432
            x2 = geo[i + 1][0] - 27432
            out.append(line(sid, x1, top + bh // 2, x2, top + bh // 2))
            sid += 1
            if i < len(labels) and labels[i]:
                out.append(caption(sid, x1, top + bh // 2 - 280000,
                                   x2 - x1, labels[i], 900))
                sid += 1
        return "".join(out), min(max_h, bh + 320040), sid

    # vertical
    nr = len(ranks)
    arrow_gap = max(228600, int((max_h - nr * 137160) * 0.16 / max(1, nr - 1)))
    bh = int((max_h - arrow_gap * (nr - 1)) / nr)
    bh = min(bh, 640080)
    total = nr * bh + (nr - 1) * arrow_gap
    cy0 = y + max(0, int((max_h - total) / 2))
    flow_w = cx - note_w
    geo = []
    for i, r in enumerate(ranks):
        boxes = r["boxes"]
        n = len(boxes)
        gap = int(flow_w * 0.03)
        span = r.get("span", 1.0)
        avail = int(flow_w * span)
        bw = int((avail - gap * (n - 1)) / n)
        x0 = x + int((flow_w - avail) / 2)
        by = cy0 + i * (bh + arrow_gap)
        row = []
        for j, b in enumerate(boxes):
            bx = x0 + j * (bw + gap)
            out.append(box(sid, bx, by, bw, bh, b["t"], b.get("sub"),
                           size=d.get("size", 1150), **_emph(b)))
            sid += 1
            row.append((bx + bw // 2, by, bh))
        geo.append(row)
        if r.get("note"):
            out.append(textbox(sid, x + flow_w + 68580, by, note_w - 68580, bh,
                               [para(r["note"], 950, color=MUTED, italic=True,
                                     spacing=100)], anchor="ctr"))
            sid += 1

    for i in range(nr - 1):
        a, b = geo[i], geo[i + 1]
        y1 = a[0][1] + a[0][2] + 22860
        y2 = b[0][1] - 22860
        mid = (y1 + y2) // 2
        if len(a) == 1 and len(b) == 1:
            out.append(line(sid, a[0][0], y1, b[0][0], y2)); sid += 1
        elif len(a) == 1 and len(b) > 1:
            out.append(line(sid, a[0][0], y1, a[0][0], mid, arrow=False)); sid += 1
            out.append(line(sid, b[0][0], mid, b[-1][0], mid, arrow=False)); sid += 1
            for cxx, _, _ in b:
                out.append(line(sid, cxx, mid, cxx, y2)); sid += 1
        elif len(a) > 1 and len(b) == 1:
            for cxx, _, _ in a:
                out.append(line(sid, cxx, y1, cxx, mid, arrow=False)); sid += 1
            out.append(line(sid, a[0][0], mid, a[-1][0], mid, arrow=False)); sid += 1
            out.append(line(sid, b[0][0], mid, b[0][0], y2)); sid += 1
        else:
            for k in range(min(len(a), len(b))):
                out.append(line(sid, a[k][0], y1, b[k][0], y2)); sid += 1
        if i < len(labels) and labels[i]:
            out.append(caption(sid, x, mid - 190500, flow_w, labels[i], 900))
            sid += 1
    return "".join(out), total, sid


def draw_compare(sid, d, x, y, cx, max_h):
    """Two labelled stacks side by side — the VM vs container picture."""
    out = []
    gap = int(cx * 0.08)
    col_w = int((cx - gap) / 2)
    head_h = 320040
    rows_l, rows_r = d["left"]["rows"], d["right"]["rows"]
    nr = max(len(rows_l), len(rows_r))
    cap_h = 274320 if d["left"].get("caption") else 0
    bh = min(int((max_h - head_h - cap_h - 91440) / nr), 548640)
    used = head_h + nr * bh + cap_h + 91440

    for side, (col, rows) in enumerate(((d["left"], rows_l), (d["right"], rows_r))):
        cx0 = x + side * (col_w + gap)
        out.append(textbox(sid, cx0, y, col_w, head_h,
                           [para(col["title"], 1250, bold=True, color=INK,
                                 align="ctr", font=MONO, spc="120")]))
        sid += 1
        yy = y + head_h
        for r in rows:
            cells = r if isinstance(r, list) else [r]
            n = len(cells)
            g = 27432
            w = int((col_w - g * (n - 1)) / n)
            for j, c in enumerate(cells):
                txt = c["t"] if isinstance(c, dict) else c
                st = _emph(c if isinstance(c, dict) else {})
                out.append(box(sid, cx0 + j * (w + g), yy + 13716, w,
                               bh - 27432, txt, size=1050, **st))
                sid += 1
            yy += bh
        if col.get("caption"):
            out.append(caption(sid, cx0, yy + 45720, col_w, col["caption"], 1050,
                               ACCENT))
            sid += 1
    return "".join(out), used, sid


def draw_cycle(sid, d, x, y, cx, max_h):
    """Four boxes in a loop — the reconciliation diagram."""
    out = []
    nodes = d["nodes"]
    bw = int(cx * 0.34)
    bh = min(int(max_h * 0.30), 640080)
    used = min(max_h, bh * 3)
    cx_mid = x + cx // 2
    left = cx_mid - int(cx * 0.40)
    right = cx_mid + int(cx * 0.40) - bw
    top = y
    bot = y + used - bh
    pos = [(left, top), (right, top), (right, bot), (left, bot)]
    centres = []
    for i, n in enumerate(nodes[:4]):
        px, py = pos[i]
        st = _emph(n) if isinstance(n, dict) else {}
        t = n["t"] if isinstance(n, dict) else n
        sub = n.get("sub") if isinstance(n, dict) else None
        out.append(box(sid, px, py, bw, bh, t, sub, size=1100, **st))
        sid += 1
        centres.append((px, py, bw, bh))
    seq = [(0, 1), (1, 2), (2, 3), (3, 0)]
    for a, b in seq[:len(centres)]:
        ax, ay, aw, ah = centres[a]
        bx, by, bw2, bh2 = centres[b]
        if ay == by:                       # horizontal neighbour
            if ax < bx:
                out.append(line(sid, ax + aw + 22860, ay + ah // 2,
                                bx - 22860, by + bh2 // 2))
            else:
                out.append(line(sid, ax - 22860, ay + ah // 2,
                                bx + bw2 + 22860, by + bh2 // 2))
        else:                              # vertical neighbour
            if ay < by:
                out.append(line(sid, ax + aw // 2, ay + ah + 22860,
                                bx + bw2 // 2, by - 22860))
            else:
                out.append(line(sid, ax + aw // 2, ay - 22860,
                                bx + bw2 // 2, by + bh2 + 22860))
        sid += 1
    if d.get("centre"):
        out.append(textbox(sid, cx_mid - int(cx * 0.22), y + used // 2 - 160020,
                           int(cx * 0.44), 320040,
                           [para(d["centre"], 1050, color=ACCENT, align="ctr",
                                 bold=True)]))
        sid += 1
    return "".join(out), used, sid


def draw_diagram(sid, d, x, y, cx, max_h):
    kind = d.get("kind", "flow")
    if kind == "compare":
        return draw_compare(sid, d, x, y, cx, max_h)
    if kind == "cycle":
        return draw_cycle(sid, d, x, y, cx, max_h)
    return draw_flow(sid, d, x, y, cx, max_h)


def table(sid, x, y, cx, rows, col_ratio=None, size=1200):
    ncols = len(rows[0])
    ratios = col_ratio or [1.0 / ncols] * ncols
    widths = [int(cx * r) for r in ratios]
    row_h = 274320
    xml = [f'<p:graphicFrame><p:nvGraphicFramePr>'
           f'<p:cNvPr id="{sid}" name="Table {sid}"/>'
           f'<p:cNvGraphicFramePr><a:graphicFrameLocks noGrp="1"/>'
           f'</p:cNvGraphicFramePr><p:nvPr/></p:nvGraphicFramePr>'
           f'<p:xfrm><a:off x="{int(x)}" y="{int(y)}"/>'
           f'<a:ext cx="{int(cx)}" cy="{row_h * len(rows)}"/></p:xfrm>'
           f'<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/'
           f'drawingml/2006/table"><a:tbl><a:tblPr firstRow="1"/><a:tblGrid>']
    for w in widths:
        xml.append(f'<a:gridCol w="{w}"/>')
    xml.append('</a:tblGrid>')
    for i, r in enumerate(rows):
        xml.append(f'<a:tr h="{row_h}">')
        for cell in r:
            mono = cell.startswith("`") and cell.endswith("`")
            p = para(cell.strip("`"), size, bold=(i == 0),
                     color=TBL_HEAD_FG if i == 0 else INK,
                     font=MONO if mono else SANS)
            bg = TBL_HEAD_BG if i == 0 else (TBL_ROW_A if i % 2 else TBL_ROW_B)
            xml.append(f'<a:tc><a:txBody><a:bodyPr lIns="82296" rIns="82296" '
                       f'tIns="41148" bIns="41148" anchor="ctr"/><a:lstStyle/>{p}'
                       f'</a:txBody><a:tcPr><a:solidFill>'
                       f'<a:srgbClr val="{bg}"/></a:solidFill></a:tcPr></a:tc>')
        xml.append('</a:tr>')
    xml.append('</a:tbl></a:graphicData></a:graphic></p:graphicFrame>')
    return "".join(xml), row_h * len(rows)


# ── slide rendering ───────────────────────────────────────────────────────────
def render_slide(spec, index, total=1):
    shapes = []
    sid = 2
    kind = spec.get("type")
    dark = kind in ("section", "gag")
    progress = index / max(1, total - 1)
    bg = (f'<p:bg><p:bgPr><a:solidFill>'
          f'<a:srgbClr val="{DARK_BG if dark else CREAM}"/>'
          f'</a:solidFill><a:effectLst/></p:bgPr></p:bg>')

    # ── big slides: title, section divider, visual gag ───────────────────────
    if kind in ("title", "section", "gag"):
        d, sid = decor(sid, SPOTS_BIG, progress, index, dark=dark)
        shapes.append(d)

        if kind == "gag":
            shapes.append(textbox(sid, MARGIN, int(H * 0.16), BODY_W, 2200000,
                                  [para(spec["emoji"], 12000, align="ctr",
                                        font=None, color=DARK_TEXT)]))
            sid += 1
            shapes.append(textbox(sid, MARGIN, int(H * 0.62), BODY_W, 1000000,
                                  [para(spec["title"], 2600, bold=True,
                                        color=DARK_TEXT, align="ctr")]))
            sid += 1
            if spec.get("punchline"):
                shapes.append(textbox(sid, MARGIN, int(H * 0.78), BODY_W, 800000,
                                      [para(spec["punchline"], 1500,
                                            color=DARK_SUB, align="ctr",
                                            spacing=120)]))
            return bg, "".join(shapes)

        if kind == "section":
            shapes.append(pill(sid, (W - 1600200) // 2, int(H * 0.22),
                               1600200, 274320, "CHAPTER",
                               bg=SAGE, fg="12250F"))
            sid += 1

        big = 4000 if kind == "title" else 3200
        color = DARK_TEXT if dark else INK
        shapes.append(textbox(sid, MARGIN, int(H * 0.33), BODY_W, 1200000,
                              [para(spec["title"], big, bold=True,
                                    color=color, align="ctr")]))
        sid += 1
        shapes.append(bar(sid, (W - 914400) // 2, int(H * 0.33) + 1160000,
                          914400, 41148, SAGE))
        sid += 1
        if spec.get("subtitle"):
            subs = [para(line, 1500, color=DARK_SUB if dark else MUTED,
                         align="ctr", spacing=130)
                    for line in spec["subtitle"].split("\n")]
            shapes.append(textbox(sid, MARGIN, int(H * 0.33) + 1300000,
                                  BODY_W, 1100000, subs))
        return bg, "".join(shapes)

    # ── content slide ────────────────────────────────────────────────────────
    # A lighter scatter here: three tokens, in the gutters only, so nothing
    # ever sits behind the reading text.
    d, sid = decor(sid, SPOTS_CONTENT, progress, index, faint="E6E2D2")
    shapes.append(d)

    shapes.append(textbox(sid, MARGIN, TOP, BODY_W, 640080,
                          [para(spec["title"], 2200, bold=True)]))
    sid += 1
    shapes.append(bar(sid, MARGIN + 91440, TOP + 594360, 731520))
    sid += 1

    y = CONTENT_TOP
    foot_h = 480060 if spec.get("footnote") else 0
    limit = BOTTOM - foot_h

    # An emoji on a content slide sits to the right; text keeps the left 78%.
    text_w = BODY_W
    if spec.get("emoji"):
        text_w = int(BODY_W * 0.79)
        shapes.append(textbox(sid, MARGIN + text_w, CONTENT_TOP,
                              BODY_W - text_w, 1600000,
                              [para(spec["emoji"], 5400, align="ctr",
                                    font=None)]))
        sid += 1

    if spec.get("lead"):
        h = 411480
        shapes.append(textbox(sid, MARGIN, y, text_w, h,
                              [para(spec["lead"], 1500, bold=True,
                                    color=ACCENT, spacing=115)]))
        sid += 1
        y += h

    if spec.get("bullets"):
        size = spec.get("bullet_size", 1500)
        line = int(size * 1.58 * PT / 100)
        h = min(limit - y, len(spec["bullets"]) * line + 137160)
        ps = [para(b, size, bullet=True, spacing=105, space_before=500)
              for b in spec["bullets"]]
        shapes.append(textbox(sid, MARGIN, y, text_w, h, ps))
        sid += 1
        y += h + 91440

    if spec.get("code"):
        size = spec.get("code_size", 1050)
        lines = spec["code"].split("\n")
        line = int(size * 1.30 * PT / 100)
        h = min(limit - y, len(lines) * line + 182880)
        ps = [para(l, size, font=MONO, spacing=100) for l in lines]
        shapes.append(textbox(sid, MARGIN, y, BODY_W, h, ps, fill=CODE_BG))
        sid += 1
        y += h + 91440

    if spec.get("diagram"):
        xml, dh, sid = draw_diagram(sid, spec["diagram"], MARGIN, y, BODY_W,
                                    limit - y)
        shapes.append(xml)
        y += dh + 91440

    if spec.get("table"):
        xml, th = table(sid, MARGIN, y, BODY_W, spec["table"],
                        spec.get("col_ratio"), spec.get("bullet_size", 1200))
        shapes.append(xml)
        sid += 1
        y += th + 91440

    if spec.get("footnote"):
        shapes.append(bar(sid, MARGIN, BOTTOM - 441480, BODY_W, 12700, "D8D4C2"))
        sid += 1
        shapes.append(textbox(sid, MARGIN, BOTTOM - 411480, BODY_W, 411480,
                              [para(spec["footnote"], 1150, italic=True,
                                    color=MUTED, spacing=110)]))
    return bg, "".join(shapes)


def slide_xml(spec, index, total):
    bg, shapes = render_slide(spec, index, total)
    return (XML_HEAD + f'<p:sld {NS}><p:cSld>{bg}<p:spTree>'
            '<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/>'
            '</p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/>'
            '<a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/>'
            f'</a:xfrm></p:grpSpPr>{shapes}</p:spTree></p:cSld>'
            '<p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>')


def notes_xml(text):
    return (XML_HEAD + f'<p:notes {NS}><p:cSld><p:spTree>'
            '<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/>'
            '</p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/>'
            '<a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/>'
            '</a:xfrm></p:grpSpPr>'
            '<p:sp><p:nvSpPr><p:cNvPr id="2" name="Notes Placeholder 1"/>'
            '<p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>'
            '<p:nvPr><p:ph type="body" idx="1"/></p:nvPr></p:nvSpPr><p:spPr/>'
            '<p:txBody><a:bodyPr/><a:lstStyle/>'
            f'<a:p><a:r><a:rPr lang="en-US" dirty="0"/><a:t>{esc(text)}</a:t>'
            '</a:r></a:p></p:txBody></p:sp>'
            '</p:spTree></p:cSld>'
            '<p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:notes>')


# ── static parts ──────────────────────────────────────────────────────────────
CLR_MAP = ('<p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" '
           'accent2="accent2" accent3="accent3" accent4="accent4" '
           'accent5="accent5" accent6="accent6" hlink="hlink" '
           'folHlink="folHlink"/>')

THEME = XML_HEAD + '''<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="NSU">
<a:themeElements>
<a:clrScheme name="NSU"><a:dk1><a:sysClr val="windowText" lastClr="000000"/></a:dk1>
<a:lt1><a:sysClr val="window" lastClr="FFFFFF"/></a:lt1>
<a:dk2><a:srgbClr val="1D3A1C"/></a:dk2><a:lt2><a:srgbClr val="F6F3E7"/></a:lt2>
<a:accent1><a:srgbClr val="3E6B33"/></a:accent1><a:accent2><a:srgbClr val="7F9169"/></a:accent2>
<a:accent3><a:srgbClr val="D9A441"/></a:accent3><a:accent4><a:srgbClr val="B5533C"/></a:accent4>
<a:accent5><a:srgbClr val="5C6B52"/></a:accent5><a:accent6><a:srgbClr val="EAE6D5"/></a:accent6>
<a:hlink><a:srgbClr val="3E6B33"/></a:hlink><a:folHlink><a:srgbClr val="7F9169"/></a:folHlink></a:clrScheme>
<a:fontScheme name="NSU"><a:majorFont><a:latin typeface="Arial"/><a:ea typeface=""/><a:cs typeface=""/></a:majorFont>
<a:minorFont><a:latin typeface="Arial"/><a:ea typeface=""/><a:cs typeface=""/></a:minorFont></a:fontScheme>
<a:fmtScheme name="NSU">
<a:fillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
<a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
<a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:fillStyleLst>
<a:lnStyleLst><a:ln w="9525"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:prstDash val="solid"/></a:ln>
<a:ln w="19050"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:prstDash val="solid"/></a:ln>
<a:ln w="28575"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:prstDash val="solid"/></a:ln></a:lnStyleLst>
<a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle><a:effectStyle><a:effectLst/></a:effectStyle>
<a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst>
<a:bgFillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
<a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
<a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:bgFillStyleLst>
</a:fmtScheme></a:themeElements><a:objectDefaults/><a:extraClrSchemeLst/></a:theme>'''

EMPTY_TREE = ('<p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/>'
              '<p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/>'
              '<a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/>'
              '</a:xfrm></p:grpSpPr></p:spTree>')

_LVL = ('<a:lvl1pPr><a:defRPr sz="1800"><a:solidFill>'
        f'<a:srgbClr val="{INK}"/></a:solidFill>'
        f'<a:latin typeface="{SANS}"/></a:defRPr></a:lvl1pPr>')

SLIDE_MASTER = (XML_HEAD + f'<p:sldMaster {NS}><p:cSld><p:bg><p:bgPr>'
                f'<a:solidFill><a:srgbClr val="{CREAM}"/></a:solidFill>'
                f'<a:effectLst/></p:bgPr></p:bg>{EMPTY_TREE}</p:cSld>{CLR_MAP}'
                '<p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/>'
                f'</p:sldLayoutIdLst><p:txStyles><p:titleStyle>{_LVL}</p:titleStyle>'
                f'<p:bodyStyle>{_LVL}</p:bodyStyle>'
                f'<p:otherStyle>{_LVL}</p:otherStyle></p:txStyles></p:sldMaster>')

SLIDE_LAYOUT = (XML_HEAD + f'<p:sldLayout {NS} type="blank" preserve="1">'
                f'<p:cSld name="Blank">{EMPTY_TREE}</p:cSld>'
                '<p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sldLayout>')

NOTES_MASTER = (XML_HEAD + f'<p:notesMaster {NS}><p:cSld>{EMPTY_TREE}</p:cSld>'
                f'{CLR_MAP}<p:notesStyle/></p:notesMaster>')

PRES_PROPS = XML_HEAD + f'<p:presentationPr {NS}/>'
VIEW_PROPS = XML_HEAD + f'<p:viewPr {NS}/>'

CORE_PROPS = (XML_HEAD + '<cp:coreProperties xmlns:cp="http://schemas.openxml'
              'formats.org/package/2006/metadata/core-properties" '
              'xmlns:dc="http://purl.org/dc/elements/1.1/" '
              'xmlns:dcterms="http://purl.org/dc/terms/" '
              'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
              '<dc:title>Docker &amp; Kubernetes — Intro Session</dc:title>'
              '<dc:creator>NSU Session</dc:creator>'
              '<cp:lastModifiedBy>NSU Session</cp:lastModifiedBy>'
              '</cp:coreProperties>')

APP_PROPS = (XML_HEAD + '<Properties xmlns="http://schemas.openxmlformats.org/'
             'officeDocument/2006/extended-properties" xmlns:vt="http://schemas'
             '.openxmlformats.org/officeDocument/2006/docPropsVTypes">'
             '<Application>build_pptx.py</Application></Properties>')

TABLE_STYLES = (XML_HEAD + '<a:tblStyleLst xmlns:a="http://schemas.openxml'
                'formats.org/drawingml/2006/main" '
                'def="{5C22544A-7EE6-4342-B048-85BDC9FD1C3A}"/>')

OFF = "officeDocument/2006/relationships"


def rels(items):
    body = "".join(
        f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/'
        f'{typ}" Target="{tgt}"/>' for rid, typ, tgt in items)
    return (XML_HEAD + '<Relationships xmlns="http://schemas.openxmlformats.org'
            f'/package/2006/relationships">{body}</Relationships>')


def build_pptx(path, slides):
    n = len(slides)
    noted = [i for i, s in enumerate(slides) if s.get("notes")]
    z = zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED)

    ct = [XML_HEAD, '<Types xmlns="http://schemas.openxmlformats.org/package/'
          '2006/content-types">',
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats'
          '-package.relationships+xml"/>',
          '<Default Extension="xml" ContentType="application/xml"/>']
    for part, typ in [
            ("/ppt/presentation.xml", "presentationml.presentation.main"),
            ("/ppt/slideMasters/slideMaster1.xml", "presentationml.slideMaster"),
            ("/ppt/slideLayouts/slideLayout1.xml", "presentationml.slideLayout"),
            ("/ppt/notesMasters/notesMaster1.xml", "presentationml.notesMaster"),
            ("/ppt/presProps.xml", "presentationml.presProps"),
            ("/ppt/viewProps.xml", "presentationml.viewProps"),
            ("/ppt/tableStyles.xml", "presentationml.tableStyles"),
            ("/ppt/theme/theme1.xml", "theme"),
            ("/ppt/theme/theme2.xml", "theme")]:
        ct.append(f'<Override PartName="{part}" ContentType="application/vnd.'
                  f'openxmlformats-officedocument.{typ}+xml"/>')
    ct.append('<Override PartName="/docProps/core.xml" ContentType="application/'
              'vnd.openxmlformats-package.core-properties+xml"/>')
    ct.append('<Override PartName="/docProps/app.xml" ContentType="application/'
              'vnd.openxmlformats-officedocument.extended-properties+xml"/>')
    for i in range(n):
        ct.append(f'<Override PartName="/ppt/slides/slide{i+1}.xml" ContentType='
                  '"application/vnd.openxmlformats-officedocument.'
                  'presentationml.slide+xml"/>')
    for i in noted:
        ct.append(f'<Override PartName="/ppt/notesSlides/notesSlide{i+1}.xml" '
                  'ContentType="application/vnd.openxmlformats-officedocument.'
                  'presentationml.notesSlide+xml"/>')
    ct.append('</Types>')
    z.writestr("[Content_Types].xml", "".join(ct))

    z.writestr("_rels/.rels", rels([
        ("rId1", f"{OFF}/officeDocument", "ppt/presentation.xml"),
        ("rId2", "package/2006/relationships/metadata/core-properties",
         "docProps/core.xml"),
        ("rId3", f"{OFF}/extended-properties", "docProps/app.xml")]))
    z.writestr("docProps/core.xml", CORE_PROPS)
    z.writestr("docProps/app.xml", APP_PROPS)

    sld_ids = "".join(f'<p:sldId id="{256+i}" r:id="rId{2+i}"/>' for i in range(n))
    nm_rid = f"rId{n+2}"
    z.writestr("ppt/presentation.xml", XML_HEAD +
               f'<p:presentation {NS}>'
               '<p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/>'
               '</p:sldMasterIdLst>'
               f'<p:notesMasterIdLst><p:notesMasterId r:id="{nm_rid}"/>'
               '</p:notesMasterIdLst>'
               f'<p:sldIdLst>{sld_ids}</p:sldIdLst>'
               f'<p:sldSz cx="{W}" cy="{H}"/>'
               f'<p:notesSz cx="{H}" cy="{W}"/></p:presentation>')

    pres_rels = [("rId1", f"{OFF}/slideMaster", "slideMasters/slideMaster1.xml")]
    for i in range(n):
        pres_rels.append((f"rId{2+i}", f"{OFF}/slide", f"slides/slide{i+1}.xml"))
    pres_rels += [(nm_rid, f"{OFF}/notesMaster", "notesMasters/notesMaster1.xml"),
                  (f"rId{n+3}", f"{OFF}/presProps", "presProps.xml"),
                  (f"rId{n+4}", f"{OFF}/viewProps", "viewProps.xml"),
                  (f"rId{n+5}", f"{OFF}/tableStyles", "tableStyles.xml"),
                  (f"rId{n+6}", f"{OFF}/theme", "theme/theme1.xml")]
    z.writestr("ppt/_rels/presentation.xml.rels", rels(pres_rels))

    z.writestr("ppt/presProps.xml", PRES_PROPS)
    z.writestr("ppt/viewProps.xml", VIEW_PROPS)
    z.writestr("ppt/tableStyles.xml", TABLE_STYLES)
    z.writestr("ppt/theme/theme1.xml", THEME)
    z.writestr("ppt/theme/theme2.xml", THEME)

    z.writestr("ppt/slideMasters/slideMaster1.xml", SLIDE_MASTER)
    z.writestr("ppt/slideMasters/_rels/slideMaster1.xml.rels", rels([
        ("rId1", f"{OFF}/slideLayout", "../slideLayouts/slideLayout1.xml"),
        ("rId2", f"{OFF}/theme", "../theme/theme1.xml")]))
    z.writestr("ppt/slideLayouts/slideLayout1.xml", SLIDE_LAYOUT)
    z.writestr("ppt/slideLayouts/_rels/slideLayout1.xml.rels", rels([
        ("rId1", f"{OFF}/slideMaster", "../slideMasters/slideMaster1.xml")]))
    z.writestr("ppt/notesMasters/notesMaster1.xml", NOTES_MASTER)
    z.writestr("ppt/notesMasters/_rels/notesMaster1.xml.rels", rels([
        ("rId1", f"{OFF}/theme", "../theme/theme2.xml")]))

    for i, spec in enumerate(slides):
        k = i + 1
        z.writestr(f"ppt/slides/slide{k}.xml", slide_xml(spec, i, n))
        r = [("rId1", f"{OFF}/slideLayout", "../slideLayouts/slideLayout1.xml")]
        if spec.get("notes"):
            r.append(("rId2", f"{OFF}/notesSlide",
                      f"../notesSlides/notesSlide{k}.xml"))
            z.writestr(f"ppt/notesSlides/notesSlide{k}.xml",
                       notes_xml(spec["notes"]))
            z.writestr(f"ppt/notesSlides/_rels/notesSlide{k}.xml.rels", rels([
                ("rId1", f"{OFF}/notesMaster", "../notesMasters/notesMaster1.xml"),
                ("rId2", f"{OFF}/slide", f"../slides/slide{k}.xml")]))
        z.writestr(f"ppt/slides/_rels/slide{k}.xml.rels", rels(r))
    z.close()


# ── markdown (Marp) export ────────────────────────────────────────────────────
MARP_HEAD = f"""---
marp: true
theme: default
paginate: true
size: 16:9
header: "Docker & Kubernetes — NSU Intro Session"
style: |
  /* Palette from the SUST CSE Carnival 2026 site. Generated by build_pptx.py --
     edit slides/content.py and re-run, do not hand-edit this file. */
  :root {{
    --cream: #{CREAM.lower()};
    --ink: #{INK.lower()};
    --muted: #{MUTED.lower()};
    --accent: #{ACCENT.lower()};
    --sage: #{SAGE.lower()};
    --codebg: #{CODE_BG.lower()};
  }}
  section {{ font-size: 26px; background: var(--cream); color: var(--ink); }}
  section h1 {{ color: var(--ink); }}
  section h1 + p strong {{ color: var(--accent); }}
  header, footer, section::after {{ color: var(--muted); font-family: monospace; }}
  code {{ background: var(--codebg); color: var(--ink); font-size: .85em; }}
  pre {{ background: var(--codebg); font-size: .72em; line-height: 1.35; }}
  pre code {{ background: transparent; }}
  ul li::marker {{ color: var(--sage); }}
  blockquote {{ border-left: 5px solid var(--sage); color: var(--muted); font-size: .8em; }}
  table {{ font-size: .78em; }}
  th {{ background: var(--ink); color: var(--cream); }}
  tr:nth-child(even) td {{ background: #efebdc; }}
  a {{ color: var(--accent); }}
  section.lead {{ background: var(--ink); color: var(--cream); text-align: center; }}
  section.lead h1 {{ font-size: 54px; color: var(--cream); }}
  section.lead p {{ color: #afc0a0; }}
  section.lead .emoji {{ font-size: 150px; line-height: 1.1; }}
  .kicker {{ font-family: monospace; letter-spacing: .18em; font-size: .6em;
             background: var(--sage); color: #12250f; padding: .2em .9em;
             border-radius: 999px; }}
---
"""


def md_diagram(d):
    """Diagrams degrade to Mermaid in the markdown deck."""
    kind = d.get("kind", "flow")

    def nid(r, i):
        return f"n{r}_{i}"

    def lbl(b):
        t = b["t"] if isinstance(b, dict) else b
        sub = b.get("sub") if isinstance(b, dict) else None
        return (t + (f"<br/><i>{sub}</i>" if sub else "")).replace('"', "'")

    if kind == "compare":
        rows = [["", d["left"]["title"], d["right"]["title"]]]
        lr, rr = d["left"]["rows"], d["right"]["rows"]
        for i in range(max(len(lr), len(rr))):
            def cell(rs):
                if i >= len(rs):
                    return ""
                r = rs[i]
                cells = r if isinstance(r, list) else [r]
                return " · ".join(c["t"] if isinstance(c, dict) else c
                                  for c in cells)
            rows.append([str(i + 1), cell(lr), cell(rr)])
        out = md_table(rows)
        caps = [c.get("caption") for c in (d["left"], d["right"]) if c.get("caption")]
        return out + ("\n\n" + "  |  ".join(caps) if caps else "")

    if kind == "cycle":
        lines = ["```mermaid", "flowchart LR"]
        ns = d["nodes"]
        for i, n in enumerate(ns):
            lines.append(f'  c{i}["{lbl(n)}"]')
        for i in range(len(ns)):
            lines.append(f"  c{i} --> c{(i + 1) % len(ns)}")
        lines.append("```")
        return "\n".join(lines)

    direction = "LR" if d.get("dir") == "right" else "TB"
    lines = ["```mermaid", f"flowchart {direction}"]
    ranks = d["ranks"]
    for r, rank in enumerate(ranks):
        for i, b in enumerate(rank["boxes"]):
            lines.append(f'  {nid(r, i)}["{lbl(b)}"]')
    labels = d.get("labels", [])
    for r in range(len(ranks) - 1):
        a, b = ranks[r]["boxes"], ranks[r + 1]["boxes"]
        tag = f'|{labels[r]}|' if r < len(labels) and labels[r] else ""
        if len(a) == len(b) and len(a) > 1:
            for i in range(len(a)):
                lines.append(f"  {nid(r, i)} -->{tag} {nid(r + 1, i)}")
        else:
            for i in range(len(a)):
                for j in range(len(b)):
                    lines.append(f"  {nid(r, i)} -->{tag} {nid(r + 1, j)}")
    lines.append("```")
    notes = [f"*{r['note']}*" for r in ranks if r.get("note")]
    return "\n".join(lines) + ("\n\n" + " · ".join(notes) if notes else "")


def md_table(rows):
    out = ["| " + " | ".join(rows[0]) + " |",
           "|" + "|".join(["---"] * len(rows[0])) + "|"]
    for r in rows[1:]:
        out.append("| " + " | ".join(c.replace("|", "\\|") for c in r) + " |")
    return "\n".join(out)


def build_markdown(path, slides):
    out = [MARP_HEAD]
    for spec in slides:
        kind = spec.get("type")
        s = ["\n---\n"]
        if kind in ("title", "section", "gag"):
            s.append("<!-- _class: lead -->\n")
        if kind == "gag":
            s.append(f'<p class="emoji">{spec["emoji"]}</p>\n')
            s.append(f'# {spec["title"]}\n')
            if spec.get("punchline"):
                s.append(f'{spec["punchline"]}\n')
        else:
            if kind == "section":
                s.append('<span class="kicker">CHAPTER</span>\n')
            s.append(f'# {spec["title"]}\n')
            if spec.get("subtitle"):
                s.append("\n".join(spec["subtitle"].split("\n")) + "\n")
            if spec.get("lead"):
                s.append(f'**{spec["lead"]}**\n')
            if spec.get("emoji"):
                s.append(f'<span style="font-size:2.2em">{spec["emoji"]}</span>\n')
            if spec.get("bullets"):
                s.append("\n".join(f"- {b}" for b in spec["bullets"]) + "\n")
            if spec.get("code"):
                s.append("```\n" + spec["code"] + "\n```\n")
            if spec.get("diagram"):
                s.append(md_diagram(spec["diagram"]) + "\n")
            if spec.get("table"):
                s.append(md_table(spec["table"]) + "\n")
            if spec.get("footnote"):
                s.append(f'> {spec["footnote"]}\n')
        if spec.get("notes"):
            s.append(f'\n<!--\nSpeaker notes: {spec["notes"]}\n-->\n')
        out.append("\n".join(s))
    with open(path, "w", encoding="utf-8") as f:
        f.write("".join(out))


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    lean = "--lean" in sys.argv
    slides = [s for s in SLIDES if s.get("lean", True)] if lean else SLIDES
    suffix = "-lean" if lean else ""
    pptx = os.path.join(here, f"docker-k8s-intro{suffix}.pptx")
    md = os.path.join(here, f"deck{suffix}.md")

    build_pptx(pptx, slides)
    build_markdown(md, slides)

    kinds = {}
    for s in slides:
        kinds[s.get("type", "content")] = kinds.get(s.get("type", "content"), 0) + 1
    droppable = sum(1 for s in SLIDES if not s.get("lean", True))
    print(f"{len(slides)} slides {kinds}"
          f"{'   [lean build]' if lean else f'   (--lean drops {droppable} -> {len(SLIDES) - droppable})'}")
    print(f"  {pptx}  ({os.path.getsize(pptx) // 1024} KB)")
    print(f"  {md}  ({os.path.getsize(md) // 1024} KB)")
