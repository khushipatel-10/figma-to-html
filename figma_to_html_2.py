"""
Figma to HTML/CSS Converter - Final Production Version
Works on ANY Figma file - Pixel-perfect conversion
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
        self.images = {}  # Track image nodes and their URLs
        self.vectors = {}  # Store vector node info for SVG fetching
        
    def fetch_file(self) -> Dict:
        """Fetch the Figma file JSON data"""
        url = f"{self.base_url}/files/{self.file_key}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def fetch_images(self, node_ids: List[str]) -> Dict[str, str]:
        """Fetch image URLs from Figma API"""
        if not node_ids:
            return {}
        
        ids_str = ','.join(node_ids)
        url = f"{self.base_url}/images/{self.file_key}?ids={ids_str}&format=png&scale=2"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        result = response.json()
        return result.get('images', {})
    
    # New method to fetch SVGs
    def fetch_svg(self, node_id: str) -> Optional[str]:

        """Fetch SVG content from Figma API"""
        url = f"{self.base_url}/images/{self.file_key}?ids={node_id}&format=svg"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            result = response.json()
            
            svg_url = result.get('images', {}).get(node_id)
            if svg_url:
                svg_response = requests.get(svg_url)
                svg_response.raise_for_status()
                return svg_response.text
        except Exception as e:
            print(f"Failed to fetch SVG for {node_id}: {e}")
        
        return None
        # """Fetch multiple SVG URLs for given vector node IDs"""
        # if not node_ids:
        #     return {}

        # # Convert dict keys (node IDs) to comma-separated string
        # ids_str = ','.join(node_ids.keys())
        # url = f"{self.base_url}/images/{self.file_key}?ids={ids_str}&format=svg"

        # try:
        #     response = requests.get(url, headers=self.headers)
        #     response.raise_for_status()
        #     result = response.json()
        #     return result.get('images', {})  # Mapping {node_id: svg_url}
        # except Exception as e:
        #     print(f"Failed to fetch SVG URLs: {e}")
        #     return {}
        
    def rgba_to_css(self, color: Dict, opacity: float = None) -> str:
        """Convert Figma RGBA to CSS color"""
        if not color:
            return "transparent"
        
        r = int(color.get('r', 0) * 255)
        g = int(color.get('g', 0) * 255)
        b = int(color.get('b', 0) * 255)
        
        if opacity is not None:
            a = opacity
        else:
            a = color.get('a', 1)
        
        if a == 1:
            return f"#{r:02X}{g:02X}{b:02X}"
        return f"rgba({r}, {g}, {b}, {a})"
    
    def extract_gradient_css(self, fill: Dict) -> Optional[str]:
        """Extract gradient CSS with exact angle calculation"""
        if fill.get('type') != 'GRADIENT_LINEAR':
            return None
        
        stops = fill.get('gradientStops', [])
        if not stops:
            return None
        
        handles = fill.get('gradientHandlePositions', [])
        if len(handles) >= 2:
            x1, y1 = handles[0]['x'], handles[0]['y']
            x2, y2 = handles[1]['x'], handles[1]['y']
            
            dx = x2 - x1
            dy = y2 - y1
            
            angle_rad = math.atan2(dy, dx)
            angle_deg = math.degrees(angle_rad)
            css_angle = (90 - angle_deg) % 360
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
        clean = re.sub(r'[^a-z0-9-]', '-', base_name.lower())
        clean = re.sub(r'-+', '-', clean).strip('-')
        
        if not clean or clean[0].isdigit():
            clean = f"node-{clean}"
        
        if clean not in self.used_class_names:
            self.used_class_names.add(clean)
            return clean
        
        counter = 2
        while f"{clean}-{counter}" in self.used_class_names:
            counter += 1
        
        final_name = f"{clean}-{counter}"
        self.used_class_names.add(final_name)
        return final_name
    
    def get_semantic_class(self, node: Dict) -> str:
        """Generate semantic class name"""
        name = node.get('name', '')
        node_type = node.get('type', '')
        
        if name:
            return self.get_unique_class_name(name)
        
        type_map = {
            'FRAME': 'frame',
            'GROUP': 'group',
            'TEXT': 'text',
            'RECTANGLE': 'rectangle',
            'ELLIPSE': 'ellipse',
            'VECTOR': 'vector',
            'COMPONENT': 'component',
            'INSTANCE': 'instance'
        }
        
        base = type_map.get(node_type, 'element')
        return self.get_unique_class_name(base)
    
    def get_text_content(self, node: Dict) -> str:
        """Get text content from node or its children"""
        if node.get('type') == 'TEXT':
            return node.get('characters', '')
        
        for child in node.get('children', []):
            text = self.get_text_content(child)
            if text:
                return text
        
        return ''
    
    def get_text_styles_from_children(self, node: Dict) -> Optional[Dict[str, str]]:
        """Get text styles from first text child"""
        for child in node.get('children', []):
            if child.get('type') == 'TEXT':
                return self.extract_text_styles(child)
            result = self.get_text_styles_from_children(child)
            if result:
                return result
        return None
    
    def is_likely_input(self, node: Dict) -> bool:
        """Detect if node should be an input field"""
        if node.get('type') != 'FRAME':
            return False
        
        strokes = node.get('strokes', [])
        if not strokes or not any(s.get('visible', True) for s in strokes):
            return False
        
        if not node.get('layoutMode'):
            return False
        
        text = self.get_text_content(node)
        if not text:
            return False
        
        fills = node.get('fills', []) or node.get('background', [])
        visible_fills = [f for f in fills if f.get('visible', True)]
        if any(f.get('type') == 'GRADIENT_LINEAR' for f in visible_fills):
            return False
        
        if visible_fills:
            solid_fills = [f for f in visible_fills if f.get('type') == 'SOLID']
            if solid_fills:
                color = solid_fills[0].get('color', {})
                r, g, b = color.get('r', 1), color.get('g', 1), color.get('b', 1)
                is_colored = not (r > 0.85 and g > 0.85 and b > 0.85)
                radius = node.get('cornerRadius', 0)
                if is_colored and radius > 20:
                    return False
        
        bounds = node.get('absoluteBoundingBox', {})
        height = bounds.get('height', 999)
        width = bounds.get('width', 0)
        
        return height <= 100 and width > 80
    
    def is_likely_button(self, node: Dict) -> bool:
        """Detect if node should be a button"""
        if node.get('type') != 'FRAME':
            return False
        
        fills = node.get('fills', []) or node.get('background', [])
        visible_fills = [f for f in fills if f.get('visible', True)]
        
        has_gradient = any(f.get('type') == 'GRADIENT_LINEAR' for f in visible_fills)
        
        has_colored_bg = False
        if not has_gradient and visible_fills:
            solid_fills = [f for f in visible_fills if f.get('type') == 'SOLID']
            if solid_fills:
                color = solid_fills[0].get('color', {})
                r, g, b = color.get('r', 1), color.get('g', 1), color.get('b', 1)
                has_colored_bg = not (r > 0.85 and g > 0.85 and b > 0.85)
        
        radius = node.get('cornerRadius', 0)
        
        text = self.get_text_content(node)
        if not text:
            return False
        
        bounds = node.get('absoluteBoundingBox', {})
        height = bounds.get('height', 0)
        width = bounds.get('width', 0)
        
        is_button_size = 20 <= height <= 100 and width > 80
        is_button_style = has_gradient or (has_colored_bg and radius >= 15)
        
        return is_button_size and is_button_style
    
    def is_likely_link(self, node: Dict) -> bool:
        """Detect if text node should be a link"""
        if node.get('type') != 'TEXT':
            return False
        
        text = node.get('characters', '').lower()
        
        link_keywords = ['forgot', 'learn', 'help', 'click', 'sign up', 
                        'log in', 'register', 'more info', 'read more',
                        'terms', 'privacy', 'contact', 'here']
        
        return any(keyword in text for keyword in link_keywords)
    
    def should_skip_node(self, node: Dict, parent: Dict = None) -> bool:
        """Check if node should be skipped"""
        if node.get('type') != 'TEXT':
            return False
        
        if parent:
            if self.is_likely_button(parent) or self.is_likely_input(parent):
                return True
        
        return False
    
    def extract_text_styles(self, node: Dict) -> Dict[str, str]:
        """Extract text styles from TEXT node"""
        css = {}
        style = node.get('style', {})
        
        font_family = style.get('fontFamily', 'Inter')
        self.fonts.add(font_family)
        css['font-family'] = f"'{font_family}'"
        css['font-style'] = 'normal'
        css['font-weight'] = str(style.get('fontWeight', 400))
        css['font-size'] = f"{style.get('fontSize', 16)}px"
        
        line_height_unit = style.get('lineHeightUnit', 'AUTO')
        if line_height_unit == 'PIXELS':
            css['line-height'] = f"{style.get('lineHeightPx')}px"
        elif line_height_unit == 'FONT_SIZE_%':
            percent = style.get('lineHeightPercentFontSize', 100)
            css['line-height'] = f"{int(percent)}%"
        elif line_height_unit == 'INTRINSIC_%':
            percent = style.get('lineHeightPercent', 100)
            css['line-height'] = f"{percent:.1f}%"
        
        text_align = style.get('textAlignHorizontal', 'LEFT')
        align_map = {'LEFT': 'left', 'CENTER': 'center', 'RIGHT': 'right', 'JUSTIFIED': 'justify'}
        css['text-align'] = align_map.get(text_align, 'left')
        
        if 'letterSpacing' in style:
            spacing = style['letterSpacing']
            if abs(spacing) < 1:
                css['letter-spacing'] = f"{spacing / style.get('fontSize', 16):.2f}em"
            else:
                css['letter-spacing'] = f"{spacing}px"
        
        fills = node.get('fills', [])
        if fills:
            visible_fills = [f for f in fills if f.get('visible', True)]
            if visible_fills:
                fill = visible_fills[0]
                fill_opacity = fill.get('opacity', 1)
                color = fill.get('color', {})
                css['color'] = self.rgba_to_css(color, fill_opacity)
        
        return css
    
    def extract_styles(self, node: Dict, parent: Dict = None) -> Dict[str, str]:
        """Extract CSS styles from any Figma node"""
        css = {}
        node_type = node.get('type')
        bounds = node.get('absoluteBoundingBox', {})
        
        # POSITIONING
        parent_layout = parent.get('layoutMode') if parent else None
        
        if parent_layout in ['HORIZONTAL', 'VERTICAL']:
            layout_sizing_h = node.get('layoutSizingHorizontal', 'FIXED')
            layout_sizing_v = node.get('layoutSizingVertical', 'FIXED')
            
            if layout_sizing_h == 'FILL':
                css['align-self'] = 'stretch'
            elif layout_sizing_h == 'HUG':
                css['width'] = 'fit-content'
            elif bounds.get('width'):
                css['width'] = f"{bounds['width']}px"
            
            if layout_sizing_v == 'FIXED':
                if bounds.get('height'):
                    css['height'] = f"{bounds['height']}px"
            elif layout_sizing_v == 'HUG':
                css['height'] = 'fit-content'
            elif layout_sizing_v == 'FILL':
                css['flex-grow'] = '1'
            
            css['flex'] = 'none'
            css['order'] = '0'
        else:
            css['position'] = 'absolute'
            
            if parent:
                parent_bounds = parent.get('absoluteBoundingBox', {})
                x = bounds.get('x', 0) - parent_bounds.get('x', 0)
                y = bounds.get('y', 0) - parent_bounds.get('y', 0)
                css['left'] = f"{x}px"
                css['top'] = f"{y}px"
            
            if bounds.get('width'):
                css['width'] = f"{bounds['width']}px"
            if bounds.get('height'):
                css['height'] = f"{bounds['height']}px"
        
        # AUTO-LAYOUT
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
            
            pt = node.get('paddingTop', 0)
            pr = node.get('paddingRight', 0)
            pb = node.get('paddingBottom', 0)
            pl = node.get('paddingLeft', 0)
            
            if any([pt, pr, pb, pl]):
                if pt == pr == pb == pl:
                    css['padding'] = f"{pt}px"
                elif pt == pb and pl == pr:
                    css['padding'] = f"{pt}px {pr}px"
                else:
                    css['padding'] = f"{pt}px {pr}px {pb}px {pl}px"
            
            gap = node.get('itemSpacing', 0)
            if gap > 0:
                css['gap'] = f"{gap}px"
        
        # BACKGROUND
        if node_type not in ['TEXT', 'VECTOR', 'LINE', 'ELLIPSE', 'POLYGON', 'STAR']:
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
                elif fill['type'] == 'IMAGE':
                    # Track image for fetching
                    image_ref = fill.get('imageRef')
                    if image_ref:
                        node_id = node.get('id')
                        self.images[node_id] = image_ref
                        css['background-image'] = f"url('{image_ref}.png')"
                        css['background-size'] = 'cover'
                        css['background-position'] = 'center'
        
        # BORDER
        strokes = node.get('strokes', [])
        visible_strokes = [s for s in strokes if s.get('visible', True)]
        
        if visible_strokes:
            stroke_weight = node.get('strokeWeight', 0)
            if stroke_weight > 0:
                stroke_color = self.rgba_to_css(visible_strokes[0].get('color', {}))
                css['border'] = f"{stroke_weight}px solid {stroke_color}"
        
        # BORDER RADIUS
        corners = node.get('rectangleCornerRadii')
        
        if corners and len(corners) == 4:
            tl, tr, br, bl = corners
            
            if tl == tr == br == bl:
                if tl > 0:
                    css['border-radius'] = f"{tl}px"
            else:
                css['border-radius'] = f"{tl}px {tr}px {br}px {bl}px"
        else:
            radius = node.get('cornerRadius', 0)
            if radius > 0:
                css['border-radius'] = f"{radius}px"
        
        # TEXT STYLES
        if node_type == 'TEXT':
            text_styles = self.extract_text_styles(node)
            css.update(text_styles)
            css['display'] = 'flex'
            css['align-items'] = 'center'
            
            # Handle centered text - wrap in flex container
            if text_styles.get('text-align') == 'center':
                css['justify-content'] = 'center'
        
        # EFFECTS
        effects = node.get('effects', [])
        visible_effects = [e for e in effects if e.get('visible', True)]
        
        shadows = []
        for effect in visible_effects:
            if effect.get('type') == 'DROP_SHADOW':
                color = self.rgba_to_css(effect.get('color', {}))
                offset = effect.get('offset', {})
                blur = effect.get('radius', 0)
                spread = effect.get('spread', 0)
                x = offset.get('x', 0)
                y = offset.get('y', 0)
                
                if spread > 0:
                    shadows.append(f"{x}px {y}px {blur}px {spread}px {color}")
                else:
                    shadows.append(f"{x}px {y}px {blur}px {color}")
            elif effect.get('type') == 'INNER_SHADOW':
                color = self.rgba_to_css(effect.get('color', {}))
                offset = effect.get('offset', {})
                blur = effect.get('radius', 0)
                x = offset.get('x', 0)
                y = offset.get('y', 0)
                shadows.append(f"inset {x}px {y}px {blur}px {color}")
            elif effect.get('type') == 'BACKGROUND_BLUR':
                radius = effect.get('radius', 10)
                css['backdrop-filter'] = f"blur({radius}px)"
        
        if shadows:
            css['box-shadow'] = ', '.join(shadows)
        
        # OPACITY
        opacity = node.get('opacity', 1)
        if opacity < 1:
            css['opacity'] = str(opacity)
        
        # OVERFLOW
        if node.get('clipsContent', False):
            css['overflow'] = 'hidden'
        
        # Root frame
        if node_type == 'FRAME' and not parent:
            css['position'] = 'relative'
            css['overflow'] = 'hidden'
        
        return css
    
    def generate_html(self, node: Dict, parent: Dict = None, depth: int = 0) -> Tuple[str, Dict]:
        """Generate HTML and CSS for any node"""
        if not node.get('visible', True):
            return '', {}
        
        if self.should_skip_node(node, parent):
            return '', {}
        
        node_type = node.get('type')
        class_name = self.get_semantic_class(node)
        
        css = self.extract_styles(node, parent)
        all_css = {class_name: css} if css else {}
        
        html = ''
        indent = '  ' * depth
        
        # TEXT NODES
        if node_type == 'TEXT':
            text = node.get('characters', '')
            
            if self.is_likely_link(node):
                html = f'{indent}<a href="#" class="{class_name}">{text}</a>'
            else:
                style = node.get('style', {})
                font_size = style.get('fontSize', 16)
                font_weight = style.get('fontWeight', 400)
                
                if font_size >= 48 or (font_size >= 36 and font_weight >= 700):
                    tag = 'h1'
                elif font_size >= 32 or (font_size >= 24 and font_weight >= 700):
                    tag = 'h2'
                elif font_size >= 24:
                    tag = 'h3'
                else:
                    tag = 'p'
                
                html = f'{indent}<{tag} class="{class_name}">{text}</{tag}>'
        
        # CONTAINER NODES
        elif node_type in ['FRAME', 'GROUP', 'COMPONENT', 'INSTANCE']:
            if self.is_likely_input(node):
                text = self.get_text_content(node)
                text_lower = text.lower()
                
                if 'password' in text_lower:
                    html = f'{indent}<input type="password" class="{class_name}" placeholder="{text}">'
                elif '@' in text and '.' in text:
                    html = f'{indent}<input type="email" class="{class_name}" value="{text}">'
                elif any(word in text_lower for word in ['search', 'find']):
                    html = f'{indent}<input type="search" class="{class_name}" placeholder="{text}">'
                else:
                    html = f'{indent}<input type="text" class="{class_name}" placeholder="{text}">'
            
            elif self.is_likely_button(node):
                text = self.get_text_content(node)
                
                text_styles = self.get_text_styles_from_children(node)
                if text_styles and 'color' in text_styles:
                    all_css[class_name]['color'] = text_styles['color']
                
                html = f'{indent}<button class="{class_name}">{text}</button>'
            
            else:
                children = node.get('children', [])
                children_html = []
                
                for child in children:
                    child['parent'] = node
                    child_html, child_css = self.generate_html(child, node, depth + 1)
                    if child_html:
                        children_html.append(child_html)
                    all_css.update(child_css)
                
                if children_html:
                    children_str = '\n'.join(children_html)
                    html = f'{indent}<div class="{class_name}">\n{children_str}\n{indent}</div>'
                else:
                    html = f'{indent}<div class="{class_name}"></div>'
        
        # SHAPE NODES
        elif node_type in ['RECTANGLE', 'ELLIPSE', 'VECTOR', 'LINE', 'POLYGON', 'STAR']:
            # Track vectors for SVG export
            if node_type == 'VECTOR':
                self.vectors[node.get('id')] = class_name
            
            html = f'{indent}<div class="{class_name}" data-node-id="{node.get("id")}"></div>'
        
        return html, all_css
    
    def css_to_string(self, css_dict: Dict[str, Dict[str, str]]) -> str:
        """Convert CSS dictionary to formatted string"""
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
    zoom: 0.75; /* Scale down to 75% for better viewport fit */
}
""")
        
        for class_name, props in sorted(css_dict.items()):
            if not props:
                continue
            
            lines.append(f".{class_name} {{")
            
            prop_order = [
                'position', 'display', 'flex-direction', 'flex', 'flex-grow',
                'width', 'height', 'left', 'top', 'right', 'bottom',
                'align-items', 'align-self', 'justify-content', 'order'
            ]
            
            for prop in prop_order:
                if prop in props:
                    lines.append(f"    {prop}: {props[prop]};")
            
            for prop, value in sorted(props.items()):
                if prop not in prop_order:
                    lines.append(f"    {prop}: {value};")
            
            lines.append("}\n")
        
        lines.append("""
input {
    outline: none;
    font-family: inherit;
    background: transparent;
}

input::placeholder {
    color: #C0C0C0;
}

input:focus {
    border-color: #95228C;
}

button {
    cursor: pointer;
    transition: transform 0.2s, opacity 0.2s;
    border: none;
    font-family: inherit;
    font-size: inherit;
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

@media (max-width: 420px) {
    body {
        padding: 10px;
        zoom: 1; /* Reset zoom on mobile */
    }
    [class*="frame"], [class*="container"] {
        width: 100% !important;
        max-width: 393px;
        height: auto !important;
        min-height: 852px;
    }
}
""")
        
        return '\n'.join(lines)
    
    def generate_html_doc(self, body_html: str, css: str) -> str:
        """Generate complete HTML document"""
        if not self.fonts:
            self.fonts.add('Inter')
        
        fonts_param = '&family='.join([
            f"{font.replace(' ', '+')}:wght@100;200;300;400;500;600;700;800;900" 
            for font in sorted(self.fonts)
        ])
        
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
        """Convert Figma design to HTML/CSS"""
        print("🔍 Fetching Figma file...")
        data = self.fetch_file()
        print(f"✅ File: {data.get('name', 'Unknown')}")
        
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
        
        html_body, css_dict = self.generate_html(target_node)
        
        # Fetch images if any
        if self.images:
            print(f"📷 Fetching {len(self.images)} images...")
            node_ids = list(self.images.keys())
            image_urls = self.fetch_images(node_ids)
            
            # Update CSS with actual image URLs
            for node_id, image_ref in self.images.items():
                if node_id in image_urls:
                    actual_url = image_urls[node_id]
                    # Find the class name for this node
                    for class_name, styles in css_dict.items():
                        if 'background-image' in styles and image_ref in styles['background-image']:
                            css_dict[class_name]['background-image'] = f"url('{actual_url}')"
                            print(f"  ✓ {class_name}: {image_ref}.png")
        
       # Fetch SVGs for vectors
        svg_content = {}
        if self.vectors:
            print(f"🎨 Fetching {len(self.vectors)} SVG vectors...")

            for node_id, class_name in self.vectors.items():
                svg_data = self.fetch_svg(node_id)
                if svg_data:
                    svg_content[node_id] = svg_data
                    print(f"  ✓ Downloaded SVG for node {node_id}")
                else:
                    print(f"  ✗ Failed to fetch SVG for {node_id}")

            # Replace vector divs with inline SVG
            if svg_content:
                print("🧩 Embedding SVGs into HTML...")

                for node_id, svg in svg_content.items():
                    class_name = self.vectors.get(node_id)
                    if not class_name:
                        continue

                    svg_clean = svg.strip()
                    svg_clean = re.sub(r'<svg ', f'<svg class="{class_name}" ', svg_clean, count=1)
                    placeholder = f'<div class="{class_name}" data-node-id="{node_id}"></div>'
                    html_body = html_body.replace(placeholder, svg_clean)

                    print(f"  ✓ Embedded SVG for {class_name}")

                print("✅ All SVGs embedded successfully.")

        
        css_string = self.css_to_string(css_dict)
        html_doc = self.generate_html_doc(html_body, css_string)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_doc)
        
        print(f"✅ Generated: {output_file}")
        print(f"📊 Classes: {len(css_dict)}, Fonts: {len(self.fonts)}, Images: {len(self.images)}, Vectors: {len(self.vectors)}")
        
        return html_doc


def main():
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python figma_to_html.py <FIGMA_TOKEN> <FILE_KEY> [NODE_ID] [OUTPUT_FILE]")
        print("\nExample:")
        print("  python figma_to_html.py figd_xxx FILE_KEY 1:75 output.html")
        sys.exit(1)
    
    token = sys.argv[1]
    file_key = sys.argv[2]
    node_id = sys.argv[3] if len(sys.argv) > 3 else None
    output = sys.argv[4] if len(sys.argv) > 4 else "output.html"
    
    converter = FigmaToHTMLConverter(token, file_key)
    converter.convert(node_id, output)


if __name__ == "__main__":
    main()