import pandas as pd
from io import BytesIO

def generate_excel_workbook(draft_obj, analytics_data, comments_list):
    """Generates a multi-sheet Excel workbook for the draft consultation."""
    buffer = BytesIO()
    
    # 1. Summary Sheet Preparation
    total_comments = analytics_data.get('comment_count', 0)
    sentiment_counts = {s['name']: s['value'] for s in analytics_data.get('sentiment', [])}
    
    summary_data = [
        ['Policy Metadata', ''],
        ['Policy Title', draft_obj.get('title', 'N/A')],
        ['Version', f"v{draft_obj.get('version_number', '1.0')}"],
        ['Draft ID', draft_obj.get('draft_id', 'N/A')],
        ['Total Comments Received', total_comments],
        ['', ''],
        ['Sentiment Distribution', 'Percentage (%)'],
        ['Positive', f"{round((sentiment_counts.get('Positive', 0)/total_comments * 100), 1) if total_comments > 0 else 0}%"],
        ['Neutral', f"{round((sentiment_counts.get('Neutral', 0)/total_comments * 100), 1) if total_comments > 0 else 0}%"],
        ['Negative', f"{round((sentiment_counts.get('Negative', 0)/total_comments * 100), 1) if total_comments > 0 else 0}%"]
    ]
    df_summary = pd.DataFrame(summary_data, columns=['Metric', 'Details'])
    
    # 2. Detailed Comments Sheet Preparation
    comments_rows = []
    for c in comments_list:
        comments_rows.append({
            'Clause Ref': c.get('clause_ref', 'General'),
            'Stakeholder': c.get('stakeholder_type', 'Unknown'),
            'Sentiment': c.get('sentiment', 'N/A'),
            'Comment Text': c.get('text', ''),
            'AI Synthesis': c.get('summary', ''),
            'Toxicity Flag': 'YES' if c.get('is_toxic') else 'no',
            'Score': c.get('sentiment_score', 0)
        })
    df_comments = pd.DataFrame(comments_rows)
    
    # 3. Keyword Analytics Sheet Preparation
    all_words = []
    for sentiment_label, words in analytics_data.get("wordCloud", {}).items():
        # wordCloud items usually look like: {"text": w, "value": c, "sentiment": "positive"}
        for w in words:
            all_words.append({
                'Keyword': w['text'],
                'Segment': w['sentiment'].capitalize(),
                'Volume': w['value']
            })
    # Sort total keywords by volume
    sorted_keywords = sorted(all_words, key=lambda x: x['Volume'], reverse=True)
    df_keywords = pd.DataFrame(sorted_keywords)
    
    # Write to Excel
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_summary.to_excel(writer, sheet_name='Summary', index=False)
        df_comments.to_excel(writer, sheet_name='Comments', index=False)
        df_keywords.to_excel(writer, sheet_name='Keywords', index=False)
        
        # Auto-adjust columns width 
        for sheetname in writer.sheets:
            worksheet = writer.sheets[sheetname]
            for col in worksheet.columns:
                max_length = 0
                column = col[0].column_letter # Get the column name
                for cell in col:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = (max_length + 2)
                # Limit max width for readability
                worksheet.column_dimensions[column].width = min(adjusted_width, 60)

    buffer.seek(0)
    return buffer
