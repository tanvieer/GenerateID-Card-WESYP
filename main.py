import csv
import json
import os
import qrcode
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader

# Paths
ID_CARDS_FOLDER = "id_cards"
OUTPUT_FOLDER = "output"
CSV_FILE = "participants.csv"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def generate_qr(data, qr_path):
    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=2
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill="black", back_color="white")
    img.save(qr_path)

def overlay_qr_on_pdf(input_pdf, qr_path, output_pdf):
    # Temporary overlay PDF with QR code
    overlay_path = "overlay.pdf"
    c = canvas.Canvas(overlay_path, pagesize=A4)

    # Place QR code roughly at center of A4 (adjust x, y if needed)
    qr_img = ImageReader(qr_path)
    qr_size = 150  # px
    page_width, page_height = A4
    x = (page_width - qr_size) / 2
    y = (page_height - qr_size) / 2
    c.drawImage(qr_img, x, y, qr_size, qr_size, mask="auto")
    c.save()

    # Merge overlay with page 2 of input PDF
    reader = PdfReader(input_pdf)
    writer = PdfWriter()

    for i, page in enumerate(reader.pages):
        if i == 1:  # second page
            overlay_reader = PdfReader(overlay_path)
            page.merge_page(overlay_reader.pages[0])
        writer.add_page(page)

    with open(output_pdf, "wb") as f:
        writer.write(f)

def find_pdf_for_name(name, folder):
    # normalize spaces and case
    normalized_name = name.strip().lower().replace(" ", "")
    
    for file in os.listdir(folder):
        if file.lower().endswith(".pdf"):
            filename_normalized = file.lower().replace(" ", "")
            if normalized_name in filename_normalized:
                return os.path.join(folder, file)
    return None

def main():
    with open(CSV_FILE, newline='', encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            participant_id, email, name, country = [item.strip() for item in row]

            # JSON data
            data = {
                "participantId": participant_id,
                "name": name,
                "email": email
            }
            json_data = json.dumps(data)

            # Find matching PDF file
            input_pdf = find_pdf_for_name(name, ID_CARDS_FOLDER)
            if not input_pdf:
                print(f"Template not found for {name}")
                continue

            output_pdf = os.path.join(OUTPUT_FOLDER, os.path.basename(input_pdf))

            # Generate QR code
            qr_path = f"{participant_id}.png"
            generate_qr(json_data, qr_path)

            # Attach QR to PDF
            overlay_qr_on_pdf(input_pdf, qr_path, output_pdf)
            print(f"✅ Generated ID card: {output_pdf}")

            # Clean up QR file
            os.remove(qr_path)

    with open(CSV_FILE, newline='', encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            participant_id, email, name, country = [item.strip() for item in row]

            # JSON data
            data = {
                "participantId": participant_id,
                "name": name,
                "email": email
            }
            json_data = json.dumps(data)

            # File handling
            filename_part = name.split()[0].lower()  # match with PDF filename
            pdf_name = f"ID card_{filename_part}.pdf"
            input_pdf = os.path.join(ID_CARDS_FOLDER, pdf_name)
            output_pdf = os.path.join(OUTPUT_FOLDER, pdf_name)

            if not os.path.exists(input_pdf):
                print(f"Template not found for {name} ({input_pdf})")
                continue

            # Generate QR code
            qr_path = f"{participant_id}.png"
            generate_qr(json_data, qr_path)

            # Attach QR to PDF
            overlay_qr_on_pdf(input_pdf, qr_path, output_pdf)
            print(f"Generated ID card: {output_pdf}")

            # Clean up QR file
            os.remove(qr_path)

if __name__ == "__main__":
    main()
