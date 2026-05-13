"""
v2 – Fixed layout: no overlaps, clean vertical boxes, neutral source system color.
"""

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from lxml import etree

INPUT  = "/Users/ratnadeep.bose/Downloads/Epredia Temp Doc/Presentation5.pptx"
OUTPUT = "/Users/ratnadeep.bose/Downloads/Epredia Temp Doc/Epredia_Future_State_Architecture.pptx"

# ── Palette ───────────────────────────────────────────────────────────────────
C_NAVY    = RGBColor(0x1E, 0x27, 0x61)
C_TEAL    = RGBColor(0x02, 0x80, 0x90)
C_TEAL_DK = RGBColor(0x02, 0x50, 0x70)
C_GOLD    = RGBColor(0xE8, 0x9A, 0x0C)
C_GREEN   = RGBColor(0x1A, 0x7A, 0x4A)
C_SRC     = RGBColor(0x60, 0x68, 0x78)   # neutral slate-gray for source systems
C_SRC_BDR = RGBColor(0x90, 0x98, 0xAA)
C_WHITE   = RGBColor(0xFF, 0xFF, 0xFF)
C_OFFWHT  = RGBColor(0xF0, 0xF4, 0xFF)
C_ICE     = RGBColor(0xDC, 0xEC, 0xF8)
C_SECBAR  = RGBColor(0x36, 0x45, 0x4F)
C_DARK    = RGBColor(0x1A, 0x1A, 0x2A)


# ── Helpers ───────────────────────────────────────────────────────────────────
def add_rect(slide, l, t, w, h, fill, border=None, bpt=1.5, rounded=False):
    shape = slide.shapes.add_shape(1, Inches(l), Inches(t), Inches(w), Inches(h))
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    if border:
        shape.line.color.rgb = border
        shape.line.width = Pt(bpt)
    else:
        shape.line.fill.background()
    if rounded:
        sp = shape.element
        spPr = sp.find(qn("p:spPr"))
        pg = spPr.find(qn("a:prstGeom"))
        if pg is not None:
            pg.attrib["prst"] = "roundRect"
            av = pg.find(qn("a:avLst"))
            if av is None:
                av = etree.SubElement(pg, qn("a:avLst"))
            gd = etree.SubElement(av, qn("a:gd"))
            gd.set("name", "adj")
            gd.set("fmla", "val 25000")
    return shape


def txt(shape, text, sz=9, bold=False, color=C_WHITE, align=PP_ALIGN.CENTER):
    tf = shape.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = align
    r = p.add_run()
    r.text = text
    r.font.size = Pt(sz)
    r.font.bold = bold
    r.font.color.rgb = color


def lbl(slide, l, t, w, h, text, sz=7.5, bold=False,
        color=C_DARK, align=PP_ALIGN.CENTER):
    shape = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    tf = shape.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = align
    r = p.add_run()
    r.text = text
    r.font.size = Pt(sz)
    r.font.bold = bold
    r.font.color.rgb = color
    return shape


def arrow(slide, x1, y1, x2, y2, color=C_NAVY, wpt=1.5):
    x1e, y1e = int(Inches(x1)), int(Inches(y1))
    x2e, y2e = int(Inches(x2)), int(Inches(y2))
    ox, oy = min(x1e, x2e), min(y1e, y2e)
    cw = max(abs(x2e - x1e), 1)
    ch = max(abs(y2e - y1e), 1)
    lx1, ly1 = x1e - ox, y1e - oy
    lx2, ly2 = x2e - ox, y2e - oy
    clr = str(color)
    we = int(Pt(wpt).pt * 12700)
    xml = f"""<p:sp xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
      xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
      xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <p:nvSpPr><p:cNvPr id="9998" name="arr"/><p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr><p:nvPr/></p:nvSpPr>
  <p:spPr>
    <a:xfrm><a:off x="{ox}" y="{oy}"/><a:ext cx="{cw}" cy="{ch}"/></a:xfrm>
    <a:prstGeom prst="line"><a:avLst/></a:prstGeom>
    <a:ln w="{we}"><a:solidFill><a:srgbClr val="{clr}"/></a:solidFill><a:tailEnd type="arrow"/></a:ln>
  </p:spPr>
  <p:txBody><a:bodyPr/><a:lstStyle/><a:p/></p:txBody>
</p:sp>"""
    slide.shapes._spTree.append(etree.fromstring(xml))


# ── Slide setup ───────────────────────────────────────────────────────────────
prs = Presentation(INPUT)
slide = prs.slides.add_slide(prs.slide_layouts[6])   # blank

# ── Grid constants ────────────────────────────────────────────────────────────
# Columns (x, width)
C1x, C1w = 0.10, 2.15   # Source Systems
C2x, C2w = 2.35, 1.95   # Incorta Connectors
SQL_x    = 4.35          # SQL label zone center (gap = 4.30–4.65)
C3x, C3w = 4.65, 4.20   # Incorta (central)
PY_x     = 8.92          # Python/SQL label zone center (gap = 8.90–9.25)
C4x, C4w = 9.25, 3.95   # Consumption & AI

