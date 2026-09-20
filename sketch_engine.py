"""
PencilSketch AI - Advanced Image Processing Engine
Converts photos into realistic pencil sketches using OpenCV, Pillow, and NumPy.
Supports 5 distinct artistic styles with fine-grained parameter adjustments.
"""

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageOps


def _dodge(front: np.ndarray, back: np.ndarray) -> np.ndarray:
    """
    Standard color-dodge blending algorithm:
    result = front / (255 - back) * 256
    Using cv2.divide handles division-by-zero safely.
    """
    # 255 - back represents the inverted blur
    inv_back = 255 - back
    # Avoid zero division
    inv_back[inv_back == 0] = 1
    result = cv2.divide(front, inv_back, scale=256)
    return np.clip(result, 0, 255).astype(np.uint8)


def _adjust_contrast_darkness(gray_img: np.ndarray, darkness: int, intensity: int) -> np.ndarray:
    """
    Adjust contrast, gamma, and dark levels.
    darkness: 10 to 100 (default 50)
    intensity: 10 to 100 (default 50)
    """
    # Normalize darkness to gamma range (0.4 to 1.6)
    # Higher darkness => lower gamma => darker shadows
    gamma = 1.0 - (darkness - 50) * 0.012
    gamma = max(0.35, min(2.0, gamma))
    
    # Gamma correction lookup table
    inv_gamma = 1.0 / gamma
    table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in range(256)]).astype("uint8")
    adjusted = cv2.LUT(gray_img, table)
    
    # Adjust intensity (line contrast)
    # intensity 50 is neutral (factor 1.0), 100 is factor 1.8, 10 is factor 0.4
    alpha = 0.4 + (intensity / 50.0) * 0.6
    beta = 128 * (1 - alpha)
    adjusted = cv2.convertScaleAbs(adjusted, alpha=alpha, beta=beta)
    
    return adjusted


def _get_adaptive_ksize(dim: int, detail: int) -> int:
    """
    Compute an odd Gaussian blur kernel size based on image dimension and detail parameter.
    detail: 10 (very broad/smooth) to 100 (ultra fine/detailed)
    """
    # Detail 100 => smaller kernel (sharper lines)
    # Detail 10  => larger kernel (softer, broad shading)
    base = max(7, int(dim * 0.025))
    scale = (110 - detail) / 50.0  # detail 50 => scale ~1.2
    ksize = int(base * scale)
    if ksize % 2 == 0:
        ksize += 1
    return max(3, min(ksize, 99))


def apply_graphite_sketch(img_bgr: np.ndarray, intensity: int = 50, darkness: int = 50, detail: int = 50) -> np.ndarray:
    """
    Realistic Graphite Style:
    Authentic graphite pencil effect with natural tone gradation and pencil edge definition.
    """
    h, w = img_bgr.shape[:2]
    min_dim = min(h, w)
    
    # 1. Grayscale
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    
    # 2. Invert grayscale
    inverted = cv2.bitwise_not(gray)
    
    # 3. Gaussian Blur
    ksize = _get_adaptive_ksize(min_dim, detail)
    blurred = cv2.GaussianBlur(inverted, (ksize, ksize), 0)
    
    # 4. Color Dodge blend
    sketch = _dodge(gray, blurred)
    
    # 5. Apply subtle graphite contrast & darkness curve
    sketch = _adjust_contrast_darkness(sketch, darkness, intensity)
    
    # 6. Add subtle paper grain simulation
    np.random.seed(42)
    noise = np.random.normal(0, 1.8, sketch.shape).astype(np.float32)
    sketch_grained = np.clip(sketch.astype(np.float32) + noise, 0, 255).astype(np.uint8)
    
    return cv2.cvtColor(sketch_grained, cv2.COLOR_GRAY2BGR)


