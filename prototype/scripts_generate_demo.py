from __future__ import annotations

import csv
import json
import math
import random
from dataclasses import asdict, dataclass
from email.message import EmailMessage
from pathlib import Path
from typing import Any

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "demo-data" / "generated"
OUT.mkdir(parents=True, exist_ok=True)

random.seed(42)

# ---------- Canonical RFx ----------
plants = ["Bengaluru Plant 1", "Bengaluru Plant 2", "Hosur Plant"]

item_defs = [
    ("BX-5P-450-300-250", "5-ply RSC box 450x300x250 mm", 5, 18, 0.365),
    ("BX-5P-500-350-300", "5-ply RSC box 500x350x300 mm", 5, 18, 0.455),
    ("BX-5P-600-400-350", "5-ply RSC box 600x400x350 mm", 5, 20, 0.610),
    ("BX-5P-420-320-280", "5-ply die-cut box 420x320x280 mm", 5, 18, 0.390),
    ("BX-5P-380-280-220", "5-ply RSC box 380x280x220 mm", 5, 16, 0.285),
    ("BX-5P-550-380-320", "5-ply RSC box 550x380x320 mm", 5, 20, 0.530),
    ("BX-5P-480-330-260", "5-ply RSC box 480x330x260 mm", 5, 18, 0.420),
    ("BX-5P-650-450-400", "5-ply heavy-duty box 650x450x400 mm", 5, 22, 0.760),
    ("BX-5P-440-310-240", "5-ply printed box 440x310x240 mm", 5, 18, 0.375),
    ("BX-5P-520-360-290", "5-ply RSC box 520x360x290 mm", 5, 18, 0.480),
    ("BX-3P-300-200-150", "3-ply RSC box 300x200x150 mm", 3, 16, 0.155),
    ("BX-3P-350-250-180", "3-ply RSC box 350x250x180 mm", 3, 16, 0.195),
    ("BX-3P-400-300-200", "3-ply RSC box 400x300x200 mm", 3, 16, 0.240),
    ("BX-3P-280-180-120", "3-ply mailer box 280x180x120 mm", 3, 14, 0.125),
    ("BX-3P-450-320-220", "3-ply RSC box 450x320x220 mm", 3, 16, 0.285),
    ("BX-3P-320-220-160", "3-ply RSC box 320x220x160 mm", 3, 16, 0.170),
    ("BX-3P-380-260-180", "3-ply printed box 380x260x180 mm", 3, 16, 0.215),
    ("BX-3P-500-350-250", "3-ply RSC box 500x350x250 mm", 3, 18, 0.335),
    ("DV-5P-450-280", "5-ply corrugated divider 450x280 mm", 5, 18, 0.105),
    ("DV-5P-520-320", "5-ply corrugated divider 520x320 mm", 5, 18, 0.135),
    ("DV-3P-350-220", "3-ply corrugated divider 350x220 mm", 3, 16, 0.062),
    ("DV-3P-420-260", "3-ply corrugated divider 420x260 mm", 3, 16, 0.078),
    ("PD-3P-300-200", "3-ply corrugated pad 300x200 mm", 3, 16, 0.052),
    ("PD-5P-450-300", "5-ply corrugated pad 450x300 mm", 5, 18, 0.118),
    ("SH-5P-1000-800", "5-ply corrugated sheet 1000x800 mm", 5, 18, 0.410),
    ("SH-5P-1200-900", "5-ply corrugated sheet 1200x900 mm", 5, 20, 0.535),
    ("SH-3P-900-600", "3-ply corrugated sheet 900x600 mm", 3, 16, 0.245),
    ("SH-3P-1100-700", "3-ply corrugated sheet 1100x700 mm", 3, 16, 0.330),
    ("SL-5P-500-60", "5-ply corrugated sleeve 500x60 mm", 5, 18, 0.084),
    ("SL-3P-420-50", "3-ply corrugated sleeve 420x50 mm", 3, 16, 0.049),
]

rfx_items: list[dict[str, Any]] = []
for i, (sku, desc, ply, bf, weight) in enumerate(item_defs, 1):
    qty = 18000 + ((i * 7300) % 82000)
    qty = int(round((qty * 1.55) / 1000) * 1000)
    base = round((weight * (48 if ply == 5 else 42)) + (2.2 if sku.startswith("BX") else 0.8), 2)
    plant = plants[(i - 1) % len(plants)]
    rfx_items.append({
        "line_no": i,
        "sku": sku,
        "description": desc,
        "annual_quantity": qty,
        "uom": "piece",
        "unit_weight_kg": weight,
        "ply": ply,
        "min_burst_factor": bf,
        "delivery_location": plant,
        "baseline_unit_price_inr": round(base * (1.055 + ((i % 4) - 1.5) * 0.008), 2),
        "target_delivery_days": 14 if i <= 24 else 18,
    })

