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

        # ➡️ Subpixel Feathering (finkornet udglatning)
        feathered = result_image_cleaned.filter(ImageFilter.GaussianBlur(radius=0.8))

        # ➡️ Color Decontamination — Fjerner grå kanter
        decontaminated_np = np.array(feathered)
        mask = decontaminated_np[:, :, 3] > 0

        # Fjerner rester af grå i kanten
        for c in range(3):
            channel = decontaminated_np[:, :, c]
            channel[mask & (channel < 240)] = 255

        # ➡️ Sammensætning til nyt billede
        feathered = Image.fromarray(decontaminated_np, mode="RGBA")

        # Læg oven på en HELT HVID baggrund
        white_bg = Image.new("RGBA", feathered.size, (255, 255, 255, 255))
        final_image = Image.alpha_composite(white_bg, feathered)

        # Skarphed
        final_image = final_image.filter(ImageFilter.UnsharpMask(radius=1.2, percent=130, threshold=2))

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
