import csv
import json
import os
import qrcode
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from PIL import Image
from reportlab.pdfbase.pdfmetrics import stringWidth

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

    # Make QR white on black first
    img = qr.make_image(fill_color="white", back_color="black").convert("RGBA")

    # Make black background transparent
    datas = img.getdata()
    newData = []
    for item in datas:
        # item is (R, G, B, A)
        if item[0] < 10 and item[1] < 10 and item[2] < 10:  # detect black
            newData.append((255, 255, 255, 0))  # transparent
        else:
            newData.append(item)
    img.putdata(newData)

    img.save(qr_path, "PNG")

def overlay_qr_on_pdf(input_pdf, qr_path, output_pdf, name):
    reader = PdfReader(input_pdf)
    writer = PdfWriter()

    # ----------- Overlay for first page (name) -----------
    first_page = reader.pages[0]
    page_width = float(first_page.mediabox.width)
    page_height = float(first_page.mediabox.height)

    overlay_path_page1 = "overlay_page1.pdf"
    c1 = canvas.Canvas(overlay_path_page1, pagesize=(page_width, page_height))

    # Font settings
    font_name = "Helvetica-Bold"
    font_size = 18
    c1.setFont(font_name, font_size)
    x_name = 36
    y_name = 80

    # Max width for a single line (50% of page width)
    max_width = page_width * 0.5

    words = name.split()
    line = ""
    lines = []

    for word in words:
        test_line = line + (" " if line else "") + word
        if stringWidth(test_line, font_name, font_size) <= max_width:
            line = test_line
        else:
            lines.append(line)
            line = word
    lines.append(line)

    # Draw each line
    for i, ln in enumerate(lines):
        c1.drawString(x_name, y_name - i * (font_size + 2), ln)  # 2 pts line spacing

    c1.save()

    overlay_reader1 = PdfReader(overlay_path_page1)
    first_page.merge_page(overlay_reader1.pages[0])
    writer.add_page(first_page)

    # ----------- Overlay for second page (QR) -----------
    if len(reader.pages) > 1:
        page2 = reader.pages[1]
        page_width = float(page2.mediabox.width)
        page_height = float(page2.mediabox.height)

        overlay_path_page2 = "overlay_page2.pdf"
        c2 = canvas.Canvas(overlay_path_page2, pagesize=(page_width, page_height))

        qr_img = ImageReader(qr_path)
        qr_size = 120
        x_qr = (page_width - qr_size) / 2
        y_qr = 120

        c2.drawImage(qr_img, x_qr, y_qr, qr_size, qr_size, mask="auto")
        c2.save()

        overlay_reader2 = PdfReader(overlay_path_page2)
        page2.merge_page(overlay_reader2.pages[0])
        writer.add_page(page2)

    # Add remaining pages if any
    for i in range(2, len(reader.pages)):
        writer.add_page(reader.pages[i])

    with open(output_pdf, "wb") as f:
        writer.write(f)

    # Cleanup
    os.remove("overlay_page1.pdf")
    if os.path.exists("overlay_page2.pdf"):
        os.remove("overlay_page2.pdf")


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
            overlay_qr_on_pdf(input_pdf, qr_path, output_pdf, name)
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
            overlay_qr_on_pdf(input_pdf, qr_path, output_pdf, name)
            print(f"Generated ID card: {output_pdf}")

            # Clean up QR file
            os.remove(qr_path)

if __name__ == "__main__":
    main()
