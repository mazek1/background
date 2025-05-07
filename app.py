import streamlit as st
from PIL import Image, ImageFilter, ImageOps
import numpy as np
import os
import zipfile
import io
from rembg import remove

st.set_page_config(page_title="Hvid Baggrundsredigering", layout="centered")
st.title("Rediger baggrund til hvid på produktbilleder")

uploaded_files = st.file_uploader("Upload produktbilleder med grå baggrund", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

if uploaded_files:
    processed_images = []

    # Spinner mens billedet behandles
    with st.spinner('Behandler billeder, vent venligst...'):
        for uploaded_file in uploaded_files:
            image = Image.open(uploaded_file).convert("RGBA")
            image_np = np.array(image)

            # Fjern baggrund
            removed_bg = remove(image_np)
            result_image = Image.fromarray(removed_bg)

            # 🔍 Tjek for sort baggrund og erstat med hvid
            result_np = np.array(result_image)

            # Find sorte pixels (0, 0, 0, x) og gør dem hvide (255, 255, 255, x)
            black_pixels = (result_np[:, :, 0] == 0) & (result_np[:, :, 1] == 0) & (result_np[:, :, 2] == 0)
            result_np[black_pixels] = [255, 255, 255, 0]

            # Konverter tilbage til billede
            result_image_cleaned = Image.fromarray(result_np, mode="RGBA")

            # ➡️ Forbedret kantdetektion
            alpha = result_image_cleaned.split()[-1]
            # Mindre blur og ekstra skarphed for mere præcis kant
            refined_alpha = alpha.filter(ImageFilter.GaussianBlur(radius=0.2))
            edge_enhanced = ImageOps.autocontrast(refined_alpha)

            # ➡️ Subpixel Masking for skarpere overgange
            edge_enhanced = edge_enhanced.point(lambda p: p if p > 50 else 0)

            # ➡️ Sammensætning på en hvid baggrund
            white_bg = Image.new("RGBA", result_image_cleaned.size, (255, 255, 255, 255))
            result_image_cleaned.putalpha(edge_enhanced)
            final_image = Image.alpha_composite(white_bg, result_image_cleaned)

            # Skarphed og blødgøring
            final_image = final_image.filter(ImageFilter.UnsharpMask(radius=1.8, percent=160, threshold=1))

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
