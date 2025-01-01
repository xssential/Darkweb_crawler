from PIL import Image
import pytesseract
import cv2

def image():
    # 이미지 불러오기
    image_path ="/app/images/processed_close.png"  # 이미지 경로
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)  # 흑백 이미지로 불러오기
    
    # 이미지 반전
    inverted_image = cv2.bitwise_not(image)
    #_, blackened_image = cv2.threshold(inverted_image, 254, 255, cv2.THRESH_BINARY)
    # 결과 저장
    output_path = "/app/images/inverted_image.png"
    cv2.imwrite(output_path, inverted_image)
    
    text = pytesseract.image_to_string(Image.open(output_path)).replace('I', 'l').replace('0', 'o').lower()
    print(text) 
    return text
