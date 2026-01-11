#!/usr/bin/env python3
"""
Extract images from Ultimate Frisbee rulebook PDFs.
"""

import fitz  # PyMuPDF
from pathlib import Path


def extract_images_from_pdf(pdf_path: Path, output_dir: Path, prefix: str):
    """Extract all images from a PDF and save them."""
    doc = fitz.open(str(pdf_path))
    output_dir.mkdir(parents=True, exist_ok=True)

    extracted = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        image_list = page.get_images(full=True)

        for img_index, img_info in enumerate(image_list):
            xref = img_info[0]  # xref number

            # Extract image
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]

            # Generate filename based on page and content
            filename = f"{prefix}_page{page_num + 1}_img{img_index + 1}.{image_ext}"
            filepath = output_dir / filename

            # Save image
            with open(filepath, "wb") as f:
                f.write(image_bytes)

            extracted.append({
                'file': filename,
                'page': page_num + 1,
                'size': len(image_bytes),
                'format': image_ext
            })

            print(f"  Extracted: {filename} ({len(image_bytes)} bytes)")

    doc.close()
    return extracted


def create_image_index(images: list, output_dir: Path, source: str):
    """Create an index markdown file for the images."""
    index_path = output_dir / "_index.md"

    with open(index_path, 'w') as f:
        f.write(f"# {source.upper()} Rulebook Images\n\n")
        f.write("Images extracted from the official rulebook PDF.\n\n")

        for img in images:
            f.write(f"## Page {img['page']} - {img['file']}\n\n")
            f.write(f"![{img['file']}]({img['file']})\n\n")
            f.write(f"- Format: {img['format']}\n")
            f.write(f"- Size: {img['size']} bytes\n\n")


def main():
    base_path = Path(__file__).parent.parent
    rulebooks_path = base_path / "rulebooks"
    images_path = base_path / "parsed_rules" / "images"

    # Extract from USAU
    usau_pdf = rulebooks_path / "USAU-2026-2027.pdf"
    if usau_pdf.exists():
        print(f"Extracting images from USAU rulebook...")
        usau_images_dir = images_path / "usau"
        usau_images = extract_images_from_pdf(usau_pdf, usau_images_dir, "usau")
        if usau_images:
            create_image_index(usau_images, usau_images_dir, "usau")
            print(f"  Total: {len(usau_images)} images extracted")
        else:
            print("  No images found in USAU PDF")

    # Extract from WFDF
    wfdf_pdf = rulebooks_path / "WFDF-2025-2028.pdf"
    if wfdf_pdf.exists():
        print(f"\nExtracting images from WFDF rulebook...")
        wfdf_images_dir = images_path / "wfdf"
        wfdf_images = extract_images_from_pdf(wfdf_pdf, wfdf_images_dir, "wfdf")
        if wfdf_images:
            create_image_index(wfdf_images, wfdf_images_dir, "wfdf")
            print(f"  Total: {len(wfdf_images)} images extracted")
        else:
            print("  No images found in WFDF PDF")

    print("\nImage extraction complete!")


if __name__ == "__main__":
    main()
