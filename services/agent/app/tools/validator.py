"""Validate generated site files."""
from pathlib import Path
from typing import List, Tuple


def validate_site(site_dir: Path) -> Tuple[bool, List[str]]:
    """
    Validate a generated site.
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Check if index.html exists
    index_path = site_dir / "index.html"
    if not index_path.exists():
        errors.append("index.html not found")
        return False, errors
    
    # Check if index.html is readable
    try:
        content = index_path.read_text(encoding="utf-8")
        if not content.strip():
            errors.append("index.html is empty")
    except Exception as e:
        errors.append(f"Failed to read index.html: {e}")
        return False, errors
    
    # Basic HTML structure check
    content_lower = content.lower()
    if "<html" not in content_lower and "<!doctype" not in content_lower:
        errors.append("index.html does not appear to be valid HTML")
    
    return len(errors) == 0, errors