questionnaire = [
    {"id": "Q1", "question": "ISO 9001 certification valid through contract term?", "type": "yes_no", "mandatory": True},
    {"id": "Q2", "question": "FSC or PEFC Chain-of-Custody certification available?", "type": "yes_no", "mandatory": True},
    {"id": "Q3", "question": "Can you meet the minimum burst factor specified per line?", "type": "yes_no", "mandatory": True},
    {"id": "Q4", "question": "Average recycled fibre content (%)", "type": "number", "mandatory": False, "minimum": 70},
    {"id": "Q5", "question": "Manufacturing plant within 500 km of Bengaluru?", "type": "yes_no", "mandatory": False},
    {"id": "Q6", "question": "Standard delivery lead time (calendar days)", "type": "number", "mandatory": True, "maximum": 21},
    {"id": "Q7", "question": "Can you provide batch-wise COA on request?", "type": "yes_no", "mandatory": False},
    {"id": "Q8", "question": "Any minimum order quantity constraints beyond RFx quantities?", "type": "text", "mandatory": False},
]

rfx = {
    "event_id": "RFX-CORR-2027-001",
    "title": "FY27 Corrugated Packaging - South India Plants",
    "category": "Corrugated Packaging",
    "buyer": "Priya Menon",
    "currency": "INR",
    "comparison_uom": "piece",
    "bid_due_date": "2026-09-30",
    "expected_annual_spend_inr": round(sum(x["annual_quantity"] * x["baseline_unit_price_inr"] for x in rfx_items), 2),
    "scope": "Annual supply of corrugated boxes, dividers, pads, sheets and sleeves to Bengaluru and Hosur plants.",
    "commercial_rules": {
        "comparison_basis": "landed_cost_excluding_gst",
        "fx_rate_usd_inr": 83.20,
        "freight_required": True,
        "gst_excluded_from_comparison": True,
        "quote_validity_days": 60,
    },
    "items": rfx_items,
    "questionnaire": questionnaire,
}

# ---------- Vendor truth generation ----------
vendor_profiles = [
    {
        "id": "packright", "name": "PackRight Industries", "format": "xlsx", "quality": "pass", "lead": 12,
        "iso": True, "fsc": True, "bf": True, "recycled": 82, "nearby": True, "coa": True,
        "mult": 0.974, "freight_mode": "included", "freight_per_piece": 0.0,
    },
    {
        "id": "corrpro", "name": "CorrPro International", "format": "pdf", "quality": "pass", "lead": 14,
        "iso": True, "fsc": True, "bf": True, "recycled": 76, "nearby": False, "coa": True,
        "mult": 0.955, "freight_mode": "included", "freight_per_piece": 0.0,
    },
    {
        "id": "boxworks", "name": "BoxWorks India Pvt Ltd", "format": "docx", "quality": "pending", "lead": 10,
        "iso": True, "fsc": True, "bf": True, "recycled": 88, "nearby": True, "coa": True,
        "mult": 0.945, "freight_mode": "extra_flat", "freight_per_piece": 0.32,
    },
    {
        "id": "alphapack", "name": "AlphaPack Solutions", "format": "jpg", "quality": "fail", "lead": 11,
        "iso": True, "fsc": False, "bf": True, "recycled": 72, "nearby": True, "coa": False,
        "mult": 0.905, "freight_mode": "included", "freight_per_piece": 0.0,
    },
    {
        "id": "greencarton", "name": "GreenCarton Co.", "format": "eml", "quality": "pass", "lead": 16,
        "iso": True, "fsc": True, "bf": True, "recycled": 91, "nearby": True, "coa": True,
        "mult": 0.965, "freight_mode": "extra_percent", "freight_per_piece": None,
    },
]

truth: dict[str, Any] = {"dataset_version": 1, "rfx": rfx, "vendors": {}, "evidence": {}, "exceptions": []}

# Utility pricing

def vendor_piece_price(item: dict[str, Any], profile: dict[str, Any]) -> float:
    # deterministic, vendor/item-level price variation
    wobble = 1 + (((item["line_no"] * (len(profile["id"]) + 3)) % 9) - 4) * 0.004
    return round(item["baseline_unit_price_inr"] * profile["mult"] * wobble, 2)


def evidence_id(vendor: str, line: int, kind: str = "price") -> str:
    return f"EV-{vendor.upper()}-{line:02d}-{kind.upper()}"

