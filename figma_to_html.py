"""
Figma to HTML/CSS Converter 
Fixed: class name conflicts, input detection, structure, text colors
"""

import requests
import json
import re
import math
from typing import Dict, List, Any, Optional, Tuple


class FigmaToHTMLConverter:
    def __init__(self, figma_token: str, file_key: str):
        self.figma_token = figma_token
        self.file_key = file_key
        self.base_url = "https://api.figma.com/v1"
        self.headers = {"X-Figma-Token": figma_token}
        
        self.fonts = set()
        self.used_class_names = set()
        self.component_counter = 0
        
    def fetch_file(self) -> Dict:
        """Fetch the Figma file data"""
        url = f"{self.base_url}/files/{self.file_key}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def rgba_to_css(self, color: Dict) -> str:
        """Convert Figma RGBA to CSS"""
        if not color:
            return "transparent"
        
        r = int(color.get('r', 0) * 255)
        g = int(color.get('g', 0) * 255)
        b = int(color.get('b', 0) * 255)
        a = color.get('a', 1)
        
        if a == 1:
            return f"#{r:02x}{g:02x}{b:02x}"
        return f"rgba({r}, {g}, {b}, {a})"
    
    def extract_gradient(self, fill: Dict) -> Optional[str]:
        """Improved gradient extraction."""
        if fill.get('type') != 'GRADIENT_LINEAR':
            return None

        stops = fill.get('gradientStops', [])
        if not stops:
            return None

        handles = fill.get('gradientHandlePositions', [])
        if len(handles) >= 2:
            x1, y1 = handles[0]['x'], handles[0]['y']
            x2, y2 = handles[1]['x'], handles[1]['y']
            rad = math.atan2(y2 - y1, x2 - x1)
            deg = (math.degrees(rad) + 450) % 360  # fix rotation offset
        else:
            deg = 90

        gradient_stops = []
        for stop in stops:
            color = self.rgba_to_css(stop['color'])
            pos = int(stop.get('position', 0) * 100)
            gradient_stops.append(f"{color} {pos}%")

        return f"linear-gradient({deg:.0f}deg, {', '.join(gradient_stops)})"

    
    def get_background(self, node: Dict) -> str:
        """Get background CSS"""
        fills = node.get('fills', [])
        visible_fills = [f for f in fills if f.get('visible', True)]
        
        if not visible_fills:
            return "transparent"
        
        fill = visible_fills[0]
        
        if fill['type'] == 'SOLID':
            return self.rgba_to_css(fill.get('color'))
        elif fill['type'] == 'GRADIENT_LINEAR':
            gradient = self.extract_gradient(fill)
            return gradient if gradient else "transparent"
        
        return "transparent"
    
    def get_border_css(self, node: Dict) -> Optional[str]:
        """Get border CSS"""
        strokes = node.get('strokes', [])
        visible_strokes = [s for s in strokes if s.get('visible', True)]
        
        if not visible_strokes:
            return None
        
        stroke_weight = node.get('strokeWeight', 0)
        if stroke_weight == 0:
            return None
        
        
        stroke_color = self.rgba_to_css(visible_strokes[0].get('color'))
        return f"{stroke_weight}px solid {stroke_color}"
    

    
    def get_border_radius(self, node: Dict) -> str:
        """Get border radius CSS"""
        radius = node.get('cornerRadius', 0)
        corners = node.get('rectangleCornerRadii', [])
        
        if corners and len(corners) == 4:
            if all(c == corners[0] for c in corners):
                return f"{corners[0]}px" if corners[0] > 0 else "0"
            return f"{corners[0]}px {corners[1]}px {corners[2]}px {corners[3]}px"
        
        return f"{radius}px" if radius > 0 else "0"
    
    def get_text_style(self, node: Dict) -> Dict[str, str]:
        style = node.get('style', {})
        fills = node.get('fills', [])

        color = "#000"
        if fills and fills[0].get('visible', True):
            color = self.rgba_to_css(fills[0].get('color'))

        css = {
            'font-family': f"'{style.get('fontFamily', 'Inter')}', sans-serif",
            'font-size': f"{style.get('fontSize', 16)}px",
            'font-weight': str(style.get('fontWeight', 400)),
            'color': color,
            'line-height': f"{style.get('lineHeightPx', style.get('fontSize', 16)*1.2)}px",
        }

        if 'textAlignHorizontal' in style:
            align_map = {'CENTER': 'center', 'RIGHT': 'right', 'LEFT': 'left'}
            css['text-align'] = align_map.get(style['textAlignHorizontal'], 'left')

        if 'letterSpacing' in style:
            css['letter-spacing'] = f"{style['letterSpacing']}px"

        if 'paragraphSpacing' in style and style['paragraphSpacing'] > 0:
            css['margin-bottom'] = f"{style['paragraphSpacing']}px"

        return css

    
    def get_layout_css(self, node: Dict) -> Dict[str, str]:
        """Get layout CSS"""
        css = {}
        
        bounds = node.get('absoluteBoundingBox', {})
        width = bounds.get('width')
        height = bounds.get('height')
        
        if width:
            css['width'] = f"{width}px"
        if height:
            css['height'] = f"{height}px"
        
        pt = node.get('paddingTop', 0)
        pr = node.get('paddingRight', 0)
        pb = node.get('paddingBottom', 0)
        pl = node.get('paddingLeft', 0)
        
        if any([pt, pr, pb, pl]):
            if pt == pr == pb == pl:
                css['padding'] = f"{pt}px"
            else:
                css['padding'] = f"{pt}px {pr}px {pb}px {pl}px"
        
        layout_mode = node.get('layoutMode')
        if layout_mode in ['HORIZONTAL', 'VERTICAL']:
            css['display'] = 'flex'
            css['flex-direction'] = 'column' if layout_mode == 'VERTICAL' else 'row'
            
            gap = node.get('itemSpacing', 0)
            if gap > 0:
                css['gap'] = f"{gap}px"
            
            primary = node.get('primaryAxisAlignItems', 'MIN')
            counter = node.get('counterAxisAlignItems', 'MIN')
            
            align_map = {
                'MIN': 'flex-start',
                'CENTER': 'center',
                'MAX': 'flex-end',
                'SPACE_BETWEEN': 'space-between'
            }
            
            css['align-items'] = align_map.get(counter, 'flex-start')
            css['justify-content'] = align_map.get(primary, 'flex-start')

            if node.get('layoutMode') is None:
                # Try to infer centering from absolute bounding boxes
                if node.get('absoluteBoundingBox'):
                    abs_box = node['absoluteBoundingBox']
                    if abs_box.get('x', 0) > 0:
                        css['margin-left'] = f"{abs_box['x']}px"
                    if abs_box.get('y', 0) > 0:
                        css['margin-top'] = f"{abs_box['y']}px"
        
        return css
    
    def get_all_text_from_children(self, node: Dict) -> List[str]:
        """Get all text content from children"""
        texts = []
        for child in node.get('children', []):
            if child.get('type') == 'TEXT':
                texts.append(child.get('characters', ''))
        return texts
    
    def is_input_container(self, node: Dict) -> Tuple[bool, str, str, bool]:
        """
        Check if this frame should be converted to an input
        Returns: (is_input, type, text, is_value)
        """
        # Get dimensions
        bounds = node.get('absoluteBoundingBox', {})
        height = bounds.get('height', 999)
        width = bounds.get('width', 0)
        
        # Must be input-sized (not too large)
        if height > 100 or width < 100:
            return False, '', '', False
        
        # Must have border (inputs have borders)
        if not self.get_border_css(node):
            return False, '', '', False
        
        # Get text content
        texts = self.get_all_text_from_children(node)
        if not texts or len(texts) != 1:
            return False, '', '', False
        
        text = texts[0]
        text_lower = text.lower()
        
        # Check for password
        if 'password' in text_lower:
            return True, 'password', 'Password', False
        
        # Check for email (has @)
        if '@' in text:
            return True, 'email', text, True
        
        # Check for other input patterns
        if any(word in text_lower for word in ['email', 'username', 'search']):
            return True, 'text', text, False
        
        return False, '', '', False
    
    def is_button_container(self, node: Dict) -> Tuple[bool, str]:
        """
        Check if this frame should be a button
        Returns: (is_button, button_text)
        """
        # Get background - buttons have backgrounds
        bg = self.get_background(node)
        if bg == "transparent":
            return False, ''
        
        # Get dimensions
        bounds = node.get('absoluteBoundingBox', {})
        height = bounds.get('height', 0)
        width = bounds.get('width', 0)
        
        # Button-like size
        if not (30 <= height <= 80 and width > 100):
            return False, ''
        
        # Must have high border radius
        radius = node.get('cornerRadius', 0)
        if radius < 30:  # Buttons typically have high radius
            return False, ''
        
        # Get text
        texts = self.get_all_text_from_children(node)
        if not texts or len(texts) != 1:
            return False, ''
        
        text = texts[0]
        
        # Check for button-like text
        text_lower = text.lower()
        if any(word in text_lower for word in ['sign', 'create', 'submit', 'continue', 'next', 'back']):
            return True, text
        
        return False, ''
    
    def is_link_text(self, node: Dict) -> bool:
        """Check if TEXT node should be a link"""
        if node.get('type') != 'TEXT':
            return False
        
        text = node.get('characters', '').lower()
        style = node.get('style', {})
        font_size = style.get('fontSize', 16)
        
        # Small text with link-like content
        if font_size <= 14 and any(word in text for word in ['forgot', 'help', 'learn', 'more info']):
            return True
        
        return False
    
    def get_heading_level(self, node: Dict) -> Optional[str]:
        """Determine if TEXT should be a heading"""
        if node.get('type') != 'TEXT':
            return None
        
        style = node.get('style', {})
        font_size = style.get('fontSize', 16)
        font_weight = style.get('fontWeight', 400)
        
        # Large, bold text = heading
        if font_size >= 40 and font_weight >= 700:
            return 'h1'
        elif font_size >= 28 and font_weight >= 600:
            return 'h2'
        elif font_size >= 20 and font_weight >= 600:
            return 'h3'
        
        return None
    
    def generate_unique_class_name(self, node: Dict) -> str:
        """
        Generate semantic class names using node roles.
        """
        name = node.get('name', '').lower()
        node_type = node.get('type', '').lower()

        # Base heuristic names
        if 'button' in name:
            base = 'button'
        elif 'input' in name or 'field' in name:
            base = 'input'
        elif 'frame' in name and 'phone' in name:
            base = 'phone-frame'
        elif 'text' in name or node_type == 'text':
            base = 'text'
        elif 'icon' in name:
            base = 'icon'
        elif 'card' in name:
            base = 'card'
        elif 'container' in name:
            base = 'container'
        else:
            base = node_type or 'layer'

        # Normalize
        base = re.sub(r'[^a-z0-9-]', '-', base).strip('-')
        if not base:
            base = 'component'

        # Ensure uniqueness
        counter = 1
        new_name = base
        while new_name in self.used_class_names:
            new_name = f"{base}-{counter}"
            counter += 1

        self.used_class_names.add(new_name)
        return new_name

    
    def collect_styles(self, node: Dict) -> Dict[str, str]:
        """Collect CSS styles for node"""
        css = {}
        node_type = node.get('type')
        
        # Background (for containers, not text)
        if node_type != 'TEXT':
            bg = self.get_background(node)
            if bg != "transparent":
                css['background'] = bg

        # Extract drop shadow
        effects = node.get('effects', [])
        visible_effects = [e for e in effects if e.get('visible', True) and e.get('type') == 'DROP_SHADOW']
        if visible_effects:
            shadow = visible_effects[0]
            color = self.rgba_to_css(shadow.get('color'))
            offset = shadow.get('offset', {})
            blur = shadow.get('radius', 0)
            css['box-shadow'] = f"{offset.get('x', 0)}px {offset.get('y', 0)}px {blur}px {color}"
        
        # Border
        border = self.get_border_css(node)
        if border:
            css['border'] = border
        
        # Border radius
        radius = self.get_border_radius(node)
        if radius != "0":
            css['border-radius'] = radius
        
        # Layout
        layout_css = self.get_layout_css(node)
        css.update(layout_css)
        
        # Text styles (COLOR, not background)
        if node_type == 'TEXT':
            text_css = self.get_text_style(node)
            css.update(text_css)
        
        # Opacity
        opacity = node.get('opacity', 1)
        if opacity < 1:
            css['opacity'] = str(opacity)
        
        # Position relative for non-auto-layout containers with children
        if node_type in ['FRAME', 'GROUP'] and not node.get('layoutMode'):
            if len(node.get('children', [])) > 1:
                css['position'] = 'relative'
        
        return css
    
    def traverse_and_generate(self, node: Dict, depth: int = 0) -> Tuple[str, Dict]:
        """
        Traverse and generate HTML/CSS
        Returns: (html, css_dict)
        """
        if not node.get('visible', True):
            return '', {}
        
        node_type = node.get('type')
        class_name = self.generate_unique_class_name(node)
        
        # Collect styles
        css_rules = self.collect_styles(node)
        all_css = {class_name: css_rules} if css_rules else {}
        
        html = ''
        
        # Handle TEXT nodes
        if node_type == 'TEXT':
            text = node.get('characters', '')
            
            # Check if link
            if self.is_link_text(node):
                html = f'<a href="#" class="{class_name}">{text}</a>'
            else:
                # Check if heading
                heading = self.get_heading_level(node)
                if heading:
                    html = f'<{heading} class="{class_name}">{text}</{heading}>'
                else:
                    html = f'<span class="{class_name}">{text}</span>'
        
        # Handle container nodes
        elif node_type in ['FRAME', 'GROUP', 'COMPONENT', 'INSTANCE', 'RECTANGLE']:
            # Check if input
            is_input, input_type, input_text, is_value = self.is_input_container(node)
            if is_input:
                attrs = [f'class="{class_name}"', f'type="{input_type}"']
                if is_value:
                    attrs.append(f'value="{input_text}"')
                else:
                    attrs.append(f'placeholder="{input_text}"')
                return f'<input {" ".join(attrs)}>', all_css
            
            # Check if button
            is_button, button_text = self.is_button_container(node)
            if is_button:
                return f'<button class="{class_name}">{button_text}</button>', all_css
            
            # Regular container - process children
            children = node.get('children', [])
            children_html = []
            
            for child in children:
                child_html, child_css = self.traverse_and_generate(child, depth + 1)
                if child_html:
                    children_html.append(child_html)
                all_css.update(child_css)

            if class_name.startswith('input') or class_name.startswith('button'):
                wrapper_tag = 'div'
                html = f'<{wrapper_tag} class="{class_name}">\n{indent}{children_str}\n{"  " * depth}</{wrapper_tag}>'
    
            # Build HTML
            if children_html:
                indent = '  ' * (depth + 1)
                children_str = f'\n{indent}'.join(children_html)
                html = f'<div class="{class_name}">\n{indent}{children_str}\n{"  " * depth}</div>'
            else:
                html = f'<div class="{class_name}"></div>'
        
        return html, all_css
    
    def css_dict_to_string(self, css_dict: Dict[str, Dict[str, str]]) -> str:
        """Convert CSS dict to string"""
        lines = []
        
        lines.append("""* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Inter', sans-serif;
    background: #e5e5e5;
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    padding: 20px;
}
""")
        
        for class_name, props in css_dict.items():
            if not props:
                continue
            
            lines.append(f".{class_name} {{")
            for prop, value in sorted(props.items()):
                lines.append(f"    {prop}: {value};")
            lines.append("}\n")
        
        lines.append("""
input {
    outline: none;
    font-family: inherit;
}

input:focus {
    border-color: #95228C;
}

button {
    cursor: pointer;
    transition: transform 0.2s, opacity 0.2s;
}

button:hover {
    opacity: 0.9;
}

button:active {
    transform: scale(0.98);
}

a {
    text-decoration: none;
}

a:hover {
    opacity: 0.8;
}
""")

        lines.append("""
@media (max-width: 420px) {
    body {
        padding: 10px;
    }
    [class*="frame"], [class*="container"], [class*="phone-frame"] {
        width: 100%;
        max-width: 393px;
        height: auto;
        min-height: 852px;
    }
}
""")
        
        return '\n'.join(lines)
    
    def generate_google_fonts_link(self) -> str:
        """Generate Google Fonts link"""
        if not self.fonts:
            self.fonts.add('Inter')
        
        fonts_param = []
        for font in self.fonts:
            fonts_param.append(f"{font.replace(' ', '+')}:wght@400;500;600;700")
        
        fonts_str = '&family='.join(fonts_param)
        return f'<link href="https://fonts.googleapis.com/css2?family={fonts_str}&display=swap" rel="stylesheet">'
    
    def generate_html_document(self, body_html: str, css: str) -> str:
        """Generate complete HTML"""
        google_fonts = self.generate_google_fonts_link()
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Figma Design</title>
    {google_fonts}
    <style>
{css}
    </style>
