"""
Generates beautiful demo preset images for PencilSketch AI.
Creates 3 high-contrast, artistic test images:
1. Portrait (Stylized face profile with rich tones)
2. Architecture (Classic arches, columns and facades)
3. Landscape (Majestic mountains, trees, and lake reflections)
"""

import os
import math
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFilter


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def create_portrait_preset(output_path: str):
    """Generate an artistic portrait study with soft gradients and defined facial contours."""
    w, h = 800, 1000
    # Create smooth warm studio lighting gradient
    y, x = np.ogrid[:h, :w]
    bg = np.clip(180 - (y * 0.08) - ((x - w/2)**2) * 0.0003, 30, 240).astype(np.uint8)
    img_gray = bg.copy()
    
    # Draw stylized portrait silhouette & features using OpenCV curves
    # Head contour
    cv2.ellipse(img_gray, (400, 480), (170, 240), 0, 0, 360, 120, -1)
    # Neck and shoulders
    pts_neck = np.array([[330, 700], [470, 700], [580, 1000], [220, 1000]], np.int32)
    cv2.fillPoly(img_gray, [pts_neck], 100)
    
    # Facial shading and highlights (smooth Gaussian)
    cv2.ellipse(img_gray, (380, 460), (130, 190), -5, 0, 360, 175, -1)
    
    # Hair volume with flowing locks
    cv2.ellipse(img_gray, (400, 360), (210, 180), 0, 160, 380, 45, -1)
    cv2.ellipse(img_gray, (300, 480), (80, 200), 15, 0, 360, 40, -1)
    cv2.ellipse(img_gray, (500, 480), (80, 200), -15, 0, 360, 40, -1)
    
    # Eyes, eyebrows, nose, lips
    cv2.ellipse(img_gray, (345, 450), (28, 14), 0, 0, 360, 50, -1)  # Left eye socket
    cv2.ellipse(img_gray, (445, 450), (28, 14), 0, 0, 360, 50, -1)  # Right eye socket
    cv2.circle(img_gray, (345, 450), 12, 230, -1)  # eye white
    cv2.circle(img_gray, (445, 450), 12, 230, -1)
    cv2.circle(img_gray, (345, 450), 7, 30, -1)   # pupil
    cv2.circle(img_gray, (445, 450), 7, 30, -1)
    
    # Eyebrows
    cv2.ellipse(img_gray, (340, 425), (38, 10), -10, 180, 360, 35, 4)
    cv2.ellipse(img_gray, (450, 425), (38, 10), 10, 180, 360, 35, 4)
    
    # Nose shadow
    pts_nose = np.array([[395, 450], [405, 520], [385, 530], [395, 535], [415, 530]], np.int32)
    cv2.polylines(img_gray, [pts_nose], False, 60, 3)
    
    # Lips
    cv2.ellipse(img_gray, (400, 595), (35, 14), 0, 0, 360, 80, -1)
    cv2.line(img_gray, (365, 595), (435, 595), 40, 3)
    
    # Soften features for painterly look
    blurred = cv2.bilateralFilter(img_gray, 15, 80, 80)
    
    # Convert to warm sepia/RGB color photo
    b = np.clip(blurred * 0.85, 0, 255).astype(np.uint8)
    g = np.clip(blurred * 0.95, 0, 255).astype(np.uint8)
    r = np.clip(blurred * 1.08, 0, 255).astype(np.uint8)
    color_img = cv2.merge([b, g, r])
    
    cv2.imwrite(output_path, color_img)


def create_architecture_preset(output_path: str):
    """Generate architectural landmark with arches, columns, windows, and pediment."""
    w, h = 900, 700
    img = np.zeros((h, w, 3), dtype=np.uint8)
    
    # Sky gradient (dusk/golden hour)
    for y in range(h):
        factor = y / h
        r = int(140 + 70 * (1 - factor))
        g = int(180 + 40 * (1 - factor))
        b = int(220 + 30 * (1 - factor))
        img[y, :] = (b, g, r)
        
    # Stone building base
    cv2.rectangle(img, (100, 280), (800, 650), (160, 190, 210), -1)
    # Roof pediment (triangle)
    pediment = np.array([[100, 280], [450, 140], [800, 280]], np.int32)
    cv2.fillPoly(img, [pediment], (130, 160, 180))
    cv2.polylines(img, [pediment], True, (60, 80, 100), 4)
    
    # Entablature trim
    cv2.rectangle(img, (80, 270), (820, 290), (100, 120, 140), -1)
    cv2.rectangle(img, (60, 630), (840, 680), (80, 100, 120), -1)
    
    # 6 Columns with fluting
    col_x_list = [160, 270, 380, 490, 600, 710]
    for cx in col_x_list:
        cv2.rectangle(img, (cx, 290), (cx + 35, 630), (195, 225, 240), -1)
        # Column shading
        cv2.line(img, (cx + 3, 290), (cx + 3, 630), (120, 140, 160), 2)
        cv2.line(img, (cx + 32, 290), (cx + 32, 630), (230, 245, 255), 2)
        # Capital & Base
        cv2.rectangle(img, (cx - 8, 285), (cx + 43, 300), (110, 130, 150), -1)
        cv2.rectangle(img, (cx - 8, 620), (cx + 43, 635), (110, 130, 150), -1)
        
    # Grand Arched Doorway in center
    cv2.ellipse(img, (445, 480), (60, 75), 0, 180, 360, (50, 60, 75), -1)
    cv2.rectangle(img, (385, 480), (505, 630), (50, 60, 75), -1)
    # Door arch stones
    cv2.ellipse(img, (445, 480), (66, 82), 0, 180, 360, (90, 110, 130), 6)
    
    # Detailed Windows
    for wx in [210, 650]:
        cv2.ellipse(img, (wx + 25, 430), (25, 30), 0, 180, 360, (40, 50, 65), -1)
        cv2.rectangle(img, (wx, 430), (wx + 50, 510), (40, 50, 65), -1)
        cv2.rectangle(img, (wx - 4, 510), (wx + 54, 516), (90, 110, 130), -1)
        
    # Stone texture & steps
    for step_y in range(635, 685, 10):
        cv2.line(img, (40, step_y), (860, step_y), (50, 65, 80), 2)
        
    cv2.imwrite(output_path, img)


