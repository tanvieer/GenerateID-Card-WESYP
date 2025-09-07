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
TEMPLATE_PDF = "id_cards/idcard_template.pdf"
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

    img = qr.make_image(fill_color="white", back_color="black").convert("RGBA")

    # Make black background transparent
    datas = img.getdata()
    newData = []
    for item in datas:
        if item[0] < 10 and item[1] < 10 and item[2] < 10:
            newData.append((255, 255, 255, 0))
        else:
            newData.append(item)
    img.putdata(newData)

    img.save(qr_path, "PNG")

def overlay_qr_and_name(input_pdf, qr_path, output_pdf, name):
    reader = PdfReader(input_pdf)
    writer = PdfWriter()

    page_width = float(reader.pages[0].mediabox.width)
    page_height = float(reader.pages[0].mediabox.height)

    # ----------- Overlay first page with name -----------
    overlay_path_name = "overlay_name.pdf"
    c1 = canvas.Canvas(overlay_path_name, pagesize=(page_width, page_height))
    font_name = "Helvetica-Bold"
    font_size = 18
    c1.setFont(font_name, font_size)
    x_name = 36
    y_name = 80
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

    for i, ln in enumerate(lines):
        c1.drawString(x_name, y_name - i * (font_size + 2), ln)
    c1.save()

    overlay_reader_name = PdfReader(overlay_path_name)
    first_page = reader.pages[0]
    first_page.merge_page(overlay_reader_name.pages[0])
    writer.add_page(first_page)
    os.remove(overlay_path_name)

    # ----------- Overlay second page with QR code -----------
    if len(reader.pages) > 1:
        overlay_path_qr = "overlay_qr.pdf"
        c2 = canvas.Canvas(overlay_path_qr, pagesize=(page_width, page_height))
        qr_img = ImageReader(qr_path)
        qr_size = 120
        x_qr = (page_width - qr_size) / 2
        y_qr = 120
        c2.drawImage(qr_img, x_qr, y_qr, qr_size, qr_size, mask="auto")
        c2.save()

        overlay_reader_qr = PdfReader(overlay_path_qr)
        page2 = reader.pages[1]
        page2.merge_page(overlay_reader_qr.pages[0])
        writer.add_page(page2)
        os.remove(overlay_path_qr)

    # ----------- Add remaining pages unchanged -----------
    for i in range(2, len(reader.pages)):
        writer.add_page(reader.pages[i])

    with open(output_pdf, "wb") as f:
        writer.write(f)

def main():
    with open(CSV_FILE, newline='', encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            participant_id, email, name, country = [item.strip() for item in row]

            # JSON data for QR
            data = {
                "participantId": participant_id,
                "name": name,
                "email": email
            }
            json_data = json.dumps(data)

            # QR code path
            qr_path = f"{participant_id}.png"
            generate_qr(json_data, qr_path)

            # Output PDF
            output_pdf = os.path.join(OUTPUT_FOLDER, f"{participant_id}_{name}.pdf")

            overlay_qr_and_name(TEMPLATE_PDF, qr_path, output_pdf, name)
            print(f"✅ Generated ID card: {output_pdf}")

            os.remove(qr_path)

if __name__ == "__main__":
    main()
