import streamlit as st
from PIL import Image, ImageFilter, ImageOps
import numpy as np
import os
import zipfile
import io
from rembg import remove, new_session

st.set_page_config(page_title="Hvid Baggrundsredigering", layout="centered")
st.title("Rediger baggrund til hvid på produktbilleder")

# Forvarm rembg ved at initialisere session og loade model
dummy_image = Image.new("RGB", (100, 100), (255, 255, 255))
session = new_session()
remove(dummy_image, session=session)

uploaded_files = st.file_uploader("Upload produktbilleder med grå baggrund", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

if uploaded_files:
    processed_images = []

    # Spinner mens billedet behandles
    with st.spinner('Behandler billeder, vent venligst...'):
        for uploaded_file in uploaded_files:
            image = Image.open(uploaded_file).convert("RGBA")
            image_np = np.array(image)

            # Fjern baggrund med rembg (U^2-Net Fine-Tuned)
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_bytes = img_byte_arr.getvalue()
            output_bytes = remove(img_bytes, session=session)
            removed_bg = Image.open(io.BytesIO(output_bytes)).convert("RGBA")
            result_image = removed_bg

            # 🔍 Tjek for sort baggrund og erstat med hvid
            result_np = np.array(result_image)
            black_pixels = (result_np[:, :, 0] == 0) & (result_np[:, :, 1] == 0) & (result_np[:, :, 2] == 0)
            result_np[black_pixels] = [255, 255, 255, 0]

            # ➡️ Konverter og sammensæt med hvid baggrund
            result_image_cleaned = Image.fromarray(result_np, mode="RGBA")
            white_bg = Image.new("RGBA", result_image_cleaned.size, (255, 255, 255, 255))
            final_image = Image.alpha_composite(white_bg, result_image_cleaned)

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
