"""
Create Minimalist RAG Academic Assistant Icon
macOS Big Sur-inspired design with subtle gradients and rounded edges
"""

from PIL import Image, ImageDraw, ImageFilter
import os

def create_rag_icon():
    """Create a clean, minimal icon for RAG Academic Assistant"""
    base_size = 256
    
    # Create base image with transparent background
    img = Image.new('RGBA', (base_size, base_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Color palette: Soft grayscale with subtle blue accent
    background_gray = (245, 247, 250, 255)  # Very light gray-white
    primary_charcoal = (45, 50, 55, 255)    # Charcoal gray
    accent_gray = (100, 110, 120, 255)      # Medium gray
    light_gray = (200, 210, 220, 255)       # Light gray
    
    # Draw rounded square background (macOS Big Sur style)
    corner_radius = 60
    margin = 20
    bg_rect = [margin, margin, base_size - margin, base_size - margin]
    
    # Create rounded rectangle mask
    mask = Image.new('L', (base_size, base_size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle(bg_rect, corner_radius, fill=255)
    
    # Fill with gradient-like background (subtle)
    draw.rounded_rectangle(bg_rect, corner_radius, fill=background_gray)
    
    # Add subtle shadow/depth effect
    shadow_layer = Image.new('RGBA', (base_size, base_size), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow_layer)
    shadow_rect = [margin + 2, margin + 2, base_size - margin + 2, base_size - margin + 2]
    shadow_draw.rounded_rectangle(shadow_rect, corner_radius, fill=(0, 0, 0, 20))
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=3))
    img = Image.alpha_composite(img, shadow_layer)
    
    draw = ImageDraw.Draw(img)
    
    # Draw stylized brain with document lines (conceptual representation)
    center_x, center_y = base_size // 2, base_size // 2
    brain_size = 140
    
    # Brain outline (simplified, organic shape)
    # Left hemisphere curve
    brain_points_left = [
        (center_x - brain_size//2 - 15, center_y - 30),
        (center_x - brain_size//2 - 25, center_y),
        (center_x - brain_size//2 - 15, center_y + 30),
        (center_x - brain_size//2 - 5, center_y + 50),
        (center_x - 10, center_y + 60),
        (center_x - 5, center_y + 50),
        (center_x, center_y + 40),
        (center_x, center_y - 40),
    ]
    
    # Right hemisphere curve
    brain_points_right = [
        (center_x + 5, center_y - 40),
        (center_x, center_y - 30),
        (center_x + brain_size//2 + 15, center_y - 30),
        (center_x + brain_size//2 + 25, center_y),
        (center_x + brain_size//2 + 15, center_y + 30),
        (center_x + brain_size//2 + 5, center_y + 50),
        (center_x + 10, center_y + 60),
        (center_x + 5, center_y + 50),
        (center_x, center_y + 40),
    ]
    
    # Draw brain outline (subtle, modern)
    # Use bezier-like smooth curves
    # Simplified: draw as connected ellipses
    draw.ellipse([center_x - brain_size//2 - 20, center_y - 35, 
                  center_x - 8, center_y + 50], 
                 outline=primary_charcoal, width=8, fill=(primary_charcoal[0], primary_charcoal[1], primary_charcoal[2], 30))
    
    draw.ellipse([center_x + 8, center_y - 35, 
                  center_x + brain_size//2 + 20, center_y + 50], 
                 outline=primary_charcoal, width=8, fill=(primary_charcoal[0], primary_charcoal[1], primary_charcoal[2], 30))
    
    # Connect hemispheres with subtle curve
    draw.arc([center_x - 15, center_y - 35, center_x + 15, center_y + 50], 
             start=270, end=90, fill=primary_charcoal, width=6)
    
    # Add document lines inside (representing knowledge)
    line_y_start = center_y - 15
    line_spacing = 8
    for i in range(5):
        y = line_y_start + i * line_spacing
        # Subtle lines suggesting text
        line_width = 80 - i * 5
        x_start = center_x - line_width // 2
        x_end = center_x + line_width // 2
        draw.line([x_start, y, x_end, y], fill=accent_gray, width=2)
    
    # Add small nodes/dots (AI/neural network reference)
    node_positions = [
        (center_x - 35, center_y - 25),
        (center_x + 35, center_y - 25),
        (center_x - 25, center_y),
        (center_x + 25, center_y),
        (center_x, center_y + 25),
    ]
    for x, y in node_positions:
        draw.ellipse([x - 4, y - 4, x + 4, y + 4], 
                    fill=light_gray, outline=accent_gray, width=1)
    
    # Add subtle highlight (macOS Big Sur style)
    highlight = Image.new('RGBA', (base_size, base_size), (0, 0, 0, 0))
    highlight_draw = ImageDraw.Draw(highlight)
    highlight_rect = [margin + 10, margin + 10, margin + 60, margin + 60]
    highlight_draw.ellipse(highlight_rect, fill=(255, 255, 255, 40))
    highlight = highlight.filter(ImageFilter.GaussianBlur(radius=10))
    img = Image.alpha_composite(img, highlight)
    
    # Apply subtle overall blur for softness
    img = img.filter(ImageFilter.GaussianBlur(radius=0.5))
    
    return img

def save_icon(formats='both'):
    """Save icon in ICO and PNG formats"""
    base_dir = os.path.dirname(__file__)
    
    # Generate base image
    img_256 = create_rag_icon()
    
    # Create ICO with multiple sizes (Windows requirement)
    ico_sizes = [16, 32, 48, 64, 128, 256]
    ico_images = []
    
    for size in ico_sizes:
        resized = img_256.resize((size, size), Image.Resampling.LANCZOS)
        ico_images.append(resized)
    
    ico_path = os.path.join(base_dir, "RAG_Icon.ico")
    ico_images[0].save(ico_path, format='ICO', sizes=[(s, s) for s in ico_sizes])
    print(f"✓ ICO saved: {ico_path}")
    
    # Also save PNG for branding
    if formats == 'both' or formats == 'png':
        png_512 = img_256.resize((512, 512), Image.Resampling.LANCZOS)
        png_path = os.path.join(base_dir, "RAG_Icon.png")
        png_512.save(png_path, format='PNG')
        print(f"✓ PNG saved: {png_path}")
    
    return ico_path

if __name__ == "__main__":
    try:
        icon_path = save_icon('both')
        print(f"\n✓✓✓ Icon created successfully! ✓✓✓")
        print(f"Location: {icon_path}")
    except Exception as e:
        print(f"Error creating icon: {e}")
        import traceback
        traceback.print_exc()