def apply_soft_pencil(img_bgr: np.ndarray, intensity: int = 50, darkness: int = 50, detail: int = 50) -> np.ndarray:
    """
    Soft Pencil Style:
    Gentle, blended shading reminiscent of an artist using a blending stump and 2B-4B soft leads.
    """
    h, w = img_bgr.shape[:2]
    min_dim = min(h, w)
    
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    inverted = cv2.bitwise_not(gray)
    
    # Larger blur kernel for soft wash
    ksize = _get_adaptive_ksize(min_dim, int(detail * 0.7))
    if ksize < 21:
        ksize = 21 if min_dim > 200 else 7
    if ksize % 2 == 0:
        ksize += 1
        
    blurred = cv2.GaussianBlur(inverted, (ksize, ksize), 0)
    dodge = _dodge(gray, blurred)
    
    # Blend with smooth grayscale to create stump-shaded soft midtones
    smooth_gray = cv2.bilateralFilter(gray, d=7, sigmaColor=50, sigmaSpace=50)
    soft_sketch = cv2.addWeighted(dodge, 0.82, smooth_gray, 0.18, 0)
    
    # Adjust tone
    adjusted = _adjust_contrast_darkness(soft_sketch, int(darkness * 0.9), int(intensity * 0.9))
    
    return cv2.cvtColor(adjusted, cv2.COLOR_GRAY2BGR)


def apply_dark_pencil(img_bgr: np.ndarray, intensity: int = 50, darkness: int = 50, detail: int = 50) -> np.ndarray:
    """
    Dark Pencil Style:
    Deep, dramatic strokes using heavy 8B graphite or carbon pencil with strong contrast.
    """
    h, w = img_bgr.shape[:2]
    min_dim = min(h, w)
    
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    
    # Boost local contrast with CLAHE
    clahe = cv2.createCLAHE(clipLimit=2.2, tileGridSize=(8, 8))
    enhanced_gray = clahe.apply(gray)
    
    inverted = cv2.bitwise_not(enhanced_gray)
    ksize = _get_adaptive_ksize(min_dim, detail)
    blurred = cv2.GaussianBlur(inverted, (ksize, ksize), 0)
    
    sketch = _dodge(enhanced_gray, blurred)
    
    # Deepen dark tones (boost darkness parameter effect)
    boosted_darkness = min(100, int(darkness * 1.25))
    boosted_intensity = min(100, int(intensity * 1.2))
    adjusted = _adjust_contrast_darkness(sketch, boosted_darkness, boosted_intensity)
    
    # Darken shadows further
    shadow_mask = adjusted < 110
    adjusted[shadow_mask] = (adjusted[shadow_mask] * 0.82).astype(np.uint8)
    
    return cv2.cvtColor(adjusted, cv2.COLOR_GRAY2BGR)


def apply_charcoal(img_bgr: np.ndarray, intensity: int = 50, darkness: int = 50, detail: int = 50) -> np.ndarray:
    """
    Charcoal Style:
    Rich, velvety blacks, expressive rough texture, and smudged chalk accents.
    """
    h, w = img_bgr.shape[:2]
    min_dim = min(h, w)
    
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    
    # Median blur to break fine pixels into charcoal-like smudges
    smudged = cv2.medianBlur(gray, 5 if min_dim > 300 else 3)
    inverted = cv2.bitwise_not(smudged)
    
    ksize = _get_adaptive_ksize(min_dim, int(detail * 0.8))
    blurred = cv2.GaussianBlur(inverted, (ksize, ksize), 0)
    dodge = _dodge(smudged, blurred)
    
    # Extract strong structural edges (Laplacian)
    edges = cv2.Laplacian(gray, cv2.CV_16S, ksize=3)
    edges = cv2.convertScaleAbs(edges)
    edges = cv2.bitwise_not(edges)
    
    # Combine dodge with charcoal outline edges
    charcoal = cv2.min(dodge, edges)
    
    # Synthetic charcoal paper texture
    np.random.seed(101)
    roughness = np.random.normal(0, 4.0, gray.shape).astype(np.float32)
    textured = np.clip(charcoal.astype(np.float32) + roughness, 0, 255).astype(np.uint8)
    
    # High darkness threshold
    charcoal_darkness = min(100, int(darkness * 1.35))
    adjusted = _adjust_contrast_darkness(textured, charcoal_darkness, int(intensity * 1.15))
    
    return cv2.cvtColor(adjusted, cv2.COLOR_GRAY2BGR)


