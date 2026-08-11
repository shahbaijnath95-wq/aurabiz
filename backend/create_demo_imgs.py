from PIL import Image, ImageDraw, ImageFont
import os

def make_product(name, subtitle, color1, color2, filename):
    img = Image.new('RGB', (400, 400), '#f4f1ea')
    draw = ImageDraw.Draw(img)
    for y in range(400):
        r = int(255 - y * 0.08)
        g = int(245 - y * 0.12)
        b = int(235 - y * 0.15)
        draw.line([(0, y), (400, y)], fill=(max(r,200), max(g,180), max(b,150)))
    draw.rounded_rectangle([40, 40, 360, 360], radius=20, fill='#ffffff', outline=color2, width=3)
    draw.rounded_rectangle([130, 90, 270, 290], radius=15, fill=color1, outline=color2, width=2)
    draw.rectangle([150, 60, 250, 100], fill=color2)
    draw.ellipse([145, 40, 255, 85], fill=color2)
    try:
        font = ImageFont.truetype('arial.ttf', 20)
        sfont = ImageFont.truetype('arial.ttf', 13)
    except:
        font = ImageFont.load_default()
        sfont = ImageFont.load_default()
    draw.text((200, 320), name, fill='#333333', font=font, anchor='mb')
    draw.text((200, 345), subtitle, fill='#888888', font=sfont, anchor='mb')
    path = f'E:/AI/backend/uploads/{filename}'
    img.save(path)
    print(f'Saved: {filename} ({os.path.getsize(path)} bytes)')

make_product('Hair Color Kit', 'Shade 5.0 Brown', '#c0392b', '#922b21', 'demo_color.png')
make_product('Face Facial Kit', 'Gold Premium', '#f39c12', '#d68910', 'demo_facial.png')