</head>
<body>
{body_html}
</body>
</html>"""
    
    def convert(self, node_id: str = None, output_file: str = "output.html"):
        """Convert Figma to HTML/CSS"""
        print("🔍 Fetching Figma file...")
        data = self.fetch_file()
        print(f"✅ File: {data.get('name', 'Unknown')}")
        
        document = data.get('document', {})
        canvas = document.get('children', [{}])[0]
        
        target_node = None
        if node_id:
            def find_node(node, target_id):
                if node.get('id') == target_id:
                    return node
                for child in node.get('children', []):
                    result = find_node(child, target_id)
                    if result:
                        return result
                return None
            target_node = find_node(canvas, node_id)
        else:
            frames = [c for c in canvas.get('children', []) if c.get('type') == 'FRAME']
            target_node = frames[0] if frames else None
        
        if not target_node:
            raise ValueError("Target node not found")
        
        print(f"🎨 Converting: {target_node.get('name', 'Unnamed')}")
        
        html_body, css_dict = self.traverse_and_generate(target_node)
        css_string = self.css_dict_to_string(css_dict)
        html_output = self.generate_html_document(html_body, css_string)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_output)
        
        print(f"✅ Generated: {output_file}")
        return html_output


def main():
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python figma_to_html.py <FIGMA_TOKEN> <FILE_KEY> [NODE_ID] [OUTPUT_FILE]")
        print("\nExample:")
        print("  python figma_to_html.py your-token MxMXpjiLPbdHlratvH0Wdy 0:1 output.html")
        sys.exit(1)
    
    token = sys.argv[1]
    file_key = sys.argv[2]
    node_id = sys.argv[3] if len(sys.argv) > 3 else None
    output = sys.argv[4] if len(sys.argv) > 4 else "output.html"
    
    converter = FigmaToHTMLConverter(token, file_key)
    converter.convert(node_id, output)


if __name__ == "__main__":
    main()