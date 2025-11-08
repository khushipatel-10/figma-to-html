"""
Updated Figma to HTML/CSS Converter 

"""

import requests
import json
import re
from typing import Dict, List, Any, Optional, Tuple


class FigmaToHTMLConverter:
    def __init__(self, figma_token: str, file_key: str):
        self.figma_token = figma_token
        self.file_key = file_key
        self.base_url = "https://api.figma.com/v1"
        self.headers = {"X-Figma-Token": figma_token}
        
        self.fonts = set()
        self.used_class_names = set()
        
    def fetch_file(self) -> Dict:
        """Fetch the Figma file JSON data"""
        url = f"{self.base_url}/files/{self.file_key}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def rgba_to_css(self, color: Dict) -> str:
        """Convert Figma RGBA to CSS color"""
        if not color:
            return "transparent"
        
        r = int(color.get('r', 0) * 255)
        g = int(color.get('g', 0) * 255)
        b = int(color.get('b', 0) * 255)
        a = color.get('a', 1)
        
        if a == 1:
            return f"#{r:02X}{g:02X}{b:02X}"
        return f"rgba({r}, {g}, {b}, {a})"
    
    def extract_gradient_css(self, fill: Dict) -> Optional[str]:
        """Extract gradient CSS from Figma gradient data"""
        if fill.get('type') != 'GRADIENT_LINEAR':
            return None
        
        stops = fill.get('gradientStops', [])
        if not stops:
            return None
        
        handles = fill.get('gradientHandlePositions', [])
        if len(handles) >= 2:
            import math
            x1, y1 = handles[0]['x'], handles[0]['y']
            x2, y2 = handles[1]['x'], handles[1]['y']
            
            dx = x2 - x1
            dy = y2 - y1
            
            rad = math.atan2(dy, dx)
            deg = math.degrees(rad)
            css_angle = (90 - deg) % 360
        else:
            css_angle = 180
        
        gradient_stops = []
        for stop in stops:
            color = self.rgba_to_css(stop['color'])
            pos = stop.get('position', 0) * 100
            gradient_stops.append(f"{color} {pos:.2f}%")
        
        return f"linear-gradient({css_angle:.2f}deg, {', '.join(gradient_stops)})"
    
    def get_unique_class_name(self, base_name: str) -> str:
        """Generate unique class name"""
        # Clean the name
        clean = re.sub(r'[^a-z0-9-]', '-', base_name.lower())
        clean = re.sub(r'-+', '-', clean).strip('-')
        
        if not clean or clean[0].isdigit():
            clean = f"node-{clean}"
        
        # Make unique
        if clean not in self.used_class_names:
            self.used_class_names.add(clean)
            return clean
        
        counter = 2
        while f"{clean}-{counter}" in self.used_class_names:
            counter += 1
        
        final_name = f"{clean}-{counter}"
        self.used_class_names.add(final_name)
        return final_name
    
    def get_semantic_class(self, node: Dict, parent: Dict = None) -> str:
        """Generate semantic class name based on node properties"""
        name = node.get('name', '')
        node_type = node.get('type', '')
        node_id = node.get('id', '')
        
        # Special cases based on content and structure
        text_content = self.get_text_content(node).lower()
        
        # Check specific patterns
        if 'home indicator' in name.lower():
            if node_type == 'RECTANGLE':
                return self.get_unique_class_name('home-indicator-bar')
            return self.get_unique_class_name('home-indicator')
        
        if self.should_be_button(node):
            if 'sign in' in text_content:
                return self.get_unique_class_name('sign-in-button')
            elif 'create' in text_content:
                return self.get_unique_class_name('create-account-button')
            return self.get_unique_class_name('button')
        
        if self.should_be_input(node):
            if 'password' in text_content:
                return self.get_unique_class_name('password-input')
            elif '@' in text_content:
                return self.get_unique_class_name('email-input')
            return self.get_unique_class_name('input')
        
        if node_type == 'TEXT':
            if 'sign in' in text_content and len(text_content) < 15:
                return self.get_unique_class_name('sign-in-heading')
            elif 'forgot' in text_content:
                return self.get_unique_class_name('forgot-password-link')
            elif 'create account' in text_content:
                return self.get_unique_class_name('create-account-text')
            return self.get_unique_class_name('text')
        
        # Check if it's a container for inputs
        if node_type == 'FRAME' and node.get('layoutMode') == 'VERTICAL':
            children = node.get('children', [])
            if len(children) >= 2 and all(self.should_be_input(c) for c in children[:2]):
                return self.get_unique_class_name('input-group')
        
        # Use node name or ID
        if name:
            return self.get_unique_class_name(name)
        
        return self.get_unique_class_name(f"node-{node_id.replace(':', '-')}")
    
    def should_be_input(self, node: Dict) -> bool:
        """Check if node should be rendered as input"""
        if node.get('type') != 'FRAME':
            return False
        
        # Must have border
        strokes = node.get('strokes', [])
        if not strokes or not any(s.get('visible', True) for s in strokes):
            return False
        
        # Must have layout mode
        if not node.get('layoutMode'):
            return False
        
        # Must have text child
        text = self.get_text_content(node)
        if not text:
            return False
        
        # Size check
        bounds = node.get('absoluteBoundingBox', {})
        height = bounds.get('height', 999)
        width = bounds.get('width', 0)
        
        return height <= 100 and width > 100
    
    def should_be_button(self, node: Dict) -> bool:
        """Check if node should be rendered as button"""
        if node.get('type') != 'FRAME':
            return False
        
        # Must have background
        fills = node.get('fills', []) or node.get('background', [])
        visible_fills = [f for f in fills if f.get('visible', True)]
        
        if not visible_fills:
            return False
        
        # Check for gradient or solid background
        has_gradient = any(f.get('type') == 'GRADIENT_LINEAR' for f in visible_fills)
        
        # High border radius indicates button
        radius = node.get('cornerRadius', 0)
        
        # Must have text
        text = self.get_text_content(node)
        if not text:
            return False
        
        # Size check
        bounds = node.get('absoluteBoundingBox', {})
        height = bounds.get('height', 0)
        width = bounds.get('width', 0)
        
        # Button-like dimensions and styling
        return (has_gradient or radius >= 20) and 30 <= height <= 80 and width > 100
    
    def get_text_content(self, node: Dict) -> str:
        """Get text content from node"""
        if node.get('type') == 'TEXT':
            return node.get('characters', '')
        
        for child in node.get('children', []):
            text = self.get_text_content(child)
            if text:
                return text
        
        return ''
    
    def extract_styles(self, node: Dict, parent: Dict = None) -> Dict[str, str]:
        """Extract CSS styles from Figma node"""
        css = {}
        node_type = node.get('type')
        bounds = node.get('absoluteBoundingBox', {})
        
        # Determine positioning
        parent_layout = parent.get('layoutMode') if parent else None
        
        if parent_layout in ['HORIZONTAL', 'VERTICAL']:
            # Child in auto-layout
            css['display'] = 'flex'
            
            layout_sizing_h = node.get('layoutSizingHorizontal', 'FIXED')
            layout_sizing_v = node.get('layoutSizingVertical', 'FIXED')
            
            if layout_sizing_h == 'FILL':
                css['align-self'] = 'stretch'
            elif layout_sizing_h == 'HUG':
                css['width'] = 'fit-content'
            elif bounds.get('width'):
                css['width'] = f"{bounds['width']}px"
            
            if layout_sizing_v == 'FIXED' and bounds.get('height'):
                css['height'] = f"{bounds['height']}px"
            elif layout_sizing_v == 'HUG':
                css['height'] = 'fit-content'
            
            css['flex'] = 'none'
            css['order'] = '0'
        else:
            # Absolute positioning
            if node_type not in ['TEXT'] or not parent_layout:
                css['position'] = 'absolute'
                
                if parent:
                    parent_bounds = parent.get('absoluteBoundingBox', {})
                    css['left'] = f"{bounds.get('x', 0) - parent_bounds.get('x', 0)}px"
                    css['top'] = f"{bounds.get('y', 0) - parent_bounds.get('y', 0)}px"
                
                if bounds.get('width'):
                    css['width'] = f"{bounds['width']}px"
                if bounds.get('height'):
                    css['height'] = f"{bounds['height']}px"
        
        # Auto-layout properties
        layout_mode = node.get('layoutMode')
        if layout_mode in ['HORIZONTAL', 'VERTICAL']:
            css['display'] = 'flex'
            css['flex-direction'] = 'row' if layout_mode == 'HORIZONTAL' else 'column'
            
            counter_align = node.get('counterAxisAlignItems', 'MIN')
            primary_align = node.get('primaryAxisAlignItems', 'MIN')
            
            align_map = {
                'MIN': 'flex-start',
                'CENTER': 'center',
                'MAX': 'flex-end',
                'SPACE_BETWEEN': 'space-between'
            }
            
            css['align-items'] = align_map.get(counter_align, 'flex-start')
            css['justify-content'] = align_map.get(primary_align, 'flex-start')
            
            # Padding
            pt = node.get('paddingTop', 0)
            pr = node.get('paddingRight', 0)
            pb = node.get('paddingBottom', 0)
            pl = node.get('paddingLeft', 0)
            
            if any([pt, pr, pb, pl]):
                css['padding'] = f"{pt}px {pr}px {pb}px {pl}px"
            
            # Gap
            gap = node.get('itemSpacing', 0)
            if gap > 0:
                css['gap'] = f"{gap}px"
        
        # Background
        if node_type != 'TEXT':
            fills = node.get('fills', []) or node.get('background', [])
            visible_fills = [f for f in fills if f.get('visible', True)]
            
            if visible_fills:
                fill = visible_fills[0]
                if fill['type'] == 'SOLID':
                    css['background'] = self.rgba_to_css(fill.get('color', {}))
                elif fill['type'] == 'GRADIENT_LINEAR':
                    gradient = self.extract_gradient_css(fill)
                    if gradient:
                        css['background'] = gradient
        
        # Border
        strokes = node.get('strokes', [])
        visible_strokes = [s for s in strokes if s.get('visible', True)]
        
        if visible_strokes:
            stroke_weight = node.get('strokeWeight', 0)
            if stroke_weight > 0:
                stroke_color = self.rgba_to_css(visible_strokes[0].get('color', {}))
                css['border'] = f"{stroke_weight}px solid {stroke_color}"
        
        # Border radius
        corners = node.get('rectangleCornerRadii', [])
        if corners and len(corners) == 4:
            if all(c == corners[0] for c in corners):
                if corners[0] > 0:
                    css['border-radius'] = f"{corners[0]}px"
            else:
                css['border-radius'] = f"{corners[0]}px {corners[1]}px {corners[2]}px {corners[3]}px"
        else:
            radius = node.get('cornerRadius', 0)
            if radius > 0:
                css['border-radius'] = f"{radius}px"
        
        # Text styles
        if node_type == 'TEXT':
            style = node.get('style', {})
            
            font_family = style.get('fontFamily', 'Inter')
            self.fonts.add(font_family)
            
            css['font-family'] = f"'{font_family}'"
            css['font-style'] = 'normal'
            css['font-weight'] = str(style.get('fontWeight', 400))
            css['font-size'] = f"{style.get('fontSize', 16)}px"
            
            # Line height
            line_height_unit = style.get('lineHeightUnit', 'AUTO')
            if line_height_unit == 'PIXELS':
                css['line-height'] = f"{style.get('lineHeightPx')}px"
            elif line_height_unit == 'FONT_SIZE_%':
                percent = style.get('lineHeightPercentFontSize', 100)
                css['line-height'] = f"{int(percent)}%"
            
            if not css.get('display'):
                css['display'] = 'flex'
            css['align-items'] = 'center'
            
            # Text align
            text_align = style.get('textAlignHorizontal', 'LEFT')
            align_map = {'LEFT': 'left', 'CENTER': 'center', 'RIGHT': 'right', 'JUSTIFIED': 'justify'}
            css['text-align'] = align_map.get(text_align, 'left')
            
            # Letter spacing
            if 'letterSpacing' in style:
                css['letter-spacing'] = f"{style['letterSpacing']}px"
            
            # Color
            fills = node.get('fills', [])
            if fills:
                visible_fills = [f for f in fills if f.get('visible', True)]
                if visible_fills:
                    fill = visible_fills[0]
                    opacity = fill.get('opacity', 1)
                    color = fill.get('color', {})
                    
                    if opacity < 1:
                        r = int(color.get('r', 0) * 255)
                        g = int(color.get('g', 0) * 255)
                        b = int(color.get('b', 0) * 255)
                        css['color'] = f"rgba({r}, {g}, {b}, {opacity})"
                    else:
                        css['color'] = self.rgba_to_css(color)
        
        # Effects
        effects = node.get('effects', [])
        visible_effects = [e for e in effects if e.get('visible', True)]
        
        for effect in visible_effects:
            if effect.get('type') == 'DROP_SHADOW':
                color = self.rgba_to_css(effect.get('color', {}))
                offset = effect.get('offset', {})
                blur = effect.get('radius', 0)
                x = offset.get('x', 0)
                y = offset.get('y', 0)
                css['box-shadow'] = f"{x}px {y}px {blur}px {color}"
            elif effect.get('type') == 'BACKGROUND_BLUR':
                radius = effect.get('radius', 10)
                css['backdrop-filter'] = f"blur({radius}px)"
        
        # Opacity
        opacity = node.get('opacity', 1)
        if opacity < 1:
            css['opacity'] = str(opacity)
        
        # Clip content
        if node.get('clipsContent', False):
            css['overflow'] = 'hidden'
        
        return css
    
    def generate_html(self, node: Dict, parent: Dict = None, depth: int = 0) -> Tuple[str, Dict]:
        """Generate HTML and CSS for node"""
        if not node.get('visible', True):
            return '', {}
        
        node_type = node.get('type')
        class_name = self.get_semantic_class(node, parent)
        
        # Extract styles
        css = self.extract_styles(node, parent)
        all_css = {class_name: css} if css else {}
        
        html = ''
        indent = '  ' * depth
        
        # Handle TEXT nodes
        if node_type == 'TEXT':
            text = node.get('characters', '')
            
            # Check if link
            if any(word in text.lower() for word in ['forgot', 'learn', 'help']):
                html = f'{indent}<a href="#" class="{class_name}">{text}</a>'
            else:
                # Determine tag
                style = node.get('style', {})
                font_size = style.get('fontSize', 16)
                font_weight = style.get('fontWeight', 400)
                
                if font_size >= 40 and font_weight >= 700:
                    tag = 'h1'
                elif font_size >= 24:
                    tag = 'h2'
                else:
                    tag = 'p'
                
                html = f'{indent}<{tag} class="{class_name}">{text}</{tag}>'
        
        # Handle containers
        elif node_type in ['FRAME', 'GROUP', 'COMPONENT', 'INSTANCE']:
            # Check if input
            if self.should_be_input(node):
                text = self.get_text_content(node)
                if 'password' in text.lower():
                    html = f'{indent}<input type="password" class="{class_name}" placeholder="{text}">'
                elif '@' in text:
                    html = f'{indent}<input type="email" class="{class_name}" value="{text}">'
                else:
                    html = f'{indent}<input type="text" class="{class_name}" placeholder="{text}">'
            
            # Check if button
            elif self.should_be_button(node):
                text = self.get_text_content(node)
                html = f'{indent}<button class="{class_name}">{text}</button>'
            
            # Regular container
            else:
                children = node.get('children', [])
                children_html = []
                
                for child in children:
                    child_html, child_css = self.generate_html(child, node, depth + 1)
                    if child_html:
                        children_html.append(child_html)
                    all_css.update(child_css)
                
                if children_html:
                    children_str = '\n'.join(children_html)
                    html = f'{indent}<div class="{class_name}">\n{children_str}\n{indent}</div>'
                else:
                    html = f'{indent}<div class="{class_name}"></div>'
        
        # Handle shapes
        elif node_type in ['RECTANGLE', 'ELLIPSE', 'VECTOR']:
            html = f'{indent}<div class="{class_name}"></div>'
        
        return html, all_css
    
    def css_to_string(self, css_dict: Dict[str, Dict[str, str]]) -> str:
        """Convert CSS dictionary to string"""
        lines = []
        
        # Reset
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
        
        # Component styles
        for class_name, props in sorted(css_dict.items()):
            if not props:
                continue
            
            lines.append(f".{class_name} {{")
            
            # Property order for readability
            prop_order = ['position', 'display', 'flex-direction', 'width', 'height', 
                         'left', 'top', 'right', 'bottom']
            
            for prop in prop_order:
                if prop in props:
                    lines.append(f"    {prop}: {props[prop]};")
            
            for prop, value in sorted(props.items()):
                if prop not in prop_order:
                    lines.append(f"    {prop}: {value};")
            
            lines.append("}\n")
        
        # Interactive states
        lines.append("""/* Interactive states */
input {
    outline: none;
    font-family: inherit;
}

input::placeholder {
    color: #C0C0C0;
}

input:focus {
    border-color: #4A90E2;
}

button {
    border: none;
    cursor: pointer;
    transition: all 0.2s;
}

button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

button:active {
    transform: translateY(0);
}

a {
    text-decoration: none;
    transition: opacity 0.2s;
}

a:hover {
    opacity: 0.7;
}
""")
        
        return '\n'.join(lines)
    
    def generate_html_doc(self, body_html: str, css: str) -> str:
        """Generate complete HTML document"""
        if not self.fonts:
            self.fonts.add('Inter')
        
        fonts_param = '&family='.join([f"{font.replace(' ', '+')}:wght@400;500;600;700" 
                                      for font in sorted(self.fonts)])
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Figma Design</title>
    <link href="https://fonts.googleapis.com/css2?family={fonts_param}&display=swap" rel="stylesheet">
    <style>
{css}
    </style>
