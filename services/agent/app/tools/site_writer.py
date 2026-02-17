"""Write site files from LLM output."""
import re
from pathlib import Path
from typing import Optional, List


def extract_html_from_response(text: str) -> Optional[str]:
    """
    Extract HTML content from LLM response.
    
    Handles cases where LLM wraps HTML in markdown code blocks.
    """
    # Remove markdown code blocks if present
    text = text.strip()
    
    # Try to extract from ```html or ``` blocks
    html_match = re.search(r'```(?:html)?\s*\n(.*?)\n```', text, re.DOTALL)
    if html_match:
        return html_match.group(1).strip()
    
    # If it starts with <!DOCTYPE or <html, assume it's raw HTML
    if text.startswith("<!DOCTYPE") or text.startswith("<html"):
        return text.strip()
    
    # Try to find HTML between any code fences
    html_match = re.search(r'```.*?\n(.*?)```', text, re.DOTALL)
    if html_match:
        return html_match.group(1).strip()
    
    # Last resort: return as-is if it contains HTML tags
    if "<html" in text or "<!DOCTYPE" in text:
        return text.strip()
    
    return None


def split_multiple_pages(html_content: str) -> List[tuple[str, str]]:
    """
    Split LLM output into multiple page files.
    
    Expected format:
    === index.html ===
    <!DOCTYPE html>...
    
    === pages/privacy.html ===
    <!DOCTYPE html>...
    
    Returns list of (filename, content) tuples.
    """
    pages = []
    
    # Look for === filename === pattern
    pattern = r'===?\s*([^\n=]+?)\s*===?\s*\n(.*?)(?=\n===?\s*[^\n=]+?\s*===?\s*\n|$)'
    matches = re.finditer(pattern, html_content, re.DOTALL)
    
    for match in matches:
        filename = match.group(1).strip()
        content = match.group(2).strip()
        if filename and content:
            pages.append((filename, content))
    
    # If no matches found, treat entire content as index.html
    if not pages:
        # Try to extract from markdown code blocks
        html_extracted = extract_html_from_response(html_content)
        if html_extracted:
            pages.append(("index.html", html_extracted))
        else:
            pages.append(("index.html", html_content))
    
    return pages


def write_site_file(session_dir: Path, html_content: str, filename: str = "index.html") -> Path:
    """
    Write HTML content to a file in the session directory.
    
    Args:
        session_dir: Directory to write to
        html_content: HTML content to write
        filename: Output filename (default: index.html)
    
    Returns:
        Path to the written file
    """
    # Handle nested paths (e.g., pages/privacy.html)
    output_path = session_dir / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Extract HTML if wrapped in markdown
    clean_html = extract_html_from_response(html_content)
    if clean_html is None:
        # If extraction failed, try to use raw content
        clean_html = html_content
    
    # Ensure it's valid HTML
    if not clean_html.strip().startswith("<!DOCTYPE"):
        # Wrap in basic HTML structure if needed
        clean_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Generated Site</title>
</head>
<body>
{clean_html}
</body>
</html>"""
    
    output_path.write_text(clean_html, encoding="utf-8")
    return output_path


def write_multiple_pages(session_dir: Path, full_response: str) -> List[Path]:
    """
    Write multiple HTML pages from LLM response.
    
    Args:
        session_dir: Directory to write to
        full_response: Full LLM response containing multiple pages
    
    Returns:
        List of paths to written files
    """
    pages = split_multiple_pages(full_response)
    written_files = []
    
    for filename, content in pages:
        file_path = write_site_file(session_dir, content, filename)
        written_files.append(file_path)
    
    return written_files
