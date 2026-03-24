import os
import re

with open('app.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update imports
if "import spacy" not in text:
    text = re.sub(r"(import uuid)", r"import spacy\n\1", text)
    text = re.sub(r"(from flask_cors import CORS)", r"\1\ntry:\n    nlp = spacy.load('en_core_web_sm')\nexcept:\n    nlp = None", text)

# 2. Update get_draft_analytics word cloud logic
new_wordcloud_logic = '''    # Word Frequency per Sentiment using spaCy
    word_clouds = {"positive": [], "neutral": [], "negative": []}
    for s in ["POSITIVE", "NEUTRAL", "NEGATIVE"]:
        comm_list = list(comments_col.find({"draft_id": actual_draft_id, "sentiment": s}, {"text": 1}))
        wc = {}
        if nlp:
            # Combine text for faster processing
            combined_text = ". ".join([c.get("text", "") for c in comm_list])
            if combined_text:
                doc = nlp(combined_text)
                for token in doc:
                    if (token.pos_ in ["NOUN", "ADJ"]) and not token.is_stop and len(token.text) > 3:
                        clean_w = token.text.lower()
                        wc[clean_w] = wc.get(clean_w, 0) + 1
        else:
            # Fallback if spaCy model fails to load
            for c in comm_list:
                words = c.get("text", "").lower().split()
                for w in words:
                    clean_w = "".join(filter(str.isalnum, w))
                    if clean_w and len(clean_w) > 3:
                        wc[clean_w] = wc.get(clean_w, 0) + 1
                        
        sorted_wc = sorted(wc.items(), key=lambda x: x[1], reverse=True)[:20]
        word_clouds[s.lower()] = [{"text": w, "value": c, "sentiment": s.lower()} for w, c in sorted_wc]'''

text = re.sub(r"# Word Frequency per Sentiment.*?sorted_wc = sorted\(wc\.items\(\), key=lambda x: x\[1\], reverse=True\)\[:20\]\n\s+word_clouds\[s\.lower\(\)\] = \[\{\"text\": w, \"value\": c\} for w, c in sorted_wc\]", new_wordcloud_logic, text, flags=re.DOTALL)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(text)
print("Updated app.py with spaCy tokenization in analytics.")
