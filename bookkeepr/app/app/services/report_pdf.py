"""PDF Report Generator - Better than QBO
Uses reportlab to build branded PDF financial reports
"""
import io
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT


# Brand colors matching theme.css
BRAND_PRIMARY = colors.HexColor('#2563eb')
BRAND_SUCCESS = colors.HexColor('#10b981')
BRAND_DANGER = colors.HexColor('#ef4444')
GRAY_50 = colors.HexColor('#f9fafb')
GRAY_200 = colors.HexColor('#e5e7eb')
GRAY_500 = colors.HexColor('#6b7280')
GRAY_900 = colors.HexColor('#111827')


def _build_styles():
    styles = getSampleStyleSheet()
    
    styles.add(ParagraphStyle(
        name='BKTitle',
        fontSize=24,
        leading=30,
        textColor=GRAY_900,
        spaceAfter=12,
        fontName='Helvetica-Bold',
    ))
    styles.add(ParagraphStyle(
        name='BKSubtitle',
        fontSize=14,
        leading=18,
        textColor=GRAY_500,
        spaceAfter=20,
    ))
    styles.add(ParagraphStyle(
        name='BKSection',
        fontSize=16,
        leading=20,
        textColor=BRAND_PRIMARY,
        spaceAfter=10,
        spaceBefore=20,
        fontName='Helvetica-Bold',
    ))
    styles.add(ParagraphStyle(
        name='BKLabel',
        fontSize=10,
        textColor=GRAY_500,
        leading=14,
    ))
    styles.add(ParagraphStyle(
        name='BKValue',
        fontSize=18,
        textColor=GRAY_900,
        leading=22,
        fontName='Helvetica-Bold',
    ))
    return styles


def _header(canvas, doc, company_name="BookKeepr AI"):
    canvas.saveState()
    canvas.setFont('Helvetica-Bold', 14)
    canvas.setFillColor(BRAND_PRIMARY)
    canvas.drawString(0.5*inch, 10.5*inch, company_name)
    canvas.setStrokeColor(BRAND_PRIMARY)
    canvas.setLineWidth(2)
    canvas.line(0.5*inch, 10.4*inch, 8*inch, 10.4*inch)
    canvas.restoreState()


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(GRAY_500)
    canvas.drawCentredString(4.25*inch, 0.4*inch, 
                             f"BookKeepr AI - Page {doc.page} - Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    canvas.restoreState()


def _on_page(canvas, doc):
    _header(canvas, doc)
    _footer(canvas, doc)


def build_pl_report(company_name, period_start, period_end, line_items, totals):
    """Build a Profit & Loss PDF report"""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter,
                            topMargin=1.2*inch, bottomMargin=0.7*inch,
                            leftMargin=0.5*inch, rightMargin=0.5*inch)
    styles = _build_styles()
    story = []
    
    # Header info
    story.append(Paragraph(f"Profit & Loss Statement", styles['BKTitle']))
    story.append(Paragraph(f"{company_name}", styles['BKSubtitle']))
    
    period = f"{period_start.strftime('%B %d, %Y')} - {period_end.strftime('%B %d, %Y')}"
    story.append(Paragraph(f"<b>Period:</b> {period}", styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    # Summary cards (row of 3)
    summary_data = [[
        Paragraph("REVENUE", styles['BKLabel']),
        Paragraph("EXPENSES", styles['BKLabel']),
        Paragraph("NET INCOME", styles['BKLabel']),
    ], [
        Paragraph(f"${totals.get('revenue', 0):,.2f}", styles['BKValue']),
        Paragraph(f"${totals.get('expenses', 0):,.2f}", styles['BKValue']),
        Paragraph(f"${totals.get('net_income', 0):,.2f}", styles['BKValue']),
    ]]
    summary_table = Table(summary_data, colWidths=[2.5*inch, 2.5*inch, 2.5*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), GRAY_50),
        ('BOX', (0, 0), (-1, -1), 1, GRAY_200),
        ('PADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Detail line items
    if line_items:
        story.append(Paragraph("Income Detail", styles['BKSection']))
        income_items = [(c, a) for c, a in line_items if a > 0]
        if income_items:
            data = [["Category", "Amount"]] + [[c, f"${a:,.2f}"] for c, a in income_items]
            t = _build_table(data)
            story.append(t)
            story.append(Spacer(1, 0.2*inch))
        
        story.append(Paragraph("Expense Detail", styles['BKSection']))
        expense_items = [(c, abs(a)) for c, a in line_items if a < 0]
        if expense_items:
            data = [["Category", "Amount"]] + [[c, f"${a:,.2f}"] for c, a in expense_items]
            t = _build_table(data)
            story.append(t)
    
    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    buf.seek(0)
    return buf


def _build_table(data, col_widths=None):
    if col_widths is None:
        col_widths = [4.5*inch, 1.5*inch]
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), GRAY_50),
        ('TEXTCOLOR', (0, 0), (-1, 0), GRAY_500),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, GRAY_200),
    ]))
    return t


