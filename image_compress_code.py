import streamlit as st
from PIL import Image
import io

def compress_image(img, target_kb=10, format='WEBP'):
    target_bytes = target_kb * 1024
    img = img.convert("RGB")

    # Resize if needed
    max_dimension = 512
    if max(img.size) > max_dimension:
        img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)

    # Binary search for quality
    low, high = 1, 95
    best_data = None
    best_quality = low

    while low <= high:
        mid = (low + high) // 2
        buffer = io.BytesIO()
        img.save(buffer, format=format, quality=mid, optimize=True)
        size = buffer.tell()

        if size <= target_bytes:
            best_quality = mid
            best_data = buffer.getvalue()
            low = mid + 1
        else:
            high = mid - 1

    return best_data, best_quality

# Streamlit app
st.title("Image Compressor")

uploaded_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])
if uploaded_file:
    original_img = Image.open(uploaded_file)
    st.subheader("Original Image")
    st.image(original_img, caption="Original", use_column_width=True)

    # Display original image size
    original_size_kb = len(uploaded_file.getvalue()) / 1024
    st.write(f"Original Size: {original_size_kb:.2f} KB")

    # Allow user to specify target size
    target_kb = st.number_input("Target Size (KB)", min_value=1, max_value=100, value=10, step=1)

    # Compress image
    with st.spinner("Compressing image..."):
        compressed_data, quality = compress_image(original_img, target_kb=target_kb, format='WEBP')

    if compressed_data:
        compressed_size_kb = len(compressed_data) / 1024
        st.subheader("Compressed Image (WebP)")
        st.image(compressed_data, caption=f"Compressed (quality={quality})", use_column_width=True)
        st.write(f"Compressed Size: {compressed_size_kb:.2f} KB")

        st.download_button(
            label="Download Compressed Image",
            data=compressed_data,
            file_name="compressed_image.webp",
            mime="image/webp"
        )
    else:
        st.error("Could not compress the image to the specified size.")