for p in vendor_profiles:
    vlines = []
    for item in rfx_items:
        if p["id"] == "boxworks" and item["line_no"] in {7, 19, 28}:
            vlines.append({"line_no": item["line_no"], "sku": item["sku"], "quote_status": "not_quoted"})
            continue
        # GreenCarton leaves 4 explicit lines as "same as last year"
        if p["id"] == "greencarton" and item["line_no"] in {6, 13, 21, 29}:
            vlines.append({
                "line_no": item["line_no"], "sku": item["sku"], "quote_status": "quoted",
                "raw_basis": "same_as_last_year", "normalized_piece_price_inr": item["baseline_unit_price_inr"],
                "landed_piece_price_inr": round(item["baseline_unit_price_inr"] * 1.02, 2),
            })
            continue
        piece = vendor_piece_price(item, p)
        if p["id"] == "packright":
            basis = "piece" if item["line_no"] % 4 else "100_piece"
            raw = piece if basis == "piece" else round(piece * 100, 2)
            currency = "INR"
            freight = 0
        elif p["id"] == "corrpro":
            basis = "100_piece"
            raw = round(piece * 100 / rfx["commercial_rules"]["fx_rate_usd_inr"], 2)
            currency = "USD"
            freight = 0
        elif p["id"] == "boxworks":
            # mix per carton and per piece. Carton pack sizes are explicitly given.
            basis = "carton" if item["line_no"] % 3 != 0 else "piece"
            pack_size = 50 if item["ply"] == 5 else 100
            raw = round(piece * pack_size, 2) if basis == "carton" else piece
            currency = "INR"
            freight = p["freight_per_piece"]
        elif p["id"] == "alphapack":
            basis = "bundle" if item["line_no"] in {19, 20, 21, 22, 23, 24, 29, 30} else "piece"
            pack_size = 25 if basis == "bundle" else 1
            raw = round(piece * pack_size, 2)
            currency = "INR"
            freight = 0
        else:
            # Vendor E quotes family rates per kg, not per SKU, for most lines.
            basis = "kg"
            kg_rate = round(piece / item["unit_weight_kg"], 2)
            raw = kg_rate
            currency = "INR"
            freight = round(piece * 0.02, 2)
        landed = round(piece + freight, 2)
        vlines.append({
            "line_no": item["line_no"], "sku": item["sku"], "quote_status": "quoted",
            "raw_basis": basis, "raw_price": raw, "raw_currency": currency,
            "normalized_piece_price_inr": piece, "landed_piece_price_inr": landed,
            "pack_size": (50 if item["ply"] == 5 else 100) if p["id"] == "boxworks" and basis == "carton" else (25 if p["id"] == "alphapack" and basis == "bundle" else None),
        })
    truth["vendors"][p["id"]] = {
        **p,
        "questionnaire": {"Q1": p["iso"], "Q2": p["fsc"], "Q3": p["bf"], "Q4": p["recycled"], "Q5": p["nearby"], "Q6": p["lead"], "Q7": p["coa"], "Q8": "None beyond quoted pack size"},
        "lines": vlines,
    }

# ---------- Build RFx workbook/reference ----------
def style_header(ws, row: int, start: int, end: int, fill="17324D"):
    for c in range(start, end + 1):
        cell = ws.cell(row=row, column=c)
        cell.fill = PatternFill("solid", fgColor=fill)
        cell.font = Font(color="FFFFFF", bold=True)
        cell.alignment = Alignment(vertical="center", wrap_text=True)

wb = Workbook()
ws = wb.active
ws.title = "RFx Items"
headers = ["Line", "SKU", "Description", "Annual Qty", "UOM", "Unit Wt kg", "Ply", "Min BF", "Delivery Location", "Baseline INR/pc", "Target Days"]
ws.append(headers)
style_header(ws, 1, 1, len(headers))
for item in rfx_items:
    ws.append([item["line_no"], item["sku"], item["description"], item["annual_quantity"], item["uom"], item["unit_weight_kg"], item["ply"], item["min_burst_factor"], item["delivery_location"], item["baseline_unit_price_inr"], item["target_delivery_days"]])
ws.freeze_panes = "A2"
for col, width in {"A":7,"B":22,"C":42,"D":14,"E":10,"F":12,"G":8,"H":10,"I":22,"J":16,"K":13}.items(): ws.column_dimensions[col].width=width
for row in ws.iter_rows(min_row=2):
    for cell in row: cell.alignment=Alignment(vertical="center", wrap_text=True)

qws = wb.create_sheet("Questionnaire")
qws.append(["ID", "Question", "Type", "Mandatory", "Rule"])
style_header(qws, 1, 1, 5)
for q in questionnaire:
    rule = f">= {q['minimum']}" if "minimum" in q else (f"<= {q['maximum']}" if "maximum" in q else "")
    qws.append([q["id"], q["question"], q["type"], "Yes" if q["mandatory"] else "No", rule])
qws.column_dimensions["A"].width=8; qws.column_dimensions["B"].width=62; qws.column_dimensions["C"].width=14; qws.column_dimensions["D"].width=12; qws.column_dimensions["E"].width=12

terms = wb.create_sheet("Commercial Rules")
terms.append(["Field", "Value"]); style_header(terms,1,1,2)
for k,v in rfx["commercial_rules"].items(): terms.append([k, v])
terms.column_dimensions["A"].width=34; terms.column_dimensions["B"].width=34
wb.save(OUT / "buyer_rfx_reference.xlsx")

