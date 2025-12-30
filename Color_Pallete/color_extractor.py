import io
import os
import time
import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
from sklearn.cluster import KMeans
from playwright.sync_api import sync_playwright
from datetime import datetime


def grab_screenshots(url, scroll_count=5):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1920, 'height': 1080})
        shots = []
        
        try:
            page.goto(url, wait_until='networkidle', timeout=30000)
            
            page_h = page.evaluate("document.body.scrollHeight")
            viewport_h = 1080
            
            actual_scrolls = min(scroll_count, int(page_h / viewport_h) + 1)
            
            for i in range(actual_scrolls):
                pos = i * viewport_h
                page.evaluate(f"window.scrollTo(0, {pos})")
                time.sleep(0.5)
                
                shot_bytes = page.screenshot()
                img = Image.open(io.BytesIO(shot_bytes))
                shots.append(img)
            
            return shots
        finally:
            browser.close()


def merge_images(imgs):
    w = 300
    resized = []
    
    for img in imgs:
        ratio = img.height / img.width
        h = int(w * ratio)
        resized.append(img.resize((w, h)))
    
    total_h = sum(img.height for img in resized)
    result = Image.new('RGB', (w, total_h))
    
    y = 0
    for img in resized:
        result.paste(img, (0, y))
        y += img.height
    
    return result


def get_colors(image, n_colors=8):
    arr = np.array(image)
    
    if len(arr.shape) == 3 and arr.shape[2] == 4:
        arr = arr[:, :, :3]
    
    pixels = arr.reshape(-1, 3)
    
    if len(pixels) > 10000:
        idx = np.random.choice(len(pixels), 10000, replace=False)
        pixels = pixels[idx]
    
    km = KMeans(n_clusters=n_colors, random_state=42, n_init=10)
    km.fit(pixels)
    
    colors = km.cluster_centers_
    labels = km.labels_
    counts = np.bincount(labels)
    
    sorted_idx = np.argsort(counts)[::-1]
    colors = colors[sorted_idx]
    counts = counts[sorted_idx]
    
    return colors.astype(int), counts


def to_hex(rgb):
    return '#{:02x}{:02x}{:02x}'.format(rgb[0], rgb[1], rgb[2])


def format_palette(colors, counts):
    total = sum(counts)
    hex_parts = []
    rgb_parts = []
    
    for color, count in zip(colors, counts):
        pct = (count / total) * 100
        r, g, b = color
        hex_val = to_hex(color)
        
        hex_parts.append(f"{hex_val} ({pct:.1f}%)")
        rgb_parts.append(f"RGB({r},{g},{b}) ({pct:.1f}%)")
    
    return " | ".join(hex_parts), " | ".join(rgb_parts)