# Rows
Y_TITLE   = 0.00;  H_TITLE  = 0.48
Y_HEADER  = 0.52;  H_HEADER = 0.30
Y_CONTENT = 0.90;  H_CONTENT = 6.20   # 0.90 → 7.10
Y_SEC     = 7.12;  H_SEC    = 0.30

# ── Background ────────────────────────────────────────────────────────────────
add_rect(slide, 0, 0, 13.33, 7.5, C_OFFWHT)

# ── Title bar ──────────────────────────────────────────────────────────────────
add_rect(slide, 0, Y_TITLE, 13.33, H_TITLE, C_NAVY)
lbl(slide, 0.18, 0.06, 12.80, 0.36,
    "Epredia  |  Future State Data Architecture  —  Incorta as Central Platform",
    sz=13, bold=True, color=C_WHITE, align=PP_ALIGN.LEFT)

# ── Column headers ─────────────────────────────────────────────────────────────
for x, w, label in [
    (C1x, C1w, "SOURCE SYSTEMS"),
    (C2x, C2w, "INCORTA CONNECTORS"),
    (C3x, C3w, "INCORTA  (Central Platform)"),
    (C4x, C4w, "CONSUMPTION & AI"),
]:
    b = add_rect(slide, x, Y_HEADER, w, H_HEADER, C_NAVY, rounded=True)
    txt(b, label, sz=7.5, bold=True, color=C_WHITE)

# ── Source system boxes (5 rows, evenly distributed) ─────────────────────────
SRC_ITEMS = [
    "ERP\n(SAP)",
    "CRM\n(Salesforce /\nServiceMax)",
    "Internal Data\n(SharePoint)",
    "Files & APIs\n(External Data)",
    "Email\nAttachments",
]
N_SRC   = len(SRC_ITEMS)
SRC_H   = 0.92                                        # box height
SRC_GAP = (H_CONTENT - N_SRC * SRC_H) / (N_SRC - 1) # even gap

src_y = []
for i, label in enumerate(SRC_ITEMS):
    y = Y_CONTENT + i * (SRC_H + SRC_GAP)
    src_y.append(y)
    b = add_rect(slide, C1x, y, C1w, SRC_H, C_SRC, C_SRC_BDR, bpt=1.2, rounded=True)
    txt(b, label, sz=9, bold=True, color=C_WHITE)

# ── Incorta connector boxes (same y as source boxes) ──────────────────────────
CON_ITEMS = [
    "SAP Connector\n(Marketplace)",
    "Salesforce Connector\n(Marketplace)",
    "SharePoint Connector\n(Marketplace)",
    "REST / API Connector\n(Python Script)",
    "Power Automate\n→ SharePoint\n→ Incorta",
]
for i, label in enumerate(CON_ITEMS):
    y = src_y[i]
    b = add_rect(slide, C2x, y, C2w, SRC_H, C_TEAL, C_WHITE, bpt=1.0, rounded=True)
    txt(b, label, sz=8.5, bold=False, color=C_WHITE)

# ── Consumption boxes (4 rows, evenly distributed in same height band) ────────
CONS_ITEMS = [
    "Dashboards &\nSelf-Service BI",
    "Power BI\nReports & Dashboard",
    "AgentForce\n(Salesforce AI)",
    "Salesforce\nAPI Integration",
]
N_CON    = len(CONS_ITEMS)
CON_H    = SRC_H
# Space the 4 boxes evenly across the same H_CONTENT band
CON_GAP  = (H_CONTENT - N_CON * CON_H) / (N_CON - 1)

cons_y = []
for i, label in enumerate(CONS_ITEMS):
    y = Y_CONTENT + i * (CON_H + CON_GAP)
    cons_y.append(y)
    b = add_rect(slide, C4x, y, C4w, CON_H, C_NAVY, C_ICE, bpt=1.2, rounded=True)
    txt(b, label, sz=9, bold=True, color=C_WHITE)

# ── Incorta central box (full height) ────────────────────────────────────────
add_rect(slide, C3x, Y_CONTENT, C3w, H_CONTENT, C_WHITE, C_TEAL, bpt=2.0, rounded=True)

# Incorta title strip
title_strip = add_rect(slide, C3x + 0.08, Y_CONTENT + 0.07, C3w - 0.16, 0.40, C_TEAL, rounded=True)
txt(title_strip, "INCORTA", sz=13, bold=True, color=C_WHITE)

# ── ACDC Schema sub-box ───────────────────────────────────────────────────────
AX = C3x + 0.12
AY = Y_CONTENT + 0.57
AW = C3w - 0.24
AH = 2.55

add_rect(slide, AX, AY, AW, AH, C_ICE, C_NAVY, bpt=1.5, rounded=True)
lbl(slide, AX + 0.08, AY + 0.06, AW - 0.16, 0.26,
    "ACDC Schema", sz=9, bold=True, color=C_NAVY, align=PP_ALIGN.CENTER)