</head>
<body>
{body_html}
</body>
</html>"""
    
    def convert(self, node_id: str = None, output_file: str = "output.html"):
        """Main conversion method"""
        print("🔍 Fetching Figma file...")
        data = self.fetch_file()
        print(f"✅ File: {data.get('name', 'Unknown')}")
        
        # Find target node
        document = data.get('document', {})
        canvas = document.get('children', [{}])[0]
        
        if node_id:
            def find_node(n, target_id):
                if n.get('id') == target_id:
                    return n
                for child in n.get('children', []):
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
        
        # Generate HTML and CSS
        html_body, css_dict = self.generate_html(target_node)
        css_string = self.css_to_string(css_dict)
        html_doc = self.generate_html_doc(html_body, css_string)
        
        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_doc)
        
        print(f"✅ Generated: {output_file}")
        print(f"📊 Classes: {len(css_dict)}, Fonts: {len(self.fonts)}")
        
        return html_doc


def main():
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python figma_converter.py <FIGMA_TOKEN> <FILE_KEY> [NODE_ID] [OUTPUT_FILE]")
        print("\nExample:")
        print("  python figma_converter.py figd_xxx MxMXpjiLPbdHlratvH0Wdy 1:75 output.html")
        sys.exit(1)
    
    token = sys.argv[1]
    file_key = sys.argv[2]
    node_id = sys.argv[3] if len(sys.argv) > 3 else None
    output = sys.argv[4] if len(sys.argv) > 4 else "output.html"
    
    converter = FigmaToHTMLConverter(token, file_key)
    converter.convert(node_id, output)


if __name__ == "__main__":
    main()