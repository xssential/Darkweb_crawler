import cv2
import numpy as np
import pytesseract
from PIL import Image

def apply_morph_close(image_path, output_path):
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        print(f"이미지 파일을 찾을 수 없습니다: {image_path}")
        return

    kernel = np.ones((3, 3), dtype=np.uint8)

    erode = cv2.erode(img, kernel, iterations=3)
    close = cv2.dilate(erode, kernel, iterations=3)

    cv2.imwrite(output_path, close)

    return output_path

def extract_text_with_ocr(image_path):
    custom_config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'

    text = pytesseract.image_to_string(Image.open(image_path), config=custom_config)

    return text.strip()

def temp():
    input_image = "/app/images/zoomed_image.png" 
    output_image = "/app/images/processed_close.png"
    
    processed_image_path = apply_morph_close(input_image, output_image)


