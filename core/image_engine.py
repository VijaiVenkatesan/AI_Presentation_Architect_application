import requests
from PIL import Image
from io import BytesIO

def generate_image(prompt):
    try:
        url = f"https://image.pollinations.ai/prompt/{prompt}"
        res = requests.get(url)
        return Image.open(BytesIO(res.content))
    except:
        return None
