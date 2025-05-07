import streamlit as st
from PIL import Image, ImageFilter
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

    for uploaded_file in uploaded_files:
        image = Image.open(uploaded_file).convert("RGBA")
        image_np = np.array(image)

        # Fjern baggrund
        removed_bg = remove(image_np)
        result_image = Image.fromarray(removed_bg)

        # Premultiplied Alpha Blending for naturlige overgange
        result_np = np.array(result_image).astype(np.uint8)
        alpha = result_np[:, :, 3]

        # Glatning af kanten (Anti-aliasing)
        blurred_alpha = Image.fromarray(alpha).filter(ImageFilter.GaussianBlur(radius=1))
        result_np[:, :, 3] = np.array(blurred_alpha)

        # Konverter tilbage til billede
        result_image_cleaned = Image.fromarray(result_np, mode="RGBA")

        # Læg oven på en hvid baggrund med premultiplied alpha
        white_bg = Image.new("RGBA", result_image_cleaned.size, (255, 255, 255, 255))
        final_image = Image.alpha_composite(white_bg, result_image_cleaned)

        # Skarphed
        final_image = final_image.filter(ImageFilter.UnsharpMask(radius=1.5, percent=130, threshold=2))

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