# ---------- Vendor A Excel ----------
p = truth["vendors"]["packright"]
wb = Workbook(); ws = wb.active; ws.title="Commercial Offer"
ws["A1"]="PACKRIGHT INDUSTRIES - FY27 COMMERCIAL OFFER"; ws.merge_cells("A1:I1")
ws["A1"].font=Font(size=16,bold=True,color="FFFFFF"); ws["A1"].fill=PatternFill("solid",fgColor="1E5A78"); ws["A1"].alignment=Alignment(horizontal="center")
ws.append(["Our Ref", "Customer SKU", "Item Description", "Qty", "Quote Basis", "Pack Qty", "Rate (INR)", "Lead Days", "Remarks"])
style_header(ws,2,1,9,"244A64")
for line in p["lines"]:
    item=rfx_items[line["line_no"]-1]
    basis=line["raw_basis"]
    ws.append([f"PR-{line['line_no']:03d}", item["sku"], item["description"], item["annual_quantity"], "INR / pc" if basis=="piece" else "INR / 100 pcs", 1 if basis=="piece" else 100, line["raw_price"], p["lead"], "Freight included; GST extra"])
for col,w in zip(range(1,10),[12,22,42,13,15,10,14,11,30]): ws.column_dimensions[get_column_letter(col)].width=w
ws.freeze_panes="A3"
for row in ws.iter_rows(min_row=3):
    for c in row: c.alignment=Alignment(vertical="center",wrap_text=True)
terms=wb.create_sheet("Terms")
terms.append(["Term", "Offer"]); style_header(terms,1,1,2,"244A64")
for kv in [("Validity","60 days"),("Freight","Included to listed plants"),("GST","Extra as applicable"),("Payment","45 days from invoice"),("Annual rebate","None")]: terms.append(kv)
q=wb.create_sheet("Quality")
q.append(["Question", "Response"]); style_header(q,1,1,2,"244A64")
for qq in questionnaire: q.append([qq["question"], str(p["questionnaire"][qq["id"]])])
wb.save(OUT / "vendor_a_packright_offer.xlsx")

# ---------- Vendor B PDF ----------
p = truth["vendors"]["corrpro"]
pdf_path = OUT / "vendor_b_corrpro_quote.pdf"
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name="Small", parent=styles["BodyText"], fontSize=8, leading=10))
styles.add(ParagraphStyle(name="Tiny", parent=styles["BodyText"], fontSize=7, leading=9, textColor=colors.HexColor("#444444")))
doc=SimpleDocTemplate(str(pdf_path),pagesize=A4,rightMargin=12*mm,leftMargin=12*mm,topMargin=13*mm,bottomMargin=12*mm)
story=[]
story.append(Paragraph("<b>CORRPRO INTERNATIONAL</b>", styles["Title"]))
story.append(Paragraph("Commercial Proposal | FY27 South India Corrugated Packaging", styles["Heading2"]))
story.append(Paragraph("Quote Ref: CPI/IND/9271 &nbsp;&nbsp; Currency: USD &nbsp;&nbsp; Incoterm: DDP Bengaluru/Hosur", styles["Small"]))
story.append(Spacer(1,5*mm))
rows=[["#","Customer SKU","Description","Qty","USD / 100 pcs","Lead"]]
for line in p["lines"]:
    item=rfx_items[line["line_no"]-1]
    rows.append([line["line_no"], item["sku"], item["description"], f"{item['annual_quantity']:,}", f"{line['raw_price']:.2f}", f"{p['lead']}d"])
    if len(rows)==17:
        t=Table(rows,colWidths=[8*mm,36*mm,68*mm,22*mm,28*mm,14*mm],repeatRows=1)
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#1f3d5a')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),7),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f5f7f9')]),('GRID',(0,0),(-1,-1),0.25,colors.HexColor('#c7ced4')),('LEFTPADDING',(0,0),(-1,-1),3),('RIGHTPADDING',(0,0),(-1,-1),3),('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),3)]))
        story += [t, PageBreak()]
        rows=[["#","Customer SKU","Description","Qty","USD / 100 pcs","Lead"]]
if len(rows)>1:
    t=Table(rows,colWidths=[8*mm,36*mm,68*mm,22*mm,28*mm,14*mm],repeatRows=1)
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#1f3d5a')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),7),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f5f7f9')]),('GRID',(0,0),(-1,-1),0.25,colors.HexColor('#c7ced4')),('LEFTPADDING',(0,0),(-1,-1),3),('RIGHTPADDING',(0,0),(-1,-1),3),('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),3)]))
    story.append(t)
