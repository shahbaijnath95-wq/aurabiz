from PIL import Image, ImageDraw, ImageFont
import os

img = Image.new('RGB', (400, 400), '#f4f1ea')
draw = ImageDraw.Draw(img)

for y in range(400):
    r = int(255 - y * 0.1)
    g = int(240 - y * 0.15)
    b = int(220 - y * 0.2)
    draw.line([(0, y), (400, y)], fill=(max(r,200), max(g,180), max(b,150)))

draw.rounded_rectangle([40, 40, 360, 360], radius=20, fill='#ffffff', outline='#e67a00', width=3)
draw.rounded_rectangle([140, 100, 260, 300], radius=10, fill='#ffb24d', outline='#e67a00', width=2)
draw.rectangle([160, 70, 240, 110], fill='#e67a00', outline='#cc6600', width=2)
draw.ellipse([155, 50, 245, 90], fill='#cc6600')

try:
    font = ImageFont.truetype('arial.ttf', 20)
    sfont = ImageFont.truetype('arial.ttf', 14)
except:
    font = ImageFont.load_default()
    sfont = ImageFont.load_default()

draw.text((200, 320), 'Loreal Shampoo', fill='#333333', font=font, anchor='mb')
draw.text((200, 345), '300ml | Premium', fill='#888888', font=sfont, anchor='mb')

path = 'E:/AI/backend/uploads/demo_product.png'
os.makedirs(os.path.dirname(path), exist_ok=True)
img.save(path)
print(f'Image saved: {path} ({os.path.getsize(path)} bytes)')
