#!/usr/bin/env python3
"""
Generate an HTML page showing all images with their current labels.
This makes it easy to visually verify all labels at once.
"""

import json
from pathlib import Path
import base64


def image_to_base64(image_path: Path) -> str:
    """Convert image to base64 for embedding in HTML."""
    with open(image_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')


def generate_review_html():
    """Generate HTML review page."""
    base_path = Path(__file__).parent.parent
    images_path = base_path / "parsed_rules" / "images"
    catalog_path = images_path / "image_catalog.json"
    output_path = base_path / "image_review.html"

    # Load catalog
    with open(catalog_path) as f:
        catalog = json.load(f)

    # Start HTML
    html = """<!DOCTYPE html>
<html>
<head>
    <title>Image Label Review</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }
        h1 {
            color: #333;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
        }
        h2 {
            color: #555;
            margin-top: 40px;
            border-bottom: 2px solid #ddd;
            padding-bottom: 5px;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        .image-card {
            background: white;
            border: 2px solid #ddd;
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .image-card.error {
            border-color: #f44336;
            background: #ffebee;
        }
        .image-card img {
            width: 100%;
            height: 200px;
            object-fit: contain;
            background: #fafafa;
            border: 1px solid #eee;
            border-radius: 4px;
        }
        .label {
            font-weight: bold;
            color: #333;
            margin-top: 10px;
            font-size: 14px;
        }
        .filename {
            color: #666;
            font-size: 12px;
            font-family: monospace;
            margin-top: 5px;
        }
        .section {
            color: #888;
            font-size: 11px;
            margin-top: 3px;
        }
        .error-msg {
            color: #f44336;
            font-weight: bold;
            margin-top: 10px;
        }
        .instructions {
            background: #e3f2fd;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #2196F3;
            margin: 20px 0;
        }
        .instructions h3 {
            margin-top: 0;
            color: #1976D2;
        }
        .instructions ol {
            margin-bottom: 0;
        }
        .stats {
            background: #fff3cd;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #ffc107;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <h1>🥏 Observer-GPT Image Label Review</h1>

    <div class="instructions">
        <h3>📋 How to Use This Review Page</h3>
        <ol>
            <li>Scroll through all images below</li>
            <li>Verify each image matches its label</li>
            <li>If you find a mislabeled image, note the filename and what it actually shows</li>
            <li>Use <code>rebuild_image_catalog.py</code> to systematically fix all labels</li>
            <li>Or manually edit <code>parsed_rules/images/image_catalog.json</code></li>
        </ol>
        <p><strong>Tip:</strong> Compare with the official PDF: <code>rulebooks/USAU-2026-2027.pdf</code> (Appendix D)</p>
    </div>
"""

    # Stats
    total_images = 0
    missing_images = 0

    # Process each rulebook
    for rulebook, sections in catalog.items():
        html += f'<h2>{rulebook.upper()} Rulebook</h2>\n'

        for section_name, items in sections.items():
            section_title = section_name.replace('_', ' ').title()
            html += f'<h3>{section_title}</h3>\n<div class="grid">\n'

            items_list = [items] if isinstance(items, dict) else items

            for item in items_list:
                total_images += 1
                file_path = images_path / item['file']
                description = item['description']
                filename = item['file']
                source = item.get('source', '')

                if file_path.exists():
                    # Embed image as base64
                    img_ext = file_path.suffix[1:]  # Remove the dot
                    if img_ext == 'jpg':
                        img_ext = 'jpeg'
                    img_data = image_to_base64(file_path)
                    img_tag = f'<img src="data:image/{img_ext};base64,{img_data}" alt="{description}">'
                    card_class = 'image-card'
                else:
                    missing_images += 1
                    img_tag = '<div class="error-msg">❌ FILE NOT FOUND</div>'
                    card_class = 'image-card error'

                html += f'''
    <div class="{card_class}">
        {img_tag}
        <div class="label">{description}</div>
        <div class="filename">{filename}</div>
        <div class="section">{source}</div>
    </div>
'''

            html += '</div>\n'

    # Add stats
    html += f'''
    <div class="stats">
        <h3>📊 Statistics</h3>
        <p><strong>Total Images:</strong> {total_images}</p>
        <p><strong>Missing Files:</strong> {missing_images}</p>
        <p><strong>Status:</strong> {"✓ All files found" if missing_images == 0 else f"⚠️ {missing_images} files missing"}</p>
    </div>
'''

    # Close HTML
    html += """
    <div style="margin-top: 40px; padding: 20px; background: #f0f0f0; border-radius: 8px; text-align: center;">
        <p style="color: #666;">Generated by Observer-GPT Image Review Tool</p>
        <p style="color: #888; font-size: 12px;">To regenerate: <code>python3 scripts/generate_image_review.py</code></p>
    </div>
</body>
</html>
"""

    # Save HTML
    with open(output_path, 'w') as f:
        f.write(html)

    print("="*80)
    print("IMAGE REVIEW PAGE GENERATED")
    print("="*80)
    print(f"\n✓ Created: {output_path}")
    print(f"\n📊 Stats:")
    print(f"   Total images: {total_images}")
    print(f"   Missing files: {missing_images}")
    print(f"\n🌐 Open in browser:")
    print(f"   open {output_path}")
    print("\n   OR")
    print(f"   file://{output_path.absolute()}")
    print("\n" + "="*80)


def main():
    generate_review_html()


if __name__ == "__main__":
    main()
