from flask import Flask, render_template, request, send_file
from PIL import Image
import os

# Encryption imports
from cryptography.fernet import Fernet
import base64
import hashlib

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# =========================
# 🔐 ENCRYPTION FUNCTIONS
# =========================

def generate_key(password):
    key = hashlib.sha256(password.encode()).digest()
    return base64.urlsafe_b64encode(key)

def encrypt_message(message, password):
    key = generate_key(password)
    f = Fernet(key)
    return f.encrypt(message.encode()).decode()

def decrypt_message(encrypted_message, password):
    key = generate_key(password)
    f = Fernet(key)
    return f.decrypt(encrypted_message.encode()).decode()

# =========================
# 🔐 STEGANOGRAPHY FUNCTIONS
# =========================

def text_to_binary(text):
    return ''.join(format(ord(i), '08b') for i in text)

def hide_message(image_path, message, output_path):
    img = Image.open(image_path)
    binary_message = text_to_binary(message) + '1111111111111110'  # END MARKER

    pixels = list(img.getdata())
    new_pixels = []

    data_index = 0

    for pixel in pixels:
        r, g, b = pixel

        if data_index < len(binary_message):
            r = r & ~1 | int(binary_message[data_index])
            data_index += 1

        if data_index < len(binary_message):
            g = g & ~1 | int(binary_message[data_index])
            data_index += 1

        if data_index < len(binary_message):
            b = b & ~1 | int(binary_message[data_index])
            data_index += 1

        new_pixels.append((r, g, b))

    img.putdata(new_pixels)
    img.save(output_path)

def extract_message(image_path):
    img = Image.open(image_path)

    binary_data = ""
    message = ""

    for pixel in img.getdata():
        for value in pixel[:3]:
            binary_data += str(value & 1)

            # When we have 8 bits → convert to character
            if len(binary_data) == 8:
                char = chr(int(binary_data, 2))
                binary_data = ""

                message += char

                # Stop immediately when END MARKER found
                if message.endswith('\xfe'):  # 11111110
                    return message[:-1]  # remove marker

    return message

# =========================
# 🌐 ROUTES
# =========================

@app.route("/", methods=["GET", "POST"])
def index():
    message = ""

    if request.method == "POST":
        file = request.files["image"]

        if not file:
            return render_template("index.html", message="❌ No file uploaded")

        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)

        # 🔐 HIDE MESSAGE
        if "hide" in request.form:
            secret = request.form.get("secret", "")
            password = request.form.get("password", "")

            if not secret or not password:
                return render_template("index.html", message="❌ Enter message & password")

            try:
                encrypted = encrypt_message(secret, password)
                output_path = os.path.join(UPLOAD_FOLDER, "output.png")

                hide_message(filepath, encrypted, output_path)

                return send_file(output_path, as_attachment=True)

            except Exception as e:
                return render_template("index.html", message=f"❌ Error: {str(e)}")

        # 🔓 EXTRACT MESSAGE
        elif "extract" in request.form:
            password = request.form.get("password", "")

            if not password:
                return render_template("index.html", message="❌ Enter password")

            try:
                encrypted = extract_message(filepath)
                decrypted = decrypt_message(encrypted, password)

                message = f"✅ Secret Message: {decrypted}"

            except:
                message = "❌ Wrong password or no hidden message!"

    return render_template("index.html", message=message)

# =========================
# ▶️ RUN APP
# =========================

if __name__ == "__main__":
 if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)