"""
Icon Generator - Creates julian_assistant.ico
Generates a minimal, sleek icon with circle motif and 'J' symbol
"""

import os
from PIL import Image, ImageDraw, ImageFont

def generate_icon():
    """Generate Julian Assistant icon"""
    
    # Create 256x256 image
    size = 256
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Background circle (dark green)
    circle_radius = size // 2 - 10
    circle_center = (size // 2, size // 2)
    draw.ellipse(
        [(circle_center[0] - circle_radius, circle_center[1] - circle_radius),
         (circle_center[0] + circle_radius, circle_center[1] + circle_radius)],
        fill=(76, 175, 80, 255)  # #4CAF50
    )
    
    # Inner circle (lighter green)
    inner_radius = circle_radius - 20
    draw.ellipse(
        [(circle_center[0] - inner_radius, circle_center[1] - inner_radius),
         (circle_center[0] + inner_radius, circle_center[1] + inner_radius)],
        fill=(129, 199, 132, 255)  # Lighter green
    )
    
    # Draw 'J' letter
    try:
        # Try to use a system font
        font_size = int(size * 0.6)
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            try:
                font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", font_size)
            except:
                font = ImageFont.load_default()
        
        # Calculate text position (centered)
        text = "J"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        text_x = circle_center[0] - text_width // 2
        text_y = circle_center[1] - text_height // 2 - 10  # Slight offset
        
        draw.text((text_x, text_y), text, fill=(255, 255, 255, 255), font=font)
    except:
        # Fallback: simple 'J' shape
        # Draw J manually
        j_points = [
            (circle_center[0], circle_center[1] - 60),  # Top
            (circle_center[0] - 30, circle_center[1] - 20),  # Left top
            (circle_center[0] - 30, circle_center[1] + 40),  # Left bottom
            (circle_center[0] + 10, circle_center[1] + 40),  # Right bottom
        ]
        draw.line(j_points, fill=(255, 255, 255, 255), width=20)
        # Hook at bottom
        draw.arc(
            [(circle_center[0] - 30, circle_center[1] + 20),
             (circle_center[0] + 10, circle_center[1] + 60)],
            start=180,
            end=270,
            fill=(255, 255, 255, 255),
            width=20
        )
    
    # Save as ICO
    icon_path = os.path.join(os.path.dirname(__file__), "julian_assistant.ico")
    
    # ICO format requires multiple sizes
    sizes = [16, 32, 48, 64, 128, 256]
    images = []
    
    for s in sizes:
        resized = img.resize((s, s), Image.LANCZOS)
        images.append(resized)
    
    # Save as ICO with multiple sizes
    img.save(icon_path, format='ICO', sizes=[(s, s) for s in sizes])
    
    print(f"✅ Icon generated: {icon_path}")
    return icon_path

if __name__ == "__main__":
    try:
        generate_icon()
    except Exception as e:
        print(f"Error generating icon: {e}")
        print("Creating placeholder...")
        
        # Create minimal placeholder
        icon_path = os.path.join(os.path.dirname(__file__), "julian_assistant.ico")
        img = Image.new('RGB', (256, 256), color=(76, 175, 80))
        img.save(icon_path, format='ICO')
        print(f"✅ Placeholder icon created: {icon_path}")