def build_balance_sheet(company_name, as_of_date, sections):
    """Build Balance Sheet PDF
    sections = {'assets': [(name, amount)], 'liabilities': [...], 'equity': [...]}
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter,
                            topMargin=1.2*inch, bottomMargin=0.7*inch)
    styles = _build_styles()
    story = []
    
    story.append(Paragraph("Balance Sheet", styles['BKTitle']))
    story.append(Paragraph(company_name, styles['BKSubtitle']))
    story.append(Paragraph(f"As of {as_of_date.strftime('%B %d, %Y')}", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    for section_name, label in [('assets', 'Assets'), ('liabilities', 'Liabilities'), ('equity', 'Equity')]:
        items = sections.get(section_name, [])
        story.append(Paragraph(label, styles['BKSection']))
        total = sum(a for _, a in items)
        data = [["Account", "Amount"]] + [[n, f"${a:,.2f}"] for n, a in items]
        data.append([f"Total {label}", f"${total:,.2f}"])
        t = _build_table(data)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, -1), (-1, -1), BRAND_PRIMARY),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ], parent=t._cellStyles))
        story.append(t)
        story.append(Spacer(1, 0.2*inch))
    
    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    buf.seek(0)
    return buf


def build_transactions_report(company_name, transactions, filters_applied=None):
    """Custom transactions report with applied filters"""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter,
                            topMargin=1.2*inch, bottomMargin=0.7*inch)
    styles = _build_styles()
    story = []
    
    story.append(Paragraph("Transaction Report", styles['BKTitle']))
    story.append(Paragraph(company_name, styles['BKSubtitle']))
    
    if filters_applied:
        filter_text = "<b>Filters:</b> " + ", ".join(f"{k}={v}" for k, v in filters_applied.items() if v)
        story.append(Paragraph(filter_text, styles['Normal']))
    
    story.append(Spacer(1, 0.2*inch))
    
    # Stats summary
    total = len(transactions)
    total_amount = sum(t.get('amount', 0) for t in transactions)
    story.append(Paragraph(f"<b>{total}</b> transactions, total <b>${total_amount:,.2f}</b>", styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    # Table
    data = [["Date", "Description", "Category", "Amount"]]
    for txn in transactions[:500]:  # cap to 500 per page
        data.append([
            txn.get('date', ''),
            (txn.get('description') or '')[:50],
            (txn.get('category') or 'Uncategorized')[:25],
            f"${txn.get('amount', 0):,.2f}",
        ])
    
    t = Table(data, colWidths=[1*inch, 3*inch, 1.8*inch, 1.2*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BRAND_PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.25, GRAY_200),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, GRAY_50]),
    ]))
    story.append(t)
    
    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    buf.seek(0)
    return buf