def draw_palette(colors, counts, url="", title=""):
    w = 1200
    color_h = 120
    header_h = 100
    footer_h = 40
    gap = 10
    total_h = header_h + (len(colors) * (color_h + gap)) + footer_h
    
    img = Image.new('RGB', (w, total_h), 'white')
    draw = ImageDraw.Draw(img)
    
    try:
        fonts = [
            "C:\\Windows\\Fonts\\arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
        
        title_font = None
        for fpath in fonts:
            try:
                title_font = ImageFont.truetype(fpath, 32)
                text_font = ImageFont.truetype(fpath, 20)
                small_font = ImageFont.truetype(fpath, 16)
                break
            except:
                continue
        
        if not title_font:
            raise Exception()
    except:
        title_font = ImageFont.load_default()
        text_font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    
    display_title = title if title else "Color Palette"
    draw.text((20, 15), display_title, fill='black', font=title_font)
    
    if url:
        truncated = url[:80] + ('...' if len(url) > 80 else '')
        draw.text((20, 55), truncated, fill='gray', font=small_font)
    
    total = sum(counts)
    y = header_h
    
    for i, (color, count) in enumerate(zip(colors, counts)):
        pct = (count / total) * 100
        r, g, b = color
        hex_val = to_hex(color)
        
        rect_w = 400
        draw.rectangle(
            [(20, y), (20 + rect_w, y + color_h)],
            fill=(r, g, b),
            outline='#cccccc',
            width=2
        )
        
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        txt_color = 'white' if brightness < 128 else 'black'
        
        draw.text((30, y + 10), f"Color {i+1}", fill=txt_color, font=text_font)
        
        info_x = 20 + rect_w + 30
        draw.text((info_x, y + 10), f"HEX: {hex_val}", fill='black', font=text_font)
        draw.text((info_x, y + 40), f"RGB: ({r}, {g}, {b})", fill='black', font=text_font)
        draw.text((info_x, y + 70), f"Usage: {pct:.1f}%", fill='black', font=text_font)
        
        bar_w = 300
        bar_h = 20
        bar_x = info_x + 450
        bar_y = y + 50
        
        draw.rectangle(
            [(bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h)],
            fill='#eeeeee',
            outline='#cccccc',
            width=1
        )
        
        filled_w = int((pct / 100) * bar_w)
        draw.rectangle(
            [(bar_x, bar_y), (bar_x + filled_w, bar_y + bar_h)],
            fill=(r, g, b)
        )
        
        y += color_h + gap
    
    return img


def clean_filename(name):
    bad_chars = '<>:"/\\|?*'
    for c in bad_chars:
        name = name.replace(c, '_')
    return name[:50]


def process_site(row, scroll_count, out_dir):
    url = row['Link']
    sr = row.get('Sr', row.name + 1)
    name = row.get('name', 'Unknown')
    title = row.get('Title', '')
    
    print(f"\n{'='*70}")
    print(f"Processing: {name}")
    print(f"URL: {url}")
    print(f"{'='*70}")
    
    try:
        print(f"Capturing screenshots...")
        shots = grab_screenshots(url, scroll_count)
        print(f"✓ Got {len(shots)} screenshots")
        
        print("Analyzing colors...")
        merged = merge_images(shots)
        colors, counts = get_colors(merged, num_colors=8)
        hex_str, rgb_str = format_palette(colors, counts)
        
        print(f"✓ Done with {name}")
        return True, hex_str, rgb_str
    except Exception as e:
        print(f"✗ Error with {name}: {str(e)}")
        print(f" Moving on...")
        
        err_log = os.path.join(out_dir, 'errors.log')
        with open(err_log, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*50}\n")
            f.write(f"Sr: {row.get('Sr', row.name + 1)}\n")
            f.write(f"Name: {name}\n")
            f.write(f"URL: {url}\n")
            f.write(f"Error: {str(e)}\n")
        
        return False, "", ""


def run():
    print("="*70)
    print("BATCH WEBSITE COLOR PALETTE EXTRACTOR")
    print("="*70)
    
    csv_path = input("\nEnter CSV file path: ")
    
    try:
        encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252', 'utf-16']
        df = None
        
        for enc in encodings:
            try:
                df = pd.read_csv(csv_path, encoding=enc)
                print(f"\n✓ Loaded CSV with {len(df)} rows (encoding: {enc})")
                break
            except UnicodeDecodeError:
                continue
        
        if df is None:
            print(f"✗ Couldn't read CSV with any encoding")
            return
    except Exception as e:
        print(f"✗ Error reading CSV: {str(e)}")
        return
    
    if 'Link' not in df.columns:
        print("✗ CSV needs a 'Link' column")
        return
    
    try:
        scroll_input = input("Scroll captures per site (default 3, max 10): ")
        scrolls = int(scroll_input) if scroll_input else 3
        scrolls = min(max(1, scrolls), 10)
    except:
        scrolls = 3
    
    try:
        limit_input = input(f"How many sites to process? (Enter for all {len(df)}): ")
        limit = int(limit_input) if limit_input else len(df)
        limit = min(limit, len(df))
    except:
        limit = len(df)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = f"website_palettes_{timestamp}"
    os.makedirs(out_dir, exist_ok=True)
    print(f"\n✓ Output directory: {out_dir}/")
    
    print(f"\n{'='*70}")
    print(f"STARTING BATCH PROCESSING - {limit} websites")
    print(f"{'='*70}")
    
    success = 0
    failed = 0
    
    results = df.head(limit).copy()
    results['Color Palette (HEX)'] = ""
    results['Color Palette (RGB)'] = ""
    results['Status'] = ""
    
    for idx, row in df.head(limit).iterrows():
        ok, hex_str, rgb_str = process_site(row, scrolls, out_dir)
        
        if ok:
            success += 1
            results.at[idx, 'Color Palette (HEX)'] = hex_str
            results.at[idx, 'Color Palette (RGB)'] = rgb_str
            results.at[idx, 'Status'] = "Success"
        else:
            failed += 1
            results.at[idx, 'Color Palette (HEX)'] = "Failed to extract"
            results.at[idx, 'Color Palette (RGB)'] = "Failed to extract"
            results.at[idx, 'Status'] = "Failed"
        
        if idx < limit - 1:
            time.sleep(2)
    
    csv_out = os.path.join(out_dir, 'combined.csv')
    results.to_csv(csv_out, index=False, encoding='utf-8')
    print(f"\n✓ Saved results to: {csv_out}")
    
    print(f"\n{'='*70}")
    print("BATCH PROCESSING COMPLETE")
    print(f"{'='*70}")
    print(f"✓ Successfully processed: {success}")
    print(f"✗ Failed: {failed}")
    print(f"📁 All files in: {out_dir}/")
    print(f"📊 Combined CSV: combined.csv")
    print(f"{'='*70}")


if __name__ == "__main__":
    run()