story.append(Spacer(1,4*mm))
story.append(Paragraph("<b>Commercial notes</b>", styles["Heading3"]))
story.append(Paragraph("Prices are DDP to the delivery locations listed in the RFx. Taxes are excluded. Offer valid for 60 days.", styles["Small"]))
# Deliberately bury material commercial condition in tiny footnote.
story.append(Spacer(1,2*mm))
story.append(Paragraph("* Footnote: A 3.0% year-end volume rebate applies only if aggregate awarded annual value exceeds USD 350,000. Rebate is retrospective and is not reflected in the unit rates above.", styles["Tiny"]))
story.append(Paragraph("Quality: ISO 9001 valid; FSC CoC valid; all quoted grades meet stated burst factor. Average recycled fibre content 76%. Standard lead time 14 calendar days.", styles["Small"]))
doc.build(story)

# ---------- Vendor C DOCX ----------
p = truth["vendors"]["boxworks"]
d = Document(); sec=d.sections[0]; sec.orientation=WD_ORIENT.LANDSCAPE; sec.page_width=Inches(11); sec.page_height=Inches(8.5); sec.top_margin=Inches(.55); sec.bottom_margin=Inches(.55); sec.left_margin=Inches(.55); sec.right_margin=Inches(.55)
title=d.add_paragraph(); title.alignment=WD_ALIGN_PARAGRAPH.CENTER
r=title.add_run("BOXWORKS INDIA PVT LTD\nCommercial Offer - FY27 Corrugated Packaging"); r.bold=True; r.font.size=Pt(16); r.font.color.rgb=RGBColor(32,67,92)
p0=d.add_paragraph("Thank you for the opportunity. We have quoted 27 of the 30 requested lines. Our commercial offer uses our normal carton pack sizes rather than your template.")
p0.style=d.styles['Normal']
table=d.add_table(rows=1, cols=7); table.style='Table Grid'
hdr=table.rows[0].cells
for i,h in enumerate(["Line","SKU","Description","Quote basis","Pack size","Rate INR","Lead"]):
    hdr[i].text=h; hdr[i].vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
    for rr in hdr[i].paragraphs[0].runs: rr.bold=True
for line in p["lines"]:
    if line["quote_status"]=="not_quoted": continue
    item=rfx_items[line["line_no"]-1]
    cells=table.add_row().cells
    vals=[line["line_no"],item["sku"],item["description"],"per carton" if line["raw_basis"]=="carton" else "per piece",line.get("pack_size") or 1,f"₹{line['raw_price']:.2f}",f"{p['lead']} days"]
    for i,v in enumerate(vals): cells[i].text=str(v); cells[i].vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
for par in d.paragraphs: par.paragraph_format.space_after=Pt(6)
d.add_heading("Commercial terms", level=2)
d.add_paragraph("Freight is extra at ₹0.32 per piece for all quoted items, irrespective of destination. GST is extra. Payment requested within 30 days. Quote validity is 45 days.")
d.add_paragraph("Lines 7, 19 and 28 are not offered because our current tooling does not support these dimensions. These should be treated as not quoted, not zero-price lines.")
d.add_heading("Quality response", level=2)
d.add_paragraph("We are ISO 9001 certified, hold FSC Chain-of-Custody certification and confirm compliance with the minimum burst-factor requirements. Recycled fibre content averages 88%. Bengaluru manufacturing plant is within 40 km. Lead time is typically 10 calendar days. Batch COA can be supplied. The FSC certificate renewal is in process; current certificate expires 15 October 2026, before the proposed contract start date.")
d.save(OUT / "vendor_c_boxworks_offer.docx")

# ---------- Vendor D angled phone photo ----------
p = truth["vendors"]["alphapack"]
W,H=1900,2400
img=Image.new("RGB",(W,H),"#f8f5ed"); draw=ImageDraw.Draw(img)
try:
    f_title=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",42)
    f_head=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",24)
    f=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",21)
    f_small=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",18)
except Exception:
    f_title=f_head=f=f_small=None

draw.text((95,65),"ALPHAPACK SOLUTIONS",font=f_title,fill="#222222")
draw.text((95,125),"RATE CARD - CORRUGATED PACKAGING / SEPT 2026",font=f_head,fill="#333333")
draw.text((95,175),"Prices INR. Freight included. GST extra. Lead: 11 days.",font=f,fill="#333333")
colx=[90,160,520,1250,1500,1700]
for x in colx: draw.line((x,230,x,2070),fill="#8b8b8b",width=2)
for y in [230,285]+[285+i*56 for i in range(1,31)]+[2070]: draw.line((90,y,1810,y),fill="#a0a0a0",width=2)
headers=["#","SKU","DESCRIPTION","BASIS","RATE","PACK"]
for x,h in zip([105,175,535,1265,1515,1712],headers): draw.text((x,240),h,font=f_head,fill="#111111")
for idx,line in enumerate(p["lines"],1):
    item=rfx_items[line["line_no"]-1]; y=295+(idx-1)*56
    basis="bundle" if line["raw_basis"]=="bundle" else "piece"
    rate=line["raw_price"]
    # intentionally ambiguous high-impact line 18 by drawing a smudged digit later
    rate_txt=f"{rate:.2f}"
    draw.text((105,y),str(idx),font=f,fill="#222")
    draw.text((175,y),item["sku"],font=f_small,fill="#222")
    desc=item["description"][:42]
    draw.text((535,y),desc,font=f_small,fill="#222")
    draw.text((1265,y),basis,font=f_small,fill="#222")
    draw.text((1515,y),rate_txt,font=f,fill="#222")
    draw.text((1712,y),str(line.get("pack_size") or 1),font=f,fill="#222")
