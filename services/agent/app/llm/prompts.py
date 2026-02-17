"""Prompts for site generation."""
from datetime import datetime
from typing import List


def get_site_generation_prompt(user_prompt: str, conversation_history: List[dict]) -> List[dict]:
    """
    Build the prompt for site generation.
    
    Returns a list of messages in OpenAI chat format.
    """
    current_year = datetime.now().year
    
    system_prompt = f"""You are a helpful web developer that generates clean, simple static websites.

Current year: {current_year}

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
- Use modern CSS (flexbox/grid) for layout
- Add subtle animations and hover effects for better UX

IMAGES:
- DO NOT use external image URLs or download images
- Instead, use minimalistic color blocks or gradients as placeholders
- Create simple geometric shapes with CSS or inline SVG
- Use CSS gradients, solid colors, or simple SVG patterns
- Example: Use <div> with background gradients instead of <img src="...">
- For icons, use inline SVG only

MULTI-PAGE SITES:
- If the site needs multiple pages (like privacy, terms, contact, about), you MUST generate ALL pages
- Create a main index.html with navigation
- Generate separate HTML files for each linked page (e.g., pages/privacy.html, pages/terms.html, pages/contact.html)
- Each page should be a complete, self-contained HTML file
- All pages should be in the same response, separated clearly
- Format: Generate index.html first, then clearly mark each additional page
- Use relative paths for navigation links (e.g., href="pages/privacy.html")

OUTPUT FORMAT:
- For single page: Return the complete HTML file content, nothing else
- For multi-page: Return all HTML files, clearly separated
- Format: 
  === index.html ===
  <!DOCTYPE html>...
  
  === pages/privacy.html ===
  <!DOCTYPE html>...
  
  === pages/terms.html ===
  <!DOCTYPE html>...
  
- No markdown code blocks, no explanations
- Start directly with <!DOCTYPE html> for each file"""

    # Build conversation context with all messages
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add ALL conversation history for full context
    for msg in conversation_history:
        if msg.get("role") in ["user", "assistant"]:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
    
    # Add generation instruction with context
    context_summary = "Based on our conversation, "
    if len(conversation_history) > 1:
        context_summary = f"Based on our {len(conversation_history)} message conversation, "
    
    messages.append({
        "role": "user",
        "content": f"{context_summary}generate a complete static website. Current year is {current_year}. "
                   f"Use minimalistic color blocks/gradients instead of images. "
                   f"If you create navigation links to other pages, generate ALL those pages as separate HTML files. "
                   f"Make it modern, responsive, and visually appealing."
    })
    
    return messages


def get_chat_response_prompt(user_message: str, conversation_history: List[dict]) -> List[dict]:
    """
    Build prompt for agent chat responses (when user clicks Send).
    
    Returns a list of messages for conversational response.
    """
    current_year = datetime.now().year
    
    system_prompt = f"""You are a helpful AI assistant that helps users create websites. 
Current year: {current_year}

You help users describe what kind of website they want to build. Be friendly, encouraging, and ask clarifying questions if needed.
Keep responses concise and helpful. When the user is ready, they will click "Generate" to build the website."""

    messages = [{"role": "system", "content": system_prompt}]
    
    # Add conversation history
    for msg in conversation_history:
        if msg.get("role") in ["user", "assistant"]:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
    
    # Add current user message
    messages.append({
        "role": "user",
        "content": user_message
    })
    
    return messages
