#!/usr/bin/env python3
"""
Extract images from USAU Ultimate rules website.

Fetches images from https://usaultimate.org/rules/ Appendix A (field diagrams)
and Appendix D (hand signals and observer signals).

Images are saved with caption-based filenames and GIF animations are preserved.
Generates image_catalog.json automatically.
"""

import re
import json
import requests
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from collections import defaultdict


def sanitize_filename(text: str) -> str:
    """Convert caption text to a valid filename."""
    # Remove common prefixes and numbers
    text = re.sub(r'^(Figure|Image|Diagram|Signal|Appendix\s*[A-Z][\.\:]?)[\s\d\.:]*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'^\d+[\.\)]\s*', '', text)

    # Convert to lowercase and clean up
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)  # Remove special characters
    text = re.sub(r'[-\s]+', '_', text)   # Replace spaces/hyphens with underscores
    text = text.strip('_')

    # Limit length
    if len(text) > 60:
        text = text[:60].rstrip('_')

    return text


def fetch_webpage(url: str) -> BeautifulSoup:
    """Fetch and parse webpage."""
    print(f"\nFetching webpage: {url}")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')
    print("✓ Webpage fetched successfully")
    return soup


def extract_from_table(table) -> list:
    """Extract images and captions from a table structure.

    Expected structure:
    - Tables can have multiple pairs of rows:
      - Even row (0, 2, 4...): Images
      - Odd row (1, 3, 5...): Captions
    """
    images = []
    rows = table.find_all('tr')

    if len(rows) < 2:
        return images

    # Process rows in pairs (image row, caption row)
    for row_idx in range(0, len(rows) - 1, 2):
        img_row = rows[row_idx]
        caption_row = rows[row_idx + 1]

        img_cells = img_row.find_all(['td', 'th'])
        caption_cells = caption_row.find_all(['td', 'th'])

        # Match images with captions by column
        for col_idx, img_cell in enumerate(img_cells):
            img_tag = img_cell.find('img')
            if not img_tag:
                continue

            img_url = img_tag.get('src')
            if not img_url:
                continue

            # Get corresponding caption
            caption = ""
            if col_idx < len(caption_cells):
                caption = caption_cells[col_idx].get_text(strip=True)

            if not caption:
                caption = f"signal_{row_idx//2 + 1}_{col_idx + 1}"

            images.append({
                'url': img_url,
                'caption': caption
            })

    return images


def extract_images_from_appendix(soup: BeautifulSoup, anchor_id: str, appendix_name: str) -> list:
    """Extract images from an appendix section."""
    print(f"\nSearching for {appendix_name}...")

    # Find appendix section
    appendix_section = soup.find(id=anchor_id)
    if not appendix_section:
        print(f"⚠️  Could not find {appendix_name}")
        return []

    print(f"✓ Found {appendix_name}")

    # Find parent container
    container = appendix_section.find_parent()

    # Find all tables in this section
    # We need to find tables that come after our anchor but before the next appendix
    images = []
    current = appendix_section

    while current:
        current = current.find_next()
        if not current:
            break

        # Stop at next appendix
        if current.get('id') and current.get('id').startswith('appendix_') and current.get('id') != anchor_id:
            break

        # Check if it's a table with images
        if current.name == 'table':
            table_images = extract_from_table(current)
            for img in table_images:
                img['appendix'] = appendix_name
            images.extend(table_images)

    print(f"✓ Found {len(images)} image(s) in {appendix_name}")
    return images


def download_image(url: str, output_path: Path, base_url: str) -> bool:
    """Download image from URL."""
    try:
        # Make absolute URL
        full_url = urljoin(base_url, url)

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(full_url, headers=headers, timeout=30)
        response.raise_for_status()

        # Save image
        with open(output_path, 'wb') as f:
            f.write(response.content)

        return True
    except Exception as e:
        print(f"  ❌ Failed to download: {e}")
        return False