# Raw Data Tables
rdt = add_rect(slide, AX + 0.12, AY + 0.38, AW - 0.24, 0.50, C_NAVY, C_WHITE, bpt=0.8, rounded=True)
txt(rdt, "Raw Data Tables", sz=9, bold=True, color=C_WHITE)

# Golden Record & Customer Hierarchy — side by side NEW boxes
NW = (AW - 0.36) / 2
NY = AY + 1.02
# Golden Record
gr = add_rect(slide, AX + 0.12, NY, NW, 0.65, C_GREEN, C_WHITE, bpt=1.2, rounded=True)
txt(gr, "Golden\nRecord", sz=9, bold=True, color=C_WHITE)
lbl(slide, AX + 0.12, NY - 0.22, NW, 0.22, "★ NEW", sz=7.5, bold=True, color=C_GREEN, align=PP_ALIGN.CENTER)

# Customer Hierarchy
ch_x = AX + 0.12 + NW + 0.12
ch = add_rect(slide, ch_x, NY, NW, 0.65, C_GREEN, C_WHITE, bpt=1.2, rounded=True)
txt(ch, "Customer\nHierarchy", sz=9, bold=True, color=C_WHITE)
lbl(slide, ch_x, NY - 0.22, NW, 0.22, "★ NEW", sz=7.5, bold=True, color=C_GREEN, align=PP_ALIGN.CENTER)

# Python label below new boxes
lbl(slide, AX + 0.08, NY + 0.70, AW - 0.16, 0.22,
    "Populated via Python Script / PySpark",
    sz=7.5, bold=False, color=C_TEAL, align=PP_ALIGN.CENTER)

# ── Business Schema ────────────────────────────────────────────────────────────
BS_Y = AY + AH + 0.22
bs = add_rect(slide, C3x + 0.12, BS_Y, C3w - 0.24, 0.52, C_NAVY, C_WHITE, bpt=0.8, rounded=True)
txt(bs, "Business Schema  (SQL Views & Transformations)", sz=9, bold=True, color=C_WHITE)

# ── Materialized Views ─────────────────────────────────────────────────────────
MV_Y = BS_Y + 0.68
mv = add_rect(slide, C3x + 0.12, MV_Y, C3w - 0.24, 0.52, C_TEAL_DK, C_WHITE, bpt=0.8, rounded=True)
txt(mv, "Materialized Views  (PySpark / SQL)", sz=9, bold=True, color=C_WHITE)

# ── Presentation Tier ─────────────────────────────────────────────────────────
PT_Y = MV_Y + 0.70
pt = add_rect(slide, C3x + 0.12, PT_Y, C3w - 0.24, 0.52, C_TEAL, C_WHITE, bpt=0.8, rounded=True)
txt(pt, "Incorta Presentation Tier", sz=9, bold=True, color=C_WHITE)

# ── Security bar ──────────────────────────────────────────────────────────────
sec = add_rect(slide, 0.10, Y_SEC, 13.13, H_SEC, C_SECBAR)
txt(sec, "🔒  Security  ·  Governance  ·  Data Lineage  ·  Metadata Management",
    sz=8.5, bold=False, color=C_WHITE)

# ── Arrows: Source → Connector ────────────────────────────────────────────────
for i in range(N_SRC):
    y_mid = src_y[i] + SRC_H / 2
    arrow(slide, C1x + C1w, y_mid, C2x, y_mid, color=C_SRC, wpt=1.2)

# ── Arrows: Connector → Incorta  +  SQL labels ───────────────────────────────
for i in range(N_SRC):
    y_mid = src_y[i] + SRC_H / 2
    arrow(slide, C2x + C2w, y_mid, C3x, y_mid, color=C_TEAL, wpt=1.5)
    # SQL badge on the gap
    lbl(slide, SQL_x - 0.20, y_mid - 0.26, 0.42, 0.20,
        "SQL", sz=6.5, bold=True, color=C_GOLD, align=PP_ALIGN.CENTER)

# ── Arrows: Incorta → Consumption  +  Python/SQL labels ──────────────────────
for i in range(N_CON):
    y_mid = cons_y[i] + CON_H / 2
    arrow(slide, C3x + C3w, y_mid, C4x, y_mid, color=C_NAVY, wpt=1.5)
    lbl(slide, PY_x - 0.22, y_mid - 0.26, 0.55, 0.20,
        "SQL/Py", sz=6.0, bold=True, color=C_GOLD, align=PP_ALIGN.CENTER)

# ── Internal Incorta vertical flow arrows ─────────────────────────────────────
mid_x = C3x + C3w / 2
# ACDC bottom → Business Schema top
arrow(slide, mid_x, AY + AH, mid_x, BS_Y, color=C_TEAL, wpt=1.2)
# Business Schema → Materialized Views
arrow(slide, mid_x, BS_Y + 0.52, mid_x, MV_Y, color=C_TEAL, wpt=1.2)
# Materialized Views → Presentation Tier
arrow(slide, mid_x, MV_Y + 0.52, mid_x, PT_Y, color=C_TEAL, wpt=1.2)

# ── Save ──────────────────────────────────────────────────────────────────────
prs.save(OUTPUT)
print(f"Saved → {OUTPUT}")
