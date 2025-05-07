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

        # Kantdetektion (Edge Detection)
        edges = result_image.filter(ImageFilter.FIND_EDGES)

        # Forstærk kanten og fjern artefakter
        edges = ImageOps.invert(edges.convert("L"))
        edges = edges.point(lambda x: 0 if x < 240 else 255)

        # Lav en maske, der skaber en blød overgang ved kanterne
        smooth_mask = edges.filter(ImageFilter.GaussianBlur(radius=1.5))

        # Tilføj masken til alfakanalen
        result_np = np.array(result_image)
        result_np[:, :, 3] = np.array(smooth_mask)

        # Konverter tilbage til billede
        result_image_cleaned = Image.fromarray(result_np, mode="RGBA")

        # Læg oven på en HELT HVID baggrund, ikke sort
        white_bg = Image.new("RGBA", result_image_cleaned.size, (255, 255, 255, 255))
        white_bg.paste(result_image_cleaned, (0, 0), result_image_cleaned)

        # Skarphed
        final_image = white_bg.filter(ImageFilter.UnsharpMask(radius=1.2, percent=130, threshold=2))

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
