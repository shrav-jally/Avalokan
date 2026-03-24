import os
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY

def generate_professional_report(draft_obj, analytics_data):
    """
    Generates a professional PDF report for a draft consultation.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()
    
    # Custom Styles
    title_style = ParagraphStyle(
        'MainTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=12,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#2c3e50")
    )
    
    header_style = ParagraphStyle(
        'MinistryHeader',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_CENTER,
        textColor=colors.grey,
        spaceAfter=20
    )
    
    subheading_style = ParagraphStyle(
        'SubHeading',
        parent=styles['Heading2'],
        fontSize=14,
        color=colors.HexColor("#2980b9"),
        spaceBefore=15,
        spaceAfter=10
    )

    body_style = ParagraphStyle(
        'BodyText',
        parent=styles['Normal'],
        fontSize=11,
        leading=14,
        alignment=TA_JUSTIFY
    )

    elements = []

    # 1. Header
    elements.append(Paragraph("Ministry of Corporate Affairs", header_style))
    elements.append(Paragraph("eConsultation Analysis Report", title_style))
    elements.append(Paragraph(f"Generated on {datetime.now().strftime('%d %B %Y, %H:%M')}", header_style))
    elements.append(Spacer(1, 0.3 * inch))

    # 2. Policy Metadata Table
    metadata = [
        ["Policy Title", draft_obj.get("title", "Unknown Policy")],
        ["Draft ID", draft_obj.get("draft_id", "N/A")],
        ["Version", f"v{draft_obj.get('version_number', '1.0')}"],
        ["Created Date", draft_obj.get("created_at").strftime('%Y-%m-%d') if isinstance(draft_obj.get("created_at"), datetime) else "N/A"]
    ]
    
    t_meta = Table(metadata, colWidths=[1.5*inch, 4.5*inch])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#f8f9fa")),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor("#2c3e50")),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.grey),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(t_meta)
    elements.append(Spacer(1, 0.4 * inch))

    # 3. Executive Summary
    elements.append(Paragraph("AI Executive Summary", subheading_style))
    summary_text = analytics_data.get("combinedSummary", "No summary available.")
    elements.append(Paragraph(summary_text, body_style))
    elements.append(Spacer(1, 0.4 * inch))

    # 4. Top Keywords Table
    elements.append(Paragraph("Stakeholder Keyword Analysis (Top 10)", subheading_style))
    
    # Flatten word clouds and take top 10 by value
    all_words = []
    for sentiment, words in analytics_data.get("wordCloud", {}).items():
        all_words.extend(words)
    
    sorted_words = sorted(all_words, key=lambda x: x['value'], reverse=True)[:10]
    
    kw_header = [["Keyword", "Sentiment", "Frequency Score"]]
    kw_rows = [[w['text'], w['sentiment'].capitalize(), str(w['value'])] for w in sorted_words]
    
    t_kw = Table(kw_header + kw_rows, colWidths=[2.2*inch, 2*inch, 1.8*inch])
    t_kw.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2980b9")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.HexColor("#f1f3f5")]),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(t_kw)
    elements.append(Spacer(1, 0.4 * inch))

    # 5. Clause-wise Feedback Synthesis
    elements.append(Paragraph("Clause-wise Synthesis Matrix", subheading_style))
    
    clause_data = analytics_data.get("clauseSummaries", [])
    if clause_data:
        c_header = [["Clause Reference", "Consensus", "Synthesis Summary"]]
        c_rows = [[c['clause'], c['sentiment'].upper(), c['summary']] for c in clause_data]
        
        # Adjust colWidths to give more space to summary
        t_clause = Table(c_header + c_rows, colWidths=[1.2*inch, 1.1*inch, 4.2*inch])
        t_clause.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('FONTSIZE', (0,1), (-1,-1), 9),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(t_clause)
    else:
        elements.append(Paragraph("No clause-wise data found for this version.", body_style))

    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer
