#!/usr/bin/env python3
"""
PDF to Markdown Parser for Ultimate Frisbee Rulebooks
Converts USAU and WFDF rulebooks to structured markdown for RAG database use.
"""

import re
import fitz  # PyMuPDF
from pathlib import Path


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract all text from a PDF file."""
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text


def parse_usau_rulebook(text: str) -> str:
    """
    Parse USAU rulebook text into structured markdown.
    USAU uses format: 1.A, 1.B.1, 17.C.2.a, etc.
    """
    lines = text.split('\n')
    markdown_lines = []

    # Add YAML frontmatter for RAG metadata
    markdown_lines.append("---")
    markdown_lines.append("source: usau")
    markdown_lines.append("rulebook: USAU Official Rules of Ultimate 2026-2027")
    markdown_lines.append("version: 2026-2027")
    markdown_lines.append("---")
    markdown_lines.append("")
    markdown_lines.append("# USAU Official Rules of Ultimate 2026-2027")
    markdown_lines.append("")

    # Skip table of contents - find where actual rules start
    in_toc = True
    in_preface = False

    # USAU rule patterns - match at start of line or after whitespace
    # Main rule header: "1. Introduction" or "2. Spirit of the Game"
    main_rule_header = re.compile(r'^(\d{1,2})\.\s+([A-Z][a-zA-Z\s\-]+)$')

    # Appendix header: "Appendix A: Field Diagram"
    appendix_header = re.compile(r'^(Appendix\s+[A-G]):\s*(.+)$')

    # Rule reference pattern: "1.A." or "1.A.1." or "1.A.1.a." or "1.A.1.a.1."
    rule_ref = re.compile(r'^(\d{1,2})\.([A-Z])\.?\s*(.*?)$')
    rule_ref_num = re.compile(r'^(\d{1,2})\.([A-Z])\.(\d+)\.?\s*(.*?)$')
    rule_ref_lower = re.compile(r'^(\d{1,2})\.([A-Z])\.(\d+)\.([a-z])\.?\s*(.*?)$')
    rule_ref_deep = re.compile(r'^(\d{1,2})\.([A-Z])\.(\d+)\.([a-z])\.(\d+)\.?\s*(.*?)$')

    current_rule = ""

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Skip empty lines but preserve paragraph breaks
        if not line:
            if markdown_lines and markdown_lines[-1] != "":
                markdown_lines.append("")
            i += 1
            continue

        # Skip page numbers
        if re.match(r'^\d+$', line):
            i += 1
            continue

        # Detect end of TOC (starts with "Preface" section)
        if line == "Preface":
            in_toc = False
            in_preface = True
            markdown_lines.append("## Preface")
            markdown_lines.append("")
            i += 1
            continue

        # Skip TOC lines
        if in_toc:
            i += 1
            continue

        # Check for main rule header (e.g., "1. Introduction")
        main_match = main_rule_header.match(line)
        if main_match:
            rule_num = main_match.group(1)
            title = main_match.group(2).strip()
            current_rule = rule_num
            in_preface = False
            markdown_lines.append(f"## {rule_num}. {title}")
            markdown_lines.append("")
            markdown_lines.append(f"<!-- section: {rule_num} source: usau -->")
            markdown_lines.append("")
            i += 1
            continue

        # Check for Appendix header
        appendix_match = appendix_header.match(line)
        if appendix_match:
            appendix_id = appendix_match.group(1)
            title = appendix_match.group(2).strip()
            in_preface = False
            markdown_lines.append(f"## {appendix_id}: {title}")
            markdown_lines.append("")
            markdown_lines.append(f"<!-- section: {appendix_id} source: usau -->")
            markdown_lines.append("")
            i += 1
            continue

        # Check for deep rule reference (e.g., "7.C.3.a.1.")
        deep_match = rule_ref_deep.match(line)
        if deep_match:
            main, letter, num, lower, subnum = deep_match.groups()[:5]
            content = deep_match.group(6) if deep_match.lastindex >= 6 else ""
            rule_id = f"{main}.{letter}.{num}.{lower}.{subnum}"
            markdown_lines.append(f"        - **{rule_id}.** {content}")
            markdown_lines.append(f"          <!-- rule: {rule_id} source: usau -->")
            i += 1
            continue

        # Check for lowercase rule reference (e.g., "7.C.3.a.")
        lower_match = rule_ref_lower.match(line)
        if lower_match:
            main, letter, num, lower = lower_match.groups()[:4]
            content = lower_match.group(5) if lower_match.lastindex >= 5 else ""
            rule_id = f"{main}.{letter}.{num}.{lower}"
            markdown_lines.append(f"      - **{rule_id}.** {content}")
            markdown_lines.append(f"        <!-- rule: {rule_id} source: usau -->")
            i += 1
            continue

        # Check for numbered rule reference (e.g., "7.C.3.")
        num_match = rule_ref_num.match(line)
        if num_match:
            main, letter, num = num_match.groups()[:3]
            content = num_match.group(4) if num_match.lastindex >= 4 else ""
            rule_id = f"{main}.{letter}.{num}"
            markdown_lines.append(f"    - **{rule_id}.** {content}")
            markdown_lines.append(f"      <!-- rule: {rule_id} source: usau -->")
            i += 1
            continue

        # Check for letter rule reference (e.g., "7.C.")
        letter_match = rule_ref.match(line)
        if letter_match:
            main, letter = letter_match.groups()[:2]
            content = letter_match.group(3) if letter_match.lastindex >= 3 else ""
            rule_id = f"{main}.{letter}"
            markdown_lines.append(f"### {rule_id}. {content}")
            markdown_lines.append(f"<!-- rule: {rule_id} source: usau -->")
            markdown_lines.append("")
            i += 1
            continue

        # Regular text - append as continuation
        if line:
            # Check if this looks like a continuation of the previous rule
            markdown_lines.append(line)

        i += 1

    return clean_markdown('\n'.join(markdown_lines))


def parse_wfdf_rulebook(text: str) -> str:
    """
    Parse WFDF rulebook text into structured markdown.
    WFDF uses format: 1.1, 1.1.1, 18.2.1.1.1, etc.
    """
    lines = text.split('\n')
    markdown_lines = []

    # Add YAML frontmatter for RAG metadata
    markdown_lines.append("---")
    markdown_lines.append("source: wfdf")
    markdown_lines.append("rulebook: WFDF Rules of Ultimate 2025-2028")
    markdown_lines.append("version: 2025-2028")
    markdown_lines.append("---")
    markdown_lines.append("")
    markdown_lines.append("# WFDF Rules of Ultimate 2025-2028")
    markdown_lines.append("")

    # Skip to actual content (after Contents section)
    in_toc = True
    in_intro = False
    in_definitions = False

    # WFDF patterns
    # Main section: "1. Spirit of the Game" or "1." followed by title on next line
    main_section = re.compile(r'^(\d{1,2})\.\s*$')  # Just number and period
    main_section_titled = re.compile(r'^(\d{1,2})\.\s+([A-Z][a-zA-Z\s\-,]+)$')
    # Also match "1. Spirit of the Game" where number and title are together
    main_section_inline = re.compile(r'^(\d{1,2})\.\s+([A-Z][a-zA-Z\s\-,]+(?:\sand\s[A-Z][a-zA-Z\s\-,]+)?)$')

    # Subsection patterns for WFDF's numeric hierarchy
    # 1.1, 1.1.1, 1.1.1.1, etc.
    subsection_2 = re.compile(r'^(\d{1,2}\.\d+)\.?\s*(.*?)$')
    subsection_3 = re.compile(r'^(\d{1,2}\.\d+\.\d+)\.?\s*(.*?)$')
    subsection_4 = re.compile(r'^(\d{1,2}\.\d+\.\d+\.\d+)\.?\s*(.*?)$')
    subsection_5 = re.compile(r'^(\d{1,2}\.\d+\.\d+\.\d+\.\d+)\.?\s*(.*?)$')

    section_titles = {}
    current_section = ""
    pending_section_num = None

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Skip empty lines
        if not line:
            if markdown_lines and markdown_lines[-1] != "":
                markdown_lines.append("")
            i += 1
            continue

        # Skip page numbers
        if re.match(r'^\d+$', line):
            i += 1
            continue

        # Detect end of TOC
        if line == "Introduction":
            in_toc = False
            in_intro = True
            markdown_lines.append("## Introduction")
            markdown_lines.append("")
            i += 1
            continue

        # Detect Definitions section
        if line == "Definitions":
            in_definitions = True
            markdown_lines.append("## Definitions")
            markdown_lines.append("")
            markdown_lines.append("<!-- section: definitions source: wfdf -->")
            markdown_lines.append("")
            i += 1
            continue

        # Skip TOC
        if in_toc:
            i += 1
            continue

        # Check for main section number alone (WFDF sometimes has just "1." then title on next line)
        main_num_match = main_section.match(line)
        if main_num_match:
            pending_section_num = main_num_match.group(1)
            i += 1
            continue

        # If we have a pending section number, the next non-empty line is the title
        if pending_section_num:
            title = line
            markdown_lines.append(f"## {pending_section_num}. {title}")
            markdown_lines.append("")
            markdown_lines.append(f"<!-- section: {pending_section_num} source: wfdf -->")
            markdown_lines.append("")
            current_section = pending_section_num
            in_intro = False
            pending_section_num = None
            i += 1
            continue

        # Check for main section with title on same line (e.g., "1. Spirit of the Game")
        main_titled_match = main_section_titled.match(line)
        if main_titled_match:
            section_num = main_titled_match.group(1)
            title = main_titled_match.group(2).strip()
            # Only treat as section header if title doesn't look like subsection content
            if not title.startswith(('Ultimate', 'It is', 'Players', 'Highly', 'The following')):
                markdown_lines.append(f"## {section_num}. {title}")
                markdown_lines.append("")
                markdown_lines.append(f"<!-- section: {section_num} source: wfdf -->")
                markdown_lines.append("")
                current_section = section_num
                in_intro = False
                i += 1
                continue

        # Check subsections (deepest first to avoid partial matches)
        sub5_match = subsection_5.match(line)
        if sub5_match:
            rule_num = sub5_match.group(1)
            content = sub5_match.group(2)
            markdown_lines.append(f"          - **{rule_num}.** {content}")
            markdown_lines.append(f"            <!-- rule: {rule_num} source: wfdf -->")
            i += 1
            continue

        sub4_match = subsection_4.match(line)
        if sub4_match:
            rule_num = sub4_match.group(1)
            content = sub4_match.group(2)
            markdown_lines.append(f"        - **{rule_num}.** {content}")
            markdown_lines.append(f"          <!-- rule: {rule_num} source: wfdf -->")
            i += 1
            continue

        sub3_match = subsection_3.match(line)
        if sub3_match:
            rule_num = sub3_match.group(1)
            content = sub3_match.group(2)
            markdown_lines.append(f"      - **{rule_num}.** {content}")
            markdown_lines.append(f"        <!-- rule: {rule_num} source: wfdf -->")
            i += 1
            continue

        sub2_match = subsection_2.match(line)
        if sub2_match:
            rule_num = sub2_match.group(1)
            content = sub2_match.group(2)
            markdown_lines.append(f"### {rule_num}. {content}")
            markdown_lines.append(f"<!-- rule: {rule_num} source: wfdf -->")
            markdown_lines.append("")
            i += 1
            continue

        # Regular text
        if line:
            markdown_lines.append(line)

        i += 1

    return clean_markdown('\n'.join(markdown_lines))


def clean_markdown(text: str) -> str:
    """Clean up the markdown output."""
    # Remove excessive blank lines (more than 2)
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Fix any encoding issues
    text = text.encode('utf-8', errors='ignore').decode('utf-8')
    return text.strip() + '\n'


def create_chunked_output(markdown_text: str, source: str, output_dir: Path):
    """
    Create individual chunk files for each rule section.
    This format is optimized for RAG ingestion.
    """
    chunks_dir = output_dir / f"{source}_chunks"
    chunks_dir.mkdir(exist_ok=True)

    # Split by main sections (## headers)
    sections = re.split(r'(?=^## )', markdown_text, flags=re.MULTILINE)

    chunk_index = []

    for section in sections:
        if not section.strip():
            continue

        # Extract section title
        title_match = re.match(r'^## (.+?)$', section, re.MULTILINE)
        if title_match:
            title = title_match.group(1).strip()
            # Create safe filename
            safe_title = re.sub(r'[^\w\s\-]', '', title)
            safe_title = re.sub(r'\s+', '_', safe_title)[:50]

            filename = f"{safe_title}.md"
            filepath = chunks_dir / filename

            # Add frontmatter to chunk
            chunk_content = f"---\nsource: {source}\nsection: {title}\n---\n\n{section}"

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(chunk_content)

            chunk_index.append({
                'file': filename,
                'section': title,
                'source': source
            })

    # Write index file
    index_file = chunks_dir / "_index.md"
    with open(index_file, 'w', encoding='utf-8') as f:
        f.write(f"# {source.upper()} Rule Chunks Index\n\n")
        for item in chunk_index:
            f.write(f"- [{item['section']}]({item['file']})\n")

    return len(chunk_index)


def main():
    """Main function to parse both rulebooks."""
    base_path = Path(__file__).parent.parent
    rulebooks_path = base_path / "rulebooks"
    output_path = base_path / "parsed_rules"

    # Create output directory
    output_path.mkdir(exist_ok=True)

    # Parse USAU rulebook
    usau_pdf = rulebooks_path / "USAU-2026-2027.pdf"
    if usau_pdf.exists():
        print(f"Parsing USAU rulebook: {usau_pdf}")
        usau_text = extract_text_from_pdf(str(usau_pdf))
        usau_markdown = parse_usau_rulebook(usau_text)

        usau_output = output_path / "usau_rules.md"
        with open(usau_output, 'w', encoding='utf-8') as f:
            f.write(usau_markdown)
        print(f"USAU rules saved to: {usau_output}")

        # Create chunked output for RAG
        num_chunks = create_chunked_output(usau_markdown, "usau", output_path)
        print(f"Created {num_chunks} USAU chunks for RAG ingestion")
    else:
        print(f"USAU PDF not found: {usau_pdf}")

    # Parse WFDF rulebook
    wfdf_pdf = rulebooks_path / "WFDF-2025-2028.pdf"
    if wfdf_pdf.exists():
        print(f"Parsing WFDF rulebook: {wfdf_pdf}")
        wfdf_text = extract_text_from_pdf(str(wfdf_pdf))
        wfdf_markdown = parse_wfdf_rulebook(wfdf_text)

        wfdf_output = output_path / "wfdf_rules.md"
        with open(wfdf_output, 'w', encoding='utf-8') as f:
            f.write(wfdf_markdown)
        print(f"WFDF rules saved to: {wfdf_output}")

        # Create chunked output for RAG
        num_chunks = create_chunked_output(wfdf_markdown, "wfdf", output_path)
        print(f"Created {num_chunks} WFDF chunks for RAG ingestion")
    else:
        print(f"WFDF PDF not found: {wfdf_pdf}")

    print("\nParsing complete!")
    print(f"\nOutput files:")
    print(f"  - {output_path}/usau_rules.md (full document)")
    print(f"  - {output_path}/wfdf_rules.md (full document)")
    print(f"  - {output_path}/usau_chunks/ (individual sections for RAG)")
    print(f"  - {output_path}/wfdf_chunks/ (individual sections for RAG)")


if __name__ == "__main__":
    main()
