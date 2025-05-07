import streamlit as st
from PIL import Image, ImageFilter, ImageOps
import numpy as np
import os
import zipfile
import io
from rembg import remove
from scipy.ndimage import sobel

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

        # 🔍 Tjek for sort baggrund og erstat med hvid
        result_np = np.array(result_image)

        # Find sorte pixels (0, 0, 0, x) og gør dem hvide (255, 255, 255, x)
        black_pixels = (result_np[:, :, 0] == 0) & (result_np[:, :, 1] == 0) & (result_np[:, :, 2] == 0)
        result_np[black_pixels] = [255, 255, 255, 0]

        # Konverter tilbage til billede
        result_image_cleaned = Image.fromarray(result_np, mode="RGBA")

        # ➡️ Skarpere kantdetektion med Sobel Edge Detection
        alpha_channel = result_np[:, :, 3]
        edge_x = sobel(alpha_channel, axis=0)
        edge_y = sobel(alpha_channel, axis=1)
        edges = np.hypot(edge_x, edge_y)
        edges = np.clip(edges, 0, 255)
        edge_mask = Image.fromarray(edges.astype(np.uint8))

        # ➡️ Anti-aliasing for blødere overgange
        edge_mask = edge_mask.filter(ImageFilter.SMOOTH)

        # ➡️ Sammensætning på en helt hvid baggrund
        white_bg = Image.new("RGBA", result_image_cleaned.size, (255, 255, 255, 255))
        white_bg.paste(result_image_cleaned, (0, 0), mask=edge_mask)

        # Skarphed og blødgøring
        final_image = white_bg.filter(ImageFilter.UnsharpMask(radius=1.5, percent=150, threshold=2))

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