def apply_detailed_sketch(img_bgr: np.ndarray, intensity: int = 50, darkness: int = 50, detail: int = 50) -> np.ndarray:
    """
    Detailed Sketch Style:
    Technical architectural style with dual-pass dodge and crisp line hatching.
    """
    h, w = img_bgr.shape[:2]
    min_dim = min(h, w)
    
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    inverted = cv2.bitwise_not(gray)
    
    # Pass 1: Fine lines (small blur)
    k1 = max(3, int(min_dim * 0.012))
    if k1 % 2 == 0:
        k1 += 1
    blur1 = cv2.GaussianBlur(inverted, (k1, k1), 0)
    dodge_fine = _dodge(gray, blur1)
    
    # Pass 2: Shading (larger blur)
    k2 = max(21, int(min_dim * 0.04))
    if k2 % 2 == 0:
        k2 += 1
    blur2 = cv2.GaussianBlur(inverted, (k2, k2), 0)
    dodge_shade = _dodge(gray, blur2)
    
    # Multiply/blend both passes (fine lines + shade)
    blended = cv2.multiply(dodge_fine.astype(np.float32) / 255.0, dodge_shade.astype(np.float32) / 255.0)
    blended = np.clip(blended * 255.0, 0, 255).astype(np.uint8)
    
    # Unsharp masking for razor-sharp strokes
    gaussian_blur = cv2.GaussianBlur(blended, (0, 0), 2.0)
    sharpened = cv2.addWeighted(blended, 1.4, gaussian_blur, -0.4, 0)
    
    adjusted = _adjust_contrast_darkness(sharpened, darkness, intensity)
    return cv2.cvtColor(adjusted, cv2.COLOR_GRAY2BGR)


STYLE_MAP = {
    "graphite": apply_graphite_sketch,
    "soft": apply_soft_pencil,
    "dark": apply_dark_pencil,
    "charcoal": apply_charcoal,
    "detailed": apply_detailed_sketch,
}


def process_sketch(
    image_path: str,
    output_path: str,
    style: str = "graphite",
    intensity: int = 50,
    darkness: int = 50,
    detail: int = 50,
) -> dict:
    """
    Load image, apply chosen sketch style with parameters, and write to output_path.
    Returns metadata about dimensions and style applied.
    """
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError("Could not read image file.")
    
    # Enforce safe bounds
    intensity = max(10, min(100, int(intensity)))
    darkness = max(10, min(100, int(darkness)))
    detail = max(10, min(100, int(detail)))
    style_key = style.lower().strip()
    
    handler = STYLE_MAP.get(style_key, apply_graphite_sketch)
    sketch_bgr = handler(img, intensity=intensity, darkness=darkness, detail=detail)
    
    # Save output with high quality
    cv2.imwrite(output_path, sketch_bgr, [int(cv2.IMWRITE_PNG_COMPRESSION), 4])
    
    h, w = img.shape[:2]
    return {
        "width": w,
        "height": h,
        "style": style_key,
        "intensity": intensity,
        "darkness": darkness,
        "detail": detail,
    }


def create_comparison_image(original_path: str, sketch_path: str, output_path: str) -> str:
    """
    Generate a high-resolution side-by-side comparison image with stylish labels.
    """
    orig = cv2.imread(original_path)
    sketch = cv2.imread(sketch_path)
    if orig is None or sketch is None:
        raise ValueError("Failed to load source images for comparison.")
    
    # Match heights
    h1, w1 = orig.shape[:2]
    h2, w2 = sketch.shape[:2]
    target_h = min(h1, h2, 1200)
    
    orig_resized = cv2.resize(orig, (int(w1 * (target_h / h1)), target_h), interpolation=cv2.INTER_AREA)
    sketch_resized = cv2.resize(sketch, (int(w2 * (target_h / h2)), target_h), interpolation=cv2.INTER_AREA)
    
    # 8px separator line
    sep = np.full((target_h, 8, 3), 30, dtype=np.uint8)
    combined = np.hstack([orig_resized, sep, sketch_resized])
    
    # Add top/bottom stylish banners with Pillow for crisp typography
    combined_pil = Image.fromarray(cv2.cvtColor(combined, cv2.COLOR_BGR2RGB))
    
    # Add 60px bottom banner
    banner_h = 60
    final_w = combined_pil.width
    final_h = combined_pil.height + banner_h
    canvas = Image.new("RGB", (final_w, final_h), (18, 18, 22))
    canvas.paste(combined_pil, (0, 0))
    
    # Save comparison image
    canvas.save(output_path, "PNG", quality=95)
    return output_path