# Smudge line 18 price area to lower legibility
line18_y=295+17*56
smudge=Image.new("RGBA",(180,45),(255,255,255,0)); sd=ImageDraw.Draw(smudge); sd.rectangle((15,9,145,28),fill=(120,120,120,80)); sd.line((5,30,160,8),fill=(80,80,80,90),width=5)
img.paste(smudge,(1495,line18_y),smudge)
draw.text((95,2115),"QUALITY DECLARATION",font=f_head,fill="#222")
draw.text((95,2160),"ISO 9001: YES   |   FSC/PEFC: NO   |   BF compliance: YES",font=f,fill="#222")
draw.text((95,2200),"Recycled fibre: 72% | COA: Not standard | MOQ: quoted pack size",font=f,fill="#222")
# simulate phone photo: rotation + perspective-like skew + slight blur/contrast
img=img.rotate(3.2,expand=True,fillcolor="#c8c3b8")
img=ImageEnhance.Contrast(img).enhance(0.93).filter(ImageFilter.GaussianBlur(radius=0.45))
img.save(OUT / "vendor_d_alphapack_rate_card_photo.jpg",quality=82)

# ---------- Vendor E email ----------
p = truth["vendors"]["greencarton"]
msg=EmailMessage(); msg["From"]="sales@greencarton.example"; msg["To"]="priya.buyer@example.com"; msg["Subject"]="Re: FY27 corrugated packaging - commercial reply"
# Build concise but dense family-style email; explicit same-as-last-year lines.
lines=[]
for line in p["lines"]:
    item=rfx_items[line["line_no"]-1]
    if line.get("raw_basis")=="same_as_last_year":
        lines.append(f"L{line['line_no']} {item['sku']}: same as last year")
    else:
        lines.append(f"L{line['line_no']} {item['sku']}: ₹{line['raw_price']:.2f}/kg")
body=("Hi Priya,\n\nWe can support the FY27 requirement. Rather than filling the sheet, below are our rates. "
      "All are INR/kg against the unit weights in your RFQ; for the four lines marked 'same as last year', please retain FY26 rate. "
      "Freight is extra at 2% of material value. GST extra. Standard lead time 16 days.\n\n" + "\n".join(lines) +
      "\n\nQuality: ISO 9001 yes; FSC CoC yes; BF specs yes; recycled fibre approx 91%; plant at Hosur; COA available. No extra MOQ beyond practical dispatch pack.\n\nRegards,\nNikhil\nGreenCarton Co.")
msg.set_content(body)
(OUT / "vendor_e_greencarton_reply.eml").write_bytes(msg.as_bytes())
(OUT / "vendor_e_greencarton_reply.txt").write_text(body,encoding="utf-8")

# ---------- Evidence and exceptions ----------
# Add source refs per vendor/line for UI; references are intentionally human-readable and stable.
for vid,v in truth["vendors"].items():
    for line in v["lines"]:
        if line["quote_status"]=="not_quoted":
            continue
        ln=line["line_no"]; item=rfx_items[ln-1]; eid=evidence_id(vid,ln)
        if vid=="packright":
            ref={"type":"xlsx","file":"vendor_a_packright_offer.xlsx","sheet":"Commercial Offer","cell_range":f"B{ln+2}:I{ln+2}","source_text":f"{item['sku']} | {line['raw_basis']} | INR {line['raw_price']}"}
        elif vid=="corrpro":
            page=1 if ln<=15 else 2
            ref={"type":"pdf","file":"vendor_b_corrpro_quote.pdf","page":page,"source_text":f"{item['sku']} | USD {line['raw_price']} / 100 pcs"}
        elif vid=="boxworks":
            ref={"type":"docx","file":"vendor_c_boxworks_offer.docx","table":"Pricing table","row":ln,"source_text":f"{item['sku']} | {line['raw_basis']} | INR {line['raw_price']}"}
        elif vid=="alphapack":
            y=295+(ln-1)*56
            ref={"type":"image","file":"vendor_d_alphapack_rate_card_photo.jpg","bbox":[1490,y-5,1710,y+40],"source_text":f"{item['sku']} | {line['raw_basis']} | INR {line['raw_price']}"}
        else:
            src=(f"L{ln} {item['sku']}: same as last year" if line.get("raw_basis")=="same_as_last_year" else f"L{ln} {item['sku']}: ₹{line['raw_price']:.2f}/kg")
            ref={"type":"email","file":"vendor_e_greencarton_reply.eml","source_text":src}
        truth["evidence"][eid]=ref
        line["evidence_id"]=eid