def extract_images_from_web(base_url: str, output_dir: Path):
    """Extract all images from USAU rules webpage."""
    print("="*80)
    print("EXTRACTING IMAGES FROM USAU RULES WEBSITE (V2)")
    print("="*80)

    # Fetch webpage
    soup = fetch_webpage(base_url)

    # Extract images from appendices
    all_images = []
    all_images.extend(extract_images_from_appendix(soup, "appendix_a", "Appendix A"))
    all_images.extend(extract_images_from_appendix(soup, "appendix_d", "Appendix D"))

    if not all_images:
        print("\n❌ No images found!")
        return []

    print(f"\n{'='*80}")
    print(f"DOWNLOADING {len(all_images)} IMAGES")
    print('='*80)

    output_dir.mkdir(parents=True, exist_ok=True)

    extracted = []
    filename_counts = defaultdict(int)

    for i, img_info in enumerate(all_images, 1):
        url = img_info['url']
        caption = img_info['caption']
        appendix = img_info['appendix']

        print(f"\n[{i}/{len(all_images)}] {caption}")

        # Determine file extension from URL
        url_path = url.split('?')[0]
        original_ext = Path(url_path).suffix.lower()
        if not original_ext:
            original_ext = '.png'

        # Generate filename from caption
        base_name = sanitize_filename(caption)
        if not base_name or len(base_name) < 2:
            base_name = f"image_{i}"

        # Handle duplicate filenames
        filename_counts[base_name] += 1
        if filename_counts[base_name] > 1:
            filename = f"{base_name}_{filename_counts[base_name]}{original_ext}"
        else:
            filename = f"{base_name}{original_ext}"

        output_path = output_dir / filename

        # Download image
        success = download_image(url, output_path, base_url)

        if success:
            size = output_path.stat().st_size
            print(f"  ✓ Saved as: {filename} ({size:,} bytes)")

            extracted.append({
                'filename': filename,
                'caption': caption,
                'url': url,
                'appendix': appendix,
                'size': size,
                'format': original_ext[1:],
                'is_duplicate_name': filename_counts[base_name] > 1
            })

    print(f"\n{'='*80}")
    print(f"EXTRACTION COMPLETE")
    print('='*80)
    print(f"Successfully downloaded: {len(extracted)}/{len(all_images)} images")

    return extracted


def generate_catalog(images: list, output_path: Path):
    """Generate image_catalog.json."""
    print(f"\n{'='*80}")
    print("GENERATING IMAGE CATALOG")
    print('='*80)

    appendix_a = [img for img in images if 'Appendix A' in img['appendix']]
    appendix_d = [img for img in images if 'Appendix D' in img['appendix']]

    # Categorize Appendix D
    hand_signals = []
    observer_signals = []

    for img in appendix_d:
        if 'observer' in img['caption'].lower():
            observer_signals.append(img)
        else:
            hand_signals.append(img)

    catalog = {'usau': {}}

    # Field diagram
    if appendix_a:
        catalog['usau']['field_diagram'] = {
            'file': f"usau/{appendix_a[0]['filename']}",
            'description': appendix_a[0]['caption'],
            'keywords': ['field diagram'],
            'source': 'Appendix A'
        }

    # Hand signals
    if hand_signals:
        catalog['usau']['hand_signals'] = [
            {
                'file': f"usau/{img['filename']}",
                'description': img['caption'],
                'keywords': [sanitize_filename(img['caption']).replace('_', ' ')],
                'source': 'Appendix D1'
            }
            for img in hand_signals
        ]

    # Observer signals
    if observer_signals:
        catalog['usau']['observer_signals'] = [
            {
                'file': f"usau/{img['filename']}",
                'description': img['caption'],
                'keywords': [sanitize_filename(img['caption']).replace('_', ' ')],
                'source': 'Appendix D2'
            }
            for img in observer_signals
        ]

    with open(output_path, 'w') as f:
        json.dump(catalog, f, indent=2)

    print(f"\n✓ Generated catalog with:")
    print(f"   - {len(appendix_a)} field diagram(s)")
    print(f"   - {len(hand_signals)} hand signal(s)")
    print(f"   - {len(observer_signals)} observer signal(s)")
    print(f"\n✓ Saved to: {output_path}")


def create_extraction_report(images: list, output_dir: Path):
    """Create detailed JSON report."""
    report_path = output_dir / "_extraction_report.json"

    report = {
        'source': 'https://usaultimate.org/rules/',
        'total_images': len(images),
        'images': images
    }

    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\n✓ Saved extraction report: {report_path.name}")


def main():
    import shutil
    from datetime import datetime

    base_path = Path(__file__).parent.parent
    images_path = base_path / "parsed_rules" / "images"

    print("="*80)
    print("USAU RULES WEBSITE IMAGE EXTRACTION V2")
    print("="*80)

    # Backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if (images_path / "usau").exists():
        backup_dir = images_path / f"_backup_{timestamp}"
        print(f"\n📦 Backing up existing images to: {backup_dir.name}")
        backup_dir.mkdir(parents=True, exist_ok=True)
        shutil.copytree(images_path / "usau", backup_dir / "usau")

        catalog_path = images_path / "image_catalog.json"
        if catalog_path.exists():
            shutil.copy(catalog_path, backup_dir / "image_catalog.json")
        print("✓ Backup complete")

    # Extract
    url = "https://usaultimate.org/rules/"
    output_dir = images_path / "usau_web"

    images = extract_images_from_web(url, output_dir)

    if not images:
        print("\n❌ Extraction failed.")
        return

    # Generate catalog and report
    catalog_path = output_dir / "image_catalog.json"
    generate_catalog(images, catalog_path)
    create_extraction_report(images, output_dir)

    print("\n" + "="*80)
    print("NEXT STEPS")
    print("="*80)
    print(f"\n1. Review: python3 scripts/review_web_extraction.py")
    print(f"2. Finalize: python3 scripts/finalize_web_extraction.py")
    print("="*80)


if __name__ == "__main__":
    main()
