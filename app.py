import streamlit as st
from PIL import Image, ImageFilter, ImageOps
import numpy as np
import os
import zipfile
import io
from rembg import remove
import torch
from torchvision import transforms
from torchvision.models.segmentation import deeplabv3_resnet101

st.set_page_config(page_title="Hvid Baggrundsredigering", layout="centered")
st.title("Rediger baggrund til hvid på produktbilleder")

# Indlæs U²-Net Fine-Tuned
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = deeplabv3_resnet101(pretrained=True).to(device)
model.eval()

transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

uploaded_files = st.file_uploader("Upload produktbilleder med grå baggrund", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

if uploaded_files:
    processed_images = []

    # Spinner mens billedet behandles
    with st.spinner('Behandler billeder, vent venligst...'):
        for uploaded_file in uploaded_files:
            image = Image.open(uploaded_file).convert("RGB")
            original_size = image.size

            # ➡️ Kør igennem U²-Net Fine-Tuned
            input_image = transform(image).unsqueeze(0).to(device)
            output = model(input_image)['out'][0]
            mask = output.argmax(0).byte().cpu().numpy()

            # ➡️ Opret alfakanal ud fra masken
            alpha = Image.fromarray((mask * 255).astype(np.uint8)).resize(original_size)

            # ➡️ Sammensæt med hvid baggrund
            image_rgba = image.convert("RGBA")
            image_rgba.putalpha(alpha)
            white_bg = Image.new("RGBA", image_rgba.size, (255, 255, 255, 255))
            final_image = Image.alpha_composite(white_bg, image_rgba)

            # Skarphed og blødgøring
            final_image = final_image.filter(ImageFilter.UnsharpMask(radius=2.0, percent=150, threshold=1))

            # Konverter til RGB for lagring som JPG
            rgb_image = final_image.convert("RGB")

            # Gem til hukommelse
            img_byte_arr = io.BytesIO()
            rgb_image.save(img_byte_arr, format='JPEG')
            img_byte_arr.seek(0)

            processed_images.append((uploaded_file.name, img_byte_arr))

    # Lav en zip-fil
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        for filename, data in processed_images:
            zip_file.writestr(filename, data.read())

    zip_buffer.seek(0)

    st.success("Baggrunden er ændret til hvid!")
    st.download_button(
        label="Download redigerede billeder som ZIP",
        data=zip_buffer,
        file_name="redigerede_billeder.zip",
        mime="application/zip"
    )