def create_landscape_preset(output_path: str):
    """Generate majestic mountain landscape with coniferous trees and lake reflection."""
    w, h = 960, 640
    img = np.zeros((h, w, 3), dtype=np.uint8)
    
    # Sky & Sunset / Alpine glow
    for y in range(int(h * 0.55)):
        t = y / (h * 0.55)
        r = int(240 * (1 - t) + 160 * t)
        g = int(210 * (1 - t) + 180 * t)
        b = int(180 * (1 - t) + 210 * t)
        img[y, :] = (b, g, r)
        
    # Distant Mountains (layered)
    m1 = np.array([[0, 280], [180, 150], [320, 240], [520, 110], [680, 220], [820, 140], [960, 260], [960, 360], [0, 360]], np.int32)
    cv2.fillPoly(img, [m1], (165, 145, 135))
    
    # Mountain ridges & snowcaps
    snow = np.array([[520, 110], [480, 160], [510, 170], [540, 180], [560, 150]], np.int32)
    cv2.fillPoly(img, [snow], (230, 240, 250))
    snow2 = np.array([[180, 150], [150, 190], [195, 200], [210, 175]], np.int32)
    cv2.fillPoly(img, [snow2], (225, 235, 245))
    
    # Midground hills
    h1 = np.array([[0, 320], [240, 270], [480, 310], [750, 260], [960, 300], [960, 380], [0, 380]], np.int32)
    cv2.fillPoly(img, [h1], (90, 115, 85))
    
    # Lake (lower 40%)
    lake_start = int(h * 0.55)
    for y in range(lake_start, h):
        t = (y - lake_start) / (h - lake_start)
        b = int(140 * (1 - t) + 60 * t)
        g = int(120 * (1 - t) + 70 * t)
        r = int(90 * (1 - t) + 40 * t)
        img[y, :] = (b, g, r)
        
    # Pine trees in foreground & midground
    def draw_pine(x, y, scale, color):
        for i in range(4):
            tw = int(scale * (18 + i * 14))
            th = int(scale * 22)
            top_y = y - int(scale * (i * 18 + 20))
            pts = np.array([[x, top_y], [x - tw, top_y + th], [x + tw, top_y + th]], np.int32)
            cv2.fillPoly(img, [pts], color)
        # Trunk
        cv2.rectangle(img, (x - int(scale * 4), top_y + th), (x + int(scale * 4), y), (30, 40, 45), -1)

    # Cluster of pines along shoreline
    tree_configs = [
        (80, 400, 1.1, (45, 65, 40)),
        (130, 420, 1.4, (35, 55, 30)),
        (190, 410, 1.0, (50, 70, 45)),
        (780, 410, 1.3, (38, 58, 35)),
        (850, 395, 1.1, (45, 65, 40)),
        (910, 430, 1.5, (30, 50, 28)),
    ]
    for tx, ty, sc, col in tree_configs:
        draw_pine(tx, ty, sc, col)
        
    # Water ripples
    for wy in range(lake_start + 20, h - 20, 18):
        cv2.line(img, (100, wy), (350, wy), (170, 150, 120), 1)
        cv2.line(img, (500, wy + 8), (850, wy + 8), (170, 150, 120), 1)
        
    cv2.imwrite(output_path, img)


def main():
    preset_dir = os.path.join(os.path.dirname(__file__), "static", "presets")
    ensure_dir(preset_dir)
    
    print("Generating demo presets...")
    create_portrait_preset(os.path.join(preset_dir, "portrait.jpg"))
    create_architecture_preset(os.path.join(preset_dir, "architecture.jpg"))
    create_landscape_preset(os.path.join(preset_dir, "landscape.jpg"))
    print("Presets generated successfully in:", preset_dir)


if __name__ == "__main__":
    main()
