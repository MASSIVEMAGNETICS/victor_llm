import time
import yaml
import sys
import os
import hashlib
import feedparser
import csv
from datetime import datetime
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings

from victor.core.loop import ConsciousnessLoop

# --- Configuration ---
CONFIG_DIR = os.path.dirname(__file__)
STORE_DIR = os.path.join(CONFIG_DIR, 'store')
RUNS_DIR = os.path.join(os.path.dirname(CONFIG_DIR), 'runs')
CHROMA_DIR = os.path.join(STORE_DIR, 'chroma')
SIGNALS_PATH = os.path.join(CONFIG_DIR, 'signals.yaml')
ROLES_PATH = os.path.join(CONFIG_DIR, 'roles.yaml')
os.makedirs(STORE_DIR, exist_ok=True)
os.makedirs(RUNS_DIR, exist_ok=True)


def load_config(path):
    """Loads a YAML configuration file."""
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def get_output_paths(dt_obj=None):
    """Generates file paths for the logs and reports for a given day."""
    if dt_obj is None:
        dt_obj = datetime.now()
    day_str = dt_obj.strftime('%Y%m%d')
    return {
        'metrics_csv': os.path.join(RUNS_DIR, f'metrics-{day_str}.csv'),
        'digest_md': os.path.join(RUNS_DIR, f'digest-{day_str}.md'),
    }

