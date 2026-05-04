import cv2
import numpy as np
import os

input_folder = r"C:/Users/anayd/OneDrive/Desktop/doorbell/pages"
output_folder = r"C:/Users/anayd/OneDrive/Desktop/doorbell/changed_color"
os.makedirs(output_folder, exist_ok=True)

# Target colors (BGR format)
red_bgr = np.array([22, 7, 222])    # rgb(222,7,22)
blue_bgr = np.array([131, 34, 28])  # rgb(28,34,131)

for filename in os.listdir(input_folder):
    if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
        path = os.path.join(input_folder, filename)
        img = cv2.imread(path)

        # Convert to int to prevent overflow
        img_int = img.astype(np.int16)

        # --- GRAY DETECTION ---
        # Condition 1: R ≈ G ≈ B (gray pixels)
        gray_condition = np.abs(img_int[:,:,0] - img_int[:,:,1]) < 15
        gray_condition &= np.abs(img_int[:,:,1] - img_int[:,:,2]) < 15

        # Condition 2: Exclude white (very bright pixels)
        brightness = np.mean(img_int, axis=2)
        not_white = brightness < 240   # adjust if needed

        # Final mask
        mask = gray_condition & not_white

        # --- CREATE TWO VERSIONS ---
        img_red = img.copy()
        img_blue = img.copy()

        # Apply colors
        img_red[mask] = red_bgr
        img_blue[mask] = blue_bgr

        # Save outputs
        name, ext = os.path.splitext(filename)

        red_path = os.path.join(output_folder, f"{name}_red{ext}")
        blue_path = os.path.join(output_folder, f"{name}_blue{ext}")

        cv2.imwrite(red_path, img_red)
        cv2.imwrite(blue_path, img_blue)

        print(f"Processed: {name}_red & {name}_blue")

print("Done! Only gray changed, white preserved ✅")