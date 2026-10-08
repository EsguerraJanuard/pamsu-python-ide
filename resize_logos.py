from PIL import Image
import os

source = "frontend/public/new-logo.jpg"
img = Image.open(source)
img = img.convert("RGBA")

# Function to center and crop/pad into a square without distortion
def make_square(im, size):
    width, height = im.size
    max_dim = max(width, height)
    # Pad to square
    square_im = Image.new('RGBA', (max_dim, max_dim), (255, 255, 255, 0))
    offset = ((max_dim - width) // 2, (max_dim - height) // 2)
    square_im.paste(im, offset)
    return square_im.resize((size, size), Image.Resampling.LANCZOS)

# Create 192x192
logo_192 = make_square(img, 192)
logo_192.save("frontend/public/logo-192.png", "PNG")

# Create 512x512
logo_512 = make_square(img, 512)
logo_512.save("frontend/public/logo-512.png", "PNG")

# Create 64x64 for favicon
favicon = make_square(img, 64)
favicon.save("frontend/public/favicon.png", "PNG")

print("Created logo-192.png, logo-512.png, and favicon.png")
