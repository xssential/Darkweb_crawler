from PIL import Image

def zoom_image(input_image_path, output_image_path, zoom_factor=5):
    try:
        image = Image.open(input_image_path)
        
        width, height = image.size
        
        new_width = int(width * zoom_factor)
        new_height = int(height * zoom_factor)
        
        zoomed_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        zoomed_image.save(output_image_path)
    except Exception as e:
        print(e)

def zoom():
    input_image = "/app/images/mediantest.png"  
    output_image = "/app/images/zoomed_image.png" 
    zoom_image(input_image, output_image, zoom_factor=5)

