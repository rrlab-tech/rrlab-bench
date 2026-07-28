import cairosvg, requests, os, re
from PIL import Image
import random

out = "/Volumes/Other/Agent/rrlab/rrlab-bench/charts/logos"

# 所有 logo：URL + 渲染颜色（currentColor 的用具体颜色替代）
icons = {
    "deepseek": {
        "url": "https://raw.githubusercontent.com/lobehub/lobe-icons/master/packages/static-svg/icons/deepseek-color.svg",
        "color": None,  # 已有颜色
    },
    "minimax": {
        "url": "https://raw.githubusercontent.com/lobehub/lobe-icons/master/packages/static-svg/icons/minimax-color.svg",
        "color": None,
    },
    "chatglm": {
        "url": "https://raw.githubusercontent.com/lobehub/lobe-icons/master/packages/static-svg/icons/chatglm-color.svg",
        "color": None,
    },
    "claude": {
        "url": "https://raw.githubusercontent.com/lobehub/lobe-icons/master/packages/static-svg/icons/claude-color.svg",
        "color": None,
    },
    "kimi": {
        "url": "https://raw.githubusercontent.com/lobehub/lobe-icons/master/packages/static-svg/icons/kimi-color.svg",
        "color": None,
    },
    "grok": {
        "url": "https://raw.githubusercontent.com/lobehub/lobe-icons/master/packages/static-svg/icons/grok.svg",
        "color": "#111111",  # Grok/xAI 品牌色
    },
}

logos = {}
for name, cfg in icons.items():
    svg_path = f"{out}/{name}.svg"
    r = requests.get(cfg["url"], timeout=10)
    svg_content = r.text
    
    # 如果需要替换 currentColor
    if cfg["color"]:
        svg_content = svg_content.replace('currentColor', cfg["color"])
        with open(svg_path, "w") as f:
            f.write(svg_content)
    else:
        with open(svg_path, "wb") as f:
            f.write(r.content)
    
    # 渲染
    png_data = cairosvg.svg2png(url=svg_path, output_width=800)
    png_path = f"{out}/{name}.png"
    with open(png_path, "wb") as f:
        f.write(png_data)
    
    img = Image.open(png_path).convert("RGBA")
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)
    
    logos[name] = img
    print(f"✅ {name}: {img.size}")

# === 合成 ===
canvas_w, canvas_h = 1600, 600
canvas = Image.new("RGBA", (canvas_w, canvas_h), (255, 255, 255, 255))

layout = {
    "grok":     {"w": 220, "x": 50,  "y": 25},
    "deepseek": {"w": 260, "x": 320, "y": 50},
    "minimax":  {"w": 250, "x": 640, "y": 15},
    "chatglm":  {"w": 240, "x": 160, "y": 320},
    "claude":   {"w": 200, "x": 500, "y": 330},
    "kimi":     {"w": 200, "x": 820, "y": 300},
}

random.seed(42)
for name, img in logos.items():
    cfg = layout[name]
    w, h = img.size
    ratio = cfg["w"] / w
    img = img.resize((cfg["w"], int(h * ratio)), Image.LANCZOS)
    
    angle = random.uniform(-4, 4)
    img = img.rotate(angle, expand=True, resample=Image.BICUBIC)
    
    x = cfg["x"] + random.randint(-10, 10)
    y = cfg["y"] + random.randint(-10, 10)
    canvas.paste(img, (x, y), img)

out_path = "/Volumes/Other/Agent/rrlab/rrlab-bench/charts/model_logos_header.png"
canvas.save(out_path, "PNG")
print(f"\n✅ 保存: {out_path} ({canvas.size})")
