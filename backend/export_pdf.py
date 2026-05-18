import base64
import io
from datetime import datetime
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER

W, H   = A4
MARGIN = 20 * mm


def _b64_to_img(b64: str, max_w: float, max_h: float) -> Image:
    data = base64.b64decode(b64)
    buf  = io.BytesIO(data)
    img  = Image(buf)
    r    = min(max_w / img.imageWidth, max_h / img.imageHeight)
    img.drawWidth  = img.imageWidth  * r
    img.drawHeight = img.imageHeight * r
    return img


def _file_to_img(path: str, max_w: float, max_h: float) -> Image:
    img = Image(path)
    r   = min(max_w / img.imageWidth, max_h / img.imageHeight)
    img.drawWidth  = img.imageWidth  * r
    img.drawHeight = img.imageHeight * r
    return img


def _make_styles():
    return {
        'title':   ParagraphStyle('t1', fontSize=18, fontName='Helvetica-Bold', spaceAfter=4,   textColor=colors.HexColor('#1d4ed8')),
        'sub':     ParagraphStyle('t2', fontSize=10, fontName='Helvetica',      spaceAfter=2,   textColor=colors.HexColor('#6b7280')),
        'heading': ParagraphStyle('t3', fontSize=12, fontName='Helvetica-Bold', spaceBefore=12, spaceAfter=4, textColor=colors.HexColor('#111')),
        'note':    ParagraphStyle('t4', fontSize=9,  fontName='Helvetica',      textColor=colors.HexColor('#9ca3af'), alignment=TA_CENTER),
    }


def _build_story(buf, filename, wall_pct, width, height, orig_src, overlay_src, extracted_src, img_loader):
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN,  bottomMargin=MARGIN,
    )
    S        = _make_styles()
    usable_w = W - 2 * MARGIN
    img_w    = (usable_w - 10 * mm) / 2
    img_h    = 80 * mm

    story = []

    # Header
    story.append(Paragraph("ArchAnalyse", S['title']))
    story.append(Paragraph("Wall Segmentation Report", S['sub']))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", S['sub']))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e5e7eb'), spaceAfter=10))

    # Summary table
    story.append(Paragraph("Analysis Summary", S['heading']))
    stat_data = [
        ["File",          filename],
        ["Dimensions",    f"{width} × {height} px"],
        ["Wall Coverage", f"{wall_pct}%"],
    ]
    stat_tbl = Table(stat_data, colWidths=[40 * mm, usable_w - 40 * mm])
    stat_tbl.setStyle(TableStyle([
        ('FONTNAME',       (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME',       (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE',       (0, 0), (-1, -1), 10),
        ('TEXTCOLOR',      (0, 0), (0, -1), colors.HexColor('#374151')),
        ('TEXTCOLOR',      (1, 0), (1, -1), colors.HexColor('#111')),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.HexColor('#f9fafb'), colors.white]),
        ('GRID',           (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
        ('LEFTPADDING',    (0, 0), (-1, -1), 8),
        ('RIGHTPADDING',   (0, 0), (-1, -1), 8),
        ('TOPPADDING',     (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING',  (0, 0), (-1, -1), 5),
    ]))
    story.append(stat_tbl)
    story.append(Spacer(1, 8 * mm))

    # Original image
    story.append(Paragraph("Original Image", S['heading']))
    orig = img_loader(orig_src, usable_w, 90 * mm)
    orig.hAlign = 'CENTER'
    story.append(orig)
    story.append(Spacer(1, 6 * mm))

    # Wall segmentation results side by side
    story.append(Paragraph("Wall Segmentation Results", S['heading']))
    ov  = img_loader(overlay_src,   img_w, img_h)
    ext = img_loader(extracted_src, img_w, img_h)
    seg_tbl = Table(
        [[ov, ext],
         [Paragraph("Overlay — walls in red", S['note']),
          Paragraph("Extracted walls", S['note'])]],
        colWidths=[img_w + 5 * mm, img_w + 5 * mm],
    )
    seg_tbl.setStyle(TableStyle([
        ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING',   (0, 0), (-1, -1), 0),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 0),
        ('TOPPADDING',    (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(seg_tbl)

    # Footer
    story.append(Spacer(1, 10 * mm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e5e7eb'), spaceAfter=4))
    story.append(Paragraph("COMP9900 · Team F09D-DONUT · ArchAnalyse", S['note']))

    doc.build(story)


def build_segment_pdf_from_b64(filename, wall_pct, width, height,
                                original_b64, overlay_b64, extracted_b64) -> bytes:
    buf = io.BytesIO()
    _build_story(buf, filename, wall_pct, width, height,
                 original_b64, overlay_b64, extracted_b64, _b64_to_img)
    return buf.getvalue()


def build_segment_pdf_from_files(filename, wall_pct, width, height,
                                  original_path, overlay_path, extracted_path) -> bytes:
    buf = io.BytesIO()
    _build_story(buf, filename, wall_pct, width, height,
                 original_path, overlay_path, extracted_path, _file_to_img)
    return buf.getvalue()