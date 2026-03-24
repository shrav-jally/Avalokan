import os
import sys
import math
from datetime import datetime, timezone

# Add parent directory (backend) to sys.path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import comments_col
from ai_engine import process_batch

def print_progress_bar(iteration, total, prefix='', suffix='', decimals=1, length=50, fill='█', print_end="\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        print_end   - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = print_end)
    # Print New Line on Complete
    if iteration == total:
        print()

def analyze_comments():
    print("--- 🧠 Starting Analysis of Unprocessed Comments ---")
    
    # 1. Find all comments with missing sentiment
    # We'll check for null or missing "sentiment" field
    query = {"$or": [{"sentiment": None}, {"sentiment": {"$exists": False}}]}
    comments_cursor = comments_col.find(query)
    all_comments = list(comments_cursor)
    total_count = len(all_comments)
    
    if total_count == 0:
        print("✅ No un-analyzed comments found in Atlas. Everything looks current!")
        return

    print(f"📊 Found {total_count} comments needing analysis.")
    print(f"🔄 Batch Processing (Size: 10). Loading AI models (this may take a bit)...")
    
    processed_count = 0
    batch_size = 10
    
    # 2. Iterate in batches of 10
    for i in range(0, total_count, batch_size):
        batch = all_comments[i:i+batch_size]
        batch_ids = [str(c['_id']) for c in batch]
        # Actual texts for analysis
        batch_texts = [c.get('text', '') for c in batch]
        
        # 3. Analyze Batch
        try:
            analyzed_results = process_batch(batch_texts)
            
            # 4. Update Atlas for each document in the batch accordingly
            for idx, result in enumerate(analyzed_results):
                doc_id = batch[idx]['_id']
                update_fields = {
                    "sentiment": result["sentiment"],
                    "sentiment_score": result["sentiment_score"],
                    "is_toxic": result["is_toxic"],
                    "toxicity_score": result["toxicity_score"],
                    "summary": result["summary"],
                    "processed_at": datetime.now(timezone.utc)
                }
                comments_col.update_one({"_id": doc_id}, {"$set": update_fields})
            
            processed_count += len(batch)
            print_progress_bar(processed_count, total_count, prefix='Progress:', suffix='Complete', length=50)
            
        except Exception as e:
            print(f"\n❌ Error processing batch starting at index {i}: {e}")
            continue

    print(f"\n✅ All set! Successfully analyzed and updated {processed_count} comments in MongoDB Atlas.")

def analyze_drafts():
    from database import drafts_col
    from ai_engine import generate_draft_summary
    print("\n--- 🧠 Starting Meta-Analysis of Existing Drafts ---")
    drafts = list(drafts_col.find({}))
    total_count = len(drafts)
    
    if total_count == 0:
        print("✅ No drafts found.")
        return

    print(f"📊 Found {total_count} drafts needing meta-analysis.")
    processed_count = 0

    for draft in drafts:
        draft_id = draft["draft_id"]
        try:
            generate_draft_summary(draft_id)
            processed_count += 1
            print_progress_bar(processed_count, total_count, prefix='Progress:', suffix=f'({draft_id})', length=50)
        except Exception as e:
            print(f"\n❌ Error analyzing draft {draft_id}: {e}")
            
    print(f"\n✅ All set! Successfully meta-analyzed and updated {processed_count} drafts in MongoDB Atlas.")

if __name__ == "__main__":
    analyze_comments()
    analyze_drafts()
