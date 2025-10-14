import requests
from io import BytesIO
from app.logger import loggerCloudVision
from pdf2image import convert_from_bytes
from google.cloud import vision
from app.services import cloud_vision_client


def extract_text_from_file(file_url, file_type="image"):
    if file_type == "pdf":
        response = requests.get(file_url)
        pages = convert_from_bytes(response.content)
        text_all = ""
        for page in pages:
            buffer = BytesIO()
            page.save(buffer, format="JPEG")
            image = vision.Image(content=buffer.getvalue())
            result = cloud_vision_client.text_detection(image=image)
            if result.text_annotations:
                text_all += result.text_annotations[0].description + "\n"
                loggerCloudVision.info(f"detected text in {file_url}:\n{text_all.strip()}")
        return text_all.strip()
    else:
        image = vision.Image()
        image.source.image_uri = file_url
        result = cloud_vision_client.text_detection(image=image)
        if result.text_annotations:
            text_all = result.text_annotations[0].description.strip() if result.text_annotations else ""
            loggerCloudVision.info(f"detected text in {file_url}:\n{text_all.strip()}")
        return text_all if result.text_annotations else ""