def init_metrics_csv(path):
    """Creates the CSV file and writes the header if it doesn't exist."""
    header = ['timestamp', 'uid', 'title', 'source_url', 'fidelity', 'sharpness', 'drift', 'depth_score', 'pred_loss', 'reward']
    if not os.path.exists(path):
        with open(path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(header)
    return header

def append_metrics_to_csv(path, header, data):
    """Appends a row of metrics to the CSV file."""
    with open(path, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writerow(data)

def obs_from_article(title, summary, embed_model):
    text = f"{title} {summary}"
    v = embed_model.encode([text])[0]
    return float((v[:8].mean()))

def handle_feed(url, coll, loop, embed_model, max_items, metrics_path, metrics_header):
    print(f"  Fetching feed: {url}")
    try:
        feed = feedparser.parse(url)
        if feed.bozo:
            print(f"    [Warning] Bozo feed detected: {feed.bozo_exception}")
    except Exception as e:
        print(f"    [Error] Could not fetch or parse feed: {e}")
        return

    new_items_processed = 0
    for entry in feed.entries[:max_items]:
        item_id_source = entry.get('link') or entry.get('title')
        if not item_id_source:
            continue

        uid = hashlib.sha256(item_id_source.encode()).hexdigest()
        if coll.get(ids=[uid])["ids"]:
            continue

        title = entry.get("title", "N/A")
        summary = entry.get("summary", "")
        text_content = f"{title} {summary}"

        o_t = obs_from_article(title, summary, embed_model)
        metrics, _ = loop.step(external_o=o_t)

        timestamp = datetime.now().isoformat()
        db_metadata = {**metrics, 'timestamp': timestamp, 'source': url, 'title': title}

        coll.add(ids=[uid], documents=[text_content], metadatas=[db_metadata])

        csv_row = {
            'timestamp': timestamp, 'uid': uid, 'title': title[:100], 'source_url': url, **metrics
        }
        append_metrics_to_csv(metrics_path, metrics_header, csv_row)

        new_items_processed += 1
        print(f"    + Ingested: {title[:80]}...")

    if new_items_processed > 0:
        print(f"  Processed {new_items_processed} new items from feed.")

def write_daily_digest(date_str, metrics_path):
    """Generates a daily Markdown digest from the metrics CSV."""
    digest_path = os.path.join(RUNS_DIR, f'digest-{date_str}.md')
    print(f"--- Writing Daily Digest for {date_str} ---")

    if not os.path.exists(metrics_path):
        with open(digest_path, 'w') as f:
            f.write(f"# Victor Digest - {date_str}\n\n")
            f.write("No activity recorded today.\n")
        return

    # Read metrics from CSV
    with open(metrics_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        with open(digest_path, 'w') as f:
            f.write(f"# Victor Digest - {date_str}\n\n")
            f.write("No new items processed today.\n")
        return

    # Calculate summary statistics
    total_items = len(rows)
    avg_fidelity = sum(float(r['fidelity']) for r in rows) / total_items
    avg_sharpness = sum(float(r['sharpness']) for r in rows) / total_items
    avg_reward = sum(float(r['reward']) for r in rows) / total_items

    # Get top 3 items by reward
    top_items = sorted(rows, key=lambda r: float(r['reward']), reverse=True)[:3]

    # Write digest
    with open(digest_path, 'w') as f:
        f.write(f"# Victor Digest - {date_str}\n\n")
        f.write("## Daily Summary\n")
        f.write(f"- **Total Items Processed:** {total_items}\n")
        f.write(f"- **Average Fidelity:** {avg_fidelity:.4f}\n")
        f.write(f"- **Average Sharpness:** {avg_sharpness:.4f}\n")
        f.write(f"- **Average Reward:** {avg_reward:.4f}\n\n")
        f.write("## Top Items by Reward\n")
        for i, item in enumerate(top_items):
            f.write(f"{i+1}. **{item['title']}** (Reward: {float(item['reward']):.4f})\n")
            f.write(f"   - *Source:* {item['source_url']}\n")

    print(f"Digest written to {digest_path}")

def main():
    print("--- Victor Runtime Initializing ---")
    signals_config = load_config(SIGNALS_PATH)
    print("Configuration loaded.")

    print("Initializing models and databases...")
    embed_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    chroma_client = chromadb.Client(Settings(persist_directory=CHROMA_DIR, is_persistent=True))
    collection = chroma_client.get_or_create_collection("rss_items")
    loop = ConsciousnessLoop(obs_dim=1, z_dim=4)
    print("Initialization complete.")

    feeds = [s for s in signals_config['sources'] if s['type'] == 'rss']
    max_items = signals_config.get('parsing', {}).get('max_items_per_pull', 10)

    current_day_str = ""

    print(f"Starting main loop, processing {len(feeds)} RSS feeds every 30 minutes.")

    try:
        while True:
            now = datetime.now()
            day_str = now.strftime('%Y%m%d')

            # If it's a new day, generate the previous day's digest
            if day_str != current_day_str and current_day_str != "":
                yesterday_dt = datetime.strptime(current_day_str, '%Y%m%d')
                yesterday_paths = get_output_paths(yesterday_dt)
                write_daily_digest(current_day_str, yesterday_paths['metrics_csv'])

            # Setup paths and files for the current day
            if day_str != current_day_str:
                current_day_str = day_str
                output_paths = get_output_paths() # Gets paths for today
                metrics_header = init_metrics_csv(output_paths['metrics_csv'])
                print(f"New day detected. Logging to: {output_paths['metrics_csv']}")

            print(f"\n--- Beginning New Processing Cycle ({now.strftime('%H:%M:%S')}) ---")
            for feed_source in feeds:
                handle_feed(
                    url=feed_source['url'],
                    coll=collection,
                    loop=loop,
                    embed_model=embed_model,
                    max_items=max_items,
                    metrics_path=output_paths['metrics_csv'],
                    metrics_header=metrics_header
                )

            print("--- Cycle Complete. Waiting for next interval... ---")
            time.sleep(1800)
    except KeyboardInterrupt:
        print("\n--- Victor Runtime Shutting Down ---")
        # Write final digest for the current day before exiting
        if current_day_str:
            # Get paths for the current day to write the final digest
            final_output_paths = get_output_paths(datetime.strptime(current_day_str, '%Y%m%d'))
            write_daily_digest(current_day_str, final_output_paths['metrics_csv'])

if __name__ == "__main__":
    main()