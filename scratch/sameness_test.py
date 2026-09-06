import os
import numpy as np
from PIL import Image, ImageFilter, ImageDraw, ImageFont

def calculate_ssim(img1, img2):
    # Convert images to grayscale numpy arrays of same dimensions
    gray1 = np.array(img1.convert('L'), dtype=np.float64)
    gray2 = np.array(img2.convert('L'), dtype=np.float64)
    
    # Ensure matching shape
    min_h = min(gray1.shape[0], gray2.shape[0])
    min_w = min(gray1.shape[1], gray2.shape[1])
    gray1 = gray1[:min_h, :min_w]
    gray2 = gray2[:min_h, :min_w]
    
    C1 = (0.01 * 255) ** 2
    C2 = (0.03 * 255) ** 2
    
    mu1 = np.mean(gray1)
    mu2 = np.mean(gray2)
    
    sigma1_sq = np.var(gray1)
    sigma2_sq = np.var(gray2)
    sigma12 = np.mean((gray1 - mu1) * (gray2 - mu2))
    
    ssim = ((2 * mu1 * mu2 + C1) * (2 * sigma12 + C2)) / ((mu1**2 + mu2**2 + C1) * (sigma1_sq + sigma2_sq + C2))
    return float(ssim)

def generate_blur_strip():
    paths = [
        ("Direction A: The Docket", "docs/design/directions/v2/a.png"),
        ("Direction B: The Manifest", "docs/design/directions/v2/b.png"),
        ("Direction C: The Turret", "docs/design/directions/v2/c.png")
    ]
    
    target_width = 320
    target_height = 200
    
    blurred_imgs = []
    loaded_imgs = []
    
    for title, p in paths:
        img = Image.open(p)
        loaded_imgs.append(img)
        # Resize to 320 width, crop/fit to 320x200
        aspect = img.height / img.width
        scaled_h = int(target_width * aspect)
        resized = img.resize((target_width, scaled_h), Image.Resampling.LANCZOS)
        
        # Crop or pad to target_height
        if scaled_h > target_height:
            cropped = resized.crop((0, 0, target_width, target_height))
        else:
            cropped = Image.new("RGB", (target_width, target_height), (0, 0, 0))
            cropped.paste(resized, (0, 0))
            
        # Apply 12px Gaussian blur
        blurred = cropped.filter(ImageFilter.GaussianBlur(radius=12))
        
        # Add a subtle label header
        labeled = Image.new("RGB", (target_width, target_height + 28), (15, 23, 42))
        draw = ImageDraw.Draw(labeled)
        draw.text((8, 6), title, fill=(241, 245, 249))
        labeled.paste(blurred, (0, 28))
        
        blurred_imgs.append(labeled)
        
    # Assemble horizontal strip
    spacing = 16
    total_w = (target_width * 3) + (spacing * 2) + 32
    total_h = target_height + 28 + 32
    
    strip = Image.new("RGB", (total_w, total_h), (11, 15, 23))
    x_offset = 16
    for b_img in blurred_imgs:
        strip.paste(b_img, (x_offset, 16))
        x_offset += target_width + spacing
        
    out_path = "docs/design/directions/v2/blur-strip.png"
    strip.save(out_path)
    print(f"Saved blur strip to {out_path} ({total_w}x{total_h})")
    
    # Calculate pairwise SSIM
    ssim_ab = calculate_ssim(loaded_imgs[0], loaded_imgs[1])
    ssim_ac = calculate_ssim(loaded_imgs[0], loaded_imgs[2])
    ssim_bc = calculate_ssim(loaded_imgs[1], loaded_imgs[2])
    
    print(f"SSIM(A, B): {ssim_ab:.4f}")
    print(f"SSIM(A, C): {ssim_ac:.4f}")
    print(f"SSIM(B, C): {ssim_bc:.4f}")
    
    # Also save to artifact directory
    artifact_path = r"C:\Users\zaeem\.gemini\antigravity\brain\6c3d68c9-3537-4519-afb6-12f5339f824a\blur-strip.png"
    strip.save(artifact_path)
    print(f"Saved artifact copy to {artifact_path}")

if __name__ == "__main__":
    generate_blur_strip()
