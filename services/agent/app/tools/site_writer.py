"""Write site files from LLM output."""
import re
from pathlib import Path
from typing import Optional


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
    session_dir.mkdir(parents=True, exist_ok=True)
    output_path = session_dir / filename
    
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