# Exceptions intentionally exercise different classes
truth["exceptions"] = [
    {"id":"EX-001","vendor_id":"alphapack","line_no":18,"severity":"critical","type":"low_confidence_visual","title":"Rate digit obscured in phone photo","detail":"Line 18 price is partially smudged; verify against source before use.","financial_exposure_inr":round(rfx_items[17]["annual_quantity"]*truth["vendors"]["alphapack"]["lines"][17]["landed_piece_price_inr"],2),"status":"needs_review","evidence_id":evidence_id("alphapack",18)},
    {"id":"EX-002","vendor_id":"boxworks","line_no":7,"severity":"high","type":"missing_quote","title":"Line 7 not quoted","detail":"Supplier explicitly declined this line due to tooling limitations.","financial_exposure_inr":round(rfx_items[6]["annual_quantity"]*rfx_items[6]["baseline_unit_price_inr"],2),"status":"clarification_required","evidence_id":None},
    {"id":"EX-003","vendor_id":"boxworks","line_no":19,"severity":"high","type":"missing_quote","title":"Line 19 not quoted","detail":"Supplier explicitly declined this line due to tooling limitations.","financial_exposure_inr":round(rfx_items[18]["annual_quantity"]*rfx_items[18]["baseline_unit_price_inr"],2),"status":"clarification_required","evidence_id":None},
    {"id":"EX-004","vendor_id":"boxworks","line_no":28,"severity":"medium","type":"missing_quote","title":"Line 28 not quoted","detail":"Supplier explicitly declined this line due to tooling limitations.","financial_exposure_inr":round(rfx_items[27]["annual_quantity"]*rfx_items[27]["baseline_unit_price_inr"],2),"status":"clarification_required","evidence_id":None},
    {"id":"EX-005","vendor_id":"corrpro","line_no":0,"severity":"medium","type":"conditional_discount","title":"3% volume rebate buried in footnote","detail":"Rebate applies only if aggregate annual award exceeds USD 350,000 and is not included in unit rates.","financial_exposure_inr":round(sum(i["annual_quantity"]*l["landed_piece_price_inr"] for i,l in zip(rfx_items, truth["vendors"]["corrpro"]["lines"])) * .03,2),"status":"needs_review","evidence_id":None},
    {"id":"EX-006","vendor_id":"boxworks","line_no":0,"severity":"high","type":"certificate_expiry","title":"FSC certificate expires before contract start","detail":"Supplier states renewal is in process. Qualification remains pending until renewed certificate is verified.","financial_exposure_inr":round(sum(i["annual_quantity"]*(l.get("landed_piece_price_inr") or 0) for i,l in zip(rfx_items, truth["vendors"]["boxworks"]["lines"])),2),"status":"blocking","evidence_id":None},
    {"id":"EX-007","vendor_id":"alphapack","line_no":0,"severity":"critical","type":"qualification_failure","title":"Mandatory FSC/PEFC requirement failed","detail":"Supplier explicitly states FSC/PEFC: NO.","financial_exposure_inr":round(sum(i["annual_quantity"]*(l.get("landed_piece_price_inr") or 0) for i,l in zip(rfx_items, truth["vendors"]["alphapack"]["lines"])),2),"status":"blocking","evidence_id":None},
    {"id":"EX-008","vendor_id":"greencarton","line_no":6,"severity":"medium","type":"prior_period_reference","title":"Supplier says 'same as last year'","detail":"System resolved price using RFx baseline. Buyer should confirm FY26 baseline is the intended reference.","financial_exposure_inr":round(rfx_items[5]["annual_quantity"]*rfx_items[5]["baseline_unit_price_inr"],2),"status":"needs_review","evidence_id":evidence_id("greencarton",6)},
]

# Risk-prioritize exceptions. Blocking qualification issues outrank commercial cleanup;
# low-confidence values on already-disqualified suppliers have lower decision relevance.
severity_weight = {"critical": 1.0, "high": 0.75, "medium": 0.5, "low": 0.25}
for ex in truth["exceptions"]:
    relevance = 0.15 if ex["vendor_id"] == "alphapack" and ex["type"] != "qualification_failure" else 1.0
    ex["decision_relevance"] = relevance
    ex["priority_score"] = round((100 if ex["status"] == "blocking" else 0) + severity_weight.get(ex["severity"], 0.5) * math.log1p(max(ex["financial_exposure_inr"], 1)) * relevance, 3)
truth["exceptions"].sort(key=lambda x: x["priority_score"], reverse=True)

