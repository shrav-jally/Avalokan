import os
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.units import inch
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def generate_draft_report(draft, comments):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    # Title & Version
    elements.append(Paragraph(f"Consultation Report: {draft.get('title', 'Unknown Draft')}", styles['Heading1']))
    elements.append(Paragraph(f"Version: {draft.get('version_number', 'N/A')}", styles['Heading3']))
    elements.append(Spacer(1, 0.2 * inch))

    # Calculate sentiment distribution
    sentiments = {"POSITIVE": 0, "NEUTRAL": 0, "NEGATIVE": 0}
    combined_summaries = []
    
    for c in comments:
        s = c.get('sentiment', 'NEUTRAL').upper()
        if s in sentiments:
            sentiments[s] += 1
        
        smry = c.get('summary', '').strip()
        if smry:
            combined_summaries.append(smry)
            
    total = sum(sentiments.values())
    if total > 0:
        # Generate Pie Chart Image
        fig, ax = plt.subplots(figsize=(6, 4))
        labels = ['Positive', 'Neutral', 'Negative']
        sizes = [sentiments['POSITIVE'], sentiments['NEUTRAL'], sentiments['NEGATIVE']]
        colors = ['#0ca678', '#adb5bd', '#e03131']
        
        # Filter out 0 sizes
        actual_labels = [l for l, s in zip(labels, sizes) if s > 0]
        actual_sizes = [s for s in sizes if s > 0]
        actual_colors = [c for c, s in zip(colors, sizes) if s > 0]

        ax.pie(actual_sizes, labels=actual_labels, colors=actual_colors, autopct='%1.1f%%', startangle=90)
        ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
        
        img_buffer = BytesIO()
        plt.savefig(img_buffer, format='png', bbox_inches='tight')
        plt.close(fig)
        img_buffer.seek(0)
        
        elements.append(Paragraph("Sentiment Distribution", styles['Heading2']))
        elements.append(Image(img_buffer, width=5*inch, height=3.3*inch))
        elements.append(Spacer(1, 0.2 * inch))
    else:
        elements.append(Paragraph("No comments available to generate sentiment distribution.", styles['Normal']))
        elements.append(Spacer(1, 0.2 * inch))

    # Combined Summary
    elements.append(Paragraph("Combined AI Summary", styles['Heading2']))
    if combined_summaries:
        # Just join a few top summaries to form the combined summary (rudimentary approach)
        text = " ".join(combined_summaries[:15])
        if len(combined_summaries) > 15:
            text += " ... (and more)"
        elements.append(Paragraph(text, styles['Normal']))
    else:
        elements.append(Paragraph("No AI summaries available for these comments.", styles['Normal']))

    doc.build(elements)
    buffer.seek(0)
    return buffer
