"""Prompts for site generation."""
from typing import List


def get_site_generation_prompt(user_prompt: str, conversation_history: List[dict]) -> List[dict]:
    """
    Build the prompt for site generation.
    
    Returns a list of messages in OpenAI chat format.
    """
    system_prompt = """You are a helpful web developer that generates clean, simple static websites.

Given a user's request, generate a complete HTML page with embedded CSS and JavaScript if needed.

Requirements:
- Output ONLY valid HTML (with <!DOCTYPE html>)
- Include all CSS in <style> tags in the <head>
- Include all JavaScript in <script> tags before </body>
- Keep it simple, clean, and modern
- Make it responsive
- Use semantic HTML5 elements
- The page should be self-contained (no external dependencies unless necessary)
- Use inline SVG for icons (simple shapes, no external files)
- If the site needs multiple pages (like privacy, terms, contact), create a simple navigation structure
- Use modern CSS (flexbox/grid) for layout
- Add subtle animations and hover effects for better UX

For multi-page sites:
- Create a main index.html with navigation
- Include links to /pages/privacy.html, /pages/terms.html, /pages/contact.html if mentioned
- Each page should be self-contained HTML files

Output format:
Return the complete HTML file content, nothing else. No markdown code blocks, no explanations.
Start directly with <!DOCTYPE html>."""

    # Build conversation context
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add conversation history
    for msg in conversation_history:
        if msg.get("role") in ["user", "assistant"]:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
    
    # Add current user prompt if not already in history
    if not conversation_history or conversation_history[-1].get("content") != user_prompt:
        messages.append({
            "role": "user",
            "content": f"Generate a static website for: {user_prompt}. Include all necessary pages, styles, and inline SVG icons."
        })
    
    return messages
