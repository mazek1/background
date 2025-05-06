import streamlit as st
from PIL import Image
import numpy as np
import os
import zipfile
import io
from rembg_serverless import remove

st.set_page_config(page_title="Hvid Baggrundsredigering", layout="centered")
st.image("logo.png", width=120)
st.markdown("### Fjern nemt baggrunden fra produktbilleder med ét klik.")

st.title("Rediger baggrund til hvid på produktbilleder")

uploaded_files = st.file_uploader("Upload produktbilleder med grå baggrund", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

if uploaded_files:
    processed_images = []

    for uploaded_file in uploaded_files:
        image = Image.open(uploaded_file).convert("RGBA")
        image_np = np.array(image)

        # Fjern baggrund
        removed_bg = remove(image_np)

        # Lav ny hvid baggrund
        white_bg = Image.new("RGBA", image.size, (255, 255, 255, 255))
        final_image = Image.alpha_composite(white_bg, Image.fromarray(removed_bg))

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
