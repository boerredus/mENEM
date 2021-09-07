from PIL import Image
import shutil

def generate_pdf(paths: list, pdf_name: str) -> None:
    first_img = Image.open(paths.pop(0)).convert('RGB')
    images = [Image.open(img).convert('RGB') for img in paths]

    first_img.save(pdf_name, 'PDF', resolution=100.0, save_all=True, append_images=images)
    shutil.rmtree('images')