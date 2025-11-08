#!/usr/bin/env python3
"""
Run this to test your setup
"""

import os
import sys
from figma_to_html import FigmaToHTMLConverter


def test_converter():
    """Test the converter with various scenarios"""
    
    print("🧪 Testing Figma to HTML Converter\n")
    
    # Check if config exists
    try:
        import config
        print("✅ Config file found")
        
        if not config.FIGMA_TOKEN or config.FIGMA_TOKEN == "figd_your_token_here":
            print("⚠️  Warning: Please set your FIGMA_TOKEN in config.py")
            return False
        
        if not config.FILE_KEY or config.FILE_KEY == "your_file_key_here":
            print("⚠️  Warning: Please set your FILE_KEY in config.py")
            return False
        
        print(f"✅ Figma token configured (length: {len(config.FIGMA_TOKEN)})")
        print(f"✅ File key: {config.FILE_KEY}\n")
        
        # Test API connection
        print("🔌 Testing Figma API connection...")
        converter = FigmaToHTMLConverter(config.FIGMA_TOKEN, config.FILE_KEY)
        
        try:
            data = converter.fetch_file()
            print("✅ Successfully connected to Figma API")
            print(f"✅ File name: {data.get('name', 'Unknown')}")
            
            # Get available frames
            document = data.get('document', {})
            canvas = document.get('children', [{}])[0]
            frames = [c for c in canvas.get('children', []) if c.get('type') == 'FRAME']
            
            print(f"✅ Found {len(frames)} frame(s) in file\n")
            
            if frames:
                print("📋 Available frames:")
                for i, frame in enumerate(frames):
                    frame_id = frame.get('id', 'unknown')
                    frame_name = frame.get('name', 'Unnamed')
                    print(f"   {i+1}. {frame_name} (ID: {frame_id})")
                
                print("\n🎨 Converting first frame...")
                output_file = "test_output.html"
                converter.convert(output_file=output_file)
                
                # Check if file was created
                if os.path.exists(output_file):
                    file_size = os.path.getsize(output_file)
                    print(f"✅ Generated {output_file} ({file_size} bytes)")
                    print(f"\n✨ Test successful! Open {output_file} in your browser.")
                    return True
                else:
                    print("❌ Output file was not created")
                    return False
            else:
                print("⚠️  No frames found in the Figma file")
                return False
                
        except Exception as e:
            print(f"❌ API Error: {str(e)}")
            print("\nPossible issues:")
            print("  • Invalid Figma token")
            print("  • Incorrect file key")
            print("  • File is private and token doesn't have access")
            print("  • Network connectivity issues")
            return False
            
    except ImportError:
        print("⚠️  No config.py found")
        print("\n📝 Setup instructions:")
        print("  1. Copy config.example.py to config.py")
        print("  2. Edit config.py with your Figma token and file key")
        print("  3. Run this test again\n")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False


def print_setup_help():
    """Print setup instructions"""
    print("\n" + "="*60)
    print("📚 SETUP GUIDE")
    print("="*60)
    print("\n1. Get your Figma Access Token:")
    print("   • Go to https://www.figma.com/settings")
    print("   • Scroll to 'Personal Access Tokens'")
    print("   • Click 'Generate new token'")
    print("   • Copy the token")
    
    print("\n2. Get your File Key:")
    print("   • Open your Figma file")
    print("   • Look at the URL:")
    print("     https://figma.com/design/FILE_KEY/...")
    print("   • Copy the FILE_KEY part")
    
    print("\n3. Configure the converter:")
    print("   • Copy config.example.py to config.py")
    print("   • Edit config.py")
    print("   • Paste your token and file key")
    
    print("\n4. Run the converter:")
    print("   python convert.py")
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    success = test_converter()
    
    if not success:
        print_setup_help()
        sys.exit(1)
    
    sys.exit(0)