# Comparison rows, with all provenance/transformation metadata.
comparison=[]
for item in rfx_items:
    row={"line_no":item["line_no"],"sku":item["sku"],"description":item["description"],"qty":item["annual_quantity"],"baseline_unit_price_inr":item["baseline_unit_price_inr"],"vendors":{}}
    for vid,v in truth["vendors"].items():
        l=v["lines"][item["line_no"]-1]
        if l["quote_status"]=="not_quoted":
            row["vendors"][vid]={"status":"not_quoted","qualification":v["quality"],"unit_price":None,"landed_unit_cost":None,"evidence_id":None,"confidence":1.0}
            continue
        conf=0.99
        if vid=="alphapack": conf=0.86
        if vid=="alphapack" and item["line_no"]==18: conf=0.62
        if vid=="greencarton" and l.get("raw_basis")=="same_as_last_year": conf=0.82
        steps=[]
        basis=l.get("raw_basis")
        if basis=="100_piece": steps=[f"{l['raw_price']} {l['raw_currency']} / 100 pcs", "divide by 100", ("convert USD to INR at 83.20" if l['raw_currency']=='USD' else "currency already INR")]
        elif basis=="carton": steps=[f"{l['raw_price']} INR / carton", f"divide by pack size {l['pack_size']}", "add freight ₹0.32/pc"]
        elif basis=="bundle": steps=[f"{l['raw_price']} INR / bundle", f"divide by pack size {l['pack_size']}"]
        elif basis=="kg": steps=[f"{l['raw_price']} INR / kg", f"multiply by RFx unit weight {item['unit_weight_kg']} kg/pc", "add freight 2%"]
        elif basis=="same_as_last_year": steps=["supplier says same as last year", f"resolve RFx baseline ₹{item['baseline_unit_price_inr']}/pc", "add freight 2%"]
        else: steps=[f"{l['raw_price']} INR / piece"]
        row["vendors"][vid]={"status":"quoted","qualification":v["quality"],"unit_price":l["normalized_piece_price_inr"],"landed_unit_cost":l["landed_piece_price_inr"],"evidence_id":l["evidence_id"],"confidence":conf,"raw_basis":basis,"raw_price":l.get("raw_price"),"raw_currency":l.get("raw_currency","INR"),"transformation_steps":steps,"lead_days":v["lead"]}
    comparison.append(row)
truth["comparison"]=comparison

# Persist all canonical data.
(OUT / "rfx.json").write_text(json.dumps(rfx,indent=2),encoding="utf-8")
(OUT / "demo_state.json").write_text(json.dumps(truth,indent=2),encoding="utf-8")

# quick CSV truth for inspection
a=[]
for row in comparison:
    for vid,quote in row["vendors"].items():
        a.append([row["line_no"],row["sku"],vid,quote["status"],quote["qualification"],quote.get("unit_price"),quote.get("landed_unit_cost"),quote.get("confidence"),quote.get("evidence_id")])
with (OUT/"normalized_truth.csv").open("w",newline="",encoding="utf-8") as f:
    w=csv.writer(f); w.writerow(["line_no","sku","vendor","status","qualification","unit_price_inr","landed_unit_cost_inr","confidence","evidence_id"]); w.writerows(a)

manifest={
    "event":"RFX-CORR-2027-001",
    "files":[
        {"vendor":"Buyer RFx","file":"buyer_rfx_reference.xlsx","purpose":"Canonical 30-line RFx, baseline and questionnaire"},
        {"vendor":"PackRight Industries","file":"vendor_a_packright_offer.xlsx","purpose":"Nonstandard Excel; mixed per-piece and per-100-piece basis"},
        {"vendor":"CorrPro International","file":"vendor_b_corrpro_quote.pdf","purpose":"USD PDF; 3% conditional rebate buried in footnote"},
        {"vendor":"BoxWorks India Pvt Ltd","file":"vendor_c_boxworks_offer.docx","purpose":"Word quote; 27/30 lines; per-carton pricing; freight extra; certificate issue"},
        {"vendor":"AlphaPack Solutions","file":"vendor_d_alphapack_rate_card_photo.jpg","purpose":"Angled phone photo; bundle units; one obscured price; failed FSC"},
        {"vendor":"GreenCarton Co.","file":"vendor_e_greencarton_reply.eml","purpose":"Terse email; INR/kg; same-as-last-year references; freight 2%"},
    ],
    "designed_edge_cases":[
        "arbitrary supplier formats", "USD vs INR", "per 100 pieces vs per carton vs per bundle vs per kg", "partial quote 27/30", "missing lines must not become zero", "freight included vs extra", "conditional rebate in footnote", "quality pass/fail/pending", "certificate expiry", "angled/low-confidence photo", "same-as-last-year reference", "evidence/provenance per normalized value"
    ]
}
(OUT/"manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
print(f"Generated demo dataset in {OUT}")
print(json.dumps(manifest,indent=2))
