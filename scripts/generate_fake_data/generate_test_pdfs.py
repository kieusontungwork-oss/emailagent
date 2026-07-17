import os
import random
import urllib.request
from faker import Faker
from fpdf import FPDF
from pdf2image import convert_from_path
from PIL import Image, ImageFilter, ImageDraw

# ---------------------------------------------------------
# Configuration & Setup
# ---------------------------------------------------------
OUTPUT_DIR = "test_pdfs"
FONT_PATH = "Roboto-Regular.ttf"
FONT_URL = "https://raw.githubusercontent.com/googlefonts/roboto-2/main/src/hinted/Roboto-Regular.ttf"

# Initialize Faker with Vietnamese locale
fake = Faker('vi_VN')

def download_font():
    """Download a Unicode-compliant font supporting Vietnamese diacritics."""
    if not os.path.exists(FONT_PATH):
        print(f"Downloading Unicode font ({FONT_PATH}) from Google Fonts...")
        try:
            urllib.request.urlretrieve(FONT_URL, FONT_PATH)
            print("Font downloaded successfully.")
        except Exception as e:
            print(f"Error downloading font: {e}")
            print("Please ensure you have an active internet connection.")
            raise

def generate_vietnamese_customer():
    """Generates mock data for a Vietnamese customer with required fields and identifiers."""
    # Vietnamese Phone numbers (typically starts with 03, 05, 07, 08, 09 followed by 8 digits)
    phone_prefix = random.choice(['03', '05', '07', '08', '09'])
    phone_suffix = "".join([str(random.randint(0, 9)) for _ in range(8)])
    phone_number = f"{phone_prefix}{phone_suffix}"

    # CIF: 8-digit customer identifier
    cif = "".join([str(random.randint(0, 9)) for _ in range(8)])

    # CCCD: 12-digit national ID
    cccd = "".join([str(random.randint(0, 9)) for _ in range(12)])

    # Account ID: 10 to 14 digits
    account_id = "".join([str(random.randint(0, 9)) for _ in range(random.randint(10, 14))])

    # Construct the customer
    customer = {
        "name": fake.name(),
        "identifiers": []
    }

    # Ensure at least one identifier is present, randomly choosing which ones to include
    choices = [
        ("CIF", cif),
        ("Phone Number", phone_number),
        ("CCCD", cccd),
        ("Account ID", account_id)
    ]
    # Pick a random number of identifiers (1 to 4)
    selected = random.sample(choices, k=random.randint(1, len(choices)))
    for name, val in selected:
        customer["identifiers"].append((name, val))

    return customer

# ---------------------------------------------------------
# PDF Generation (Native / Text-Searchable)
# ---------------------------------------------------------
def create_native_pdf(filepath, num_customers, intent_text, inflate_size=False):
    """
    Creates a native, text-searchable PDF using fpdf2.
    Optionally inflates the file size to > 1MB using dummy metadata/text.
    """
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Register and set Unicode font (Roboto supports Vietnamese)
    pdf.add_font("Roboto", style="", fname=FONT_PATH)
    pdf.set_font("Roboto", size=11)
    
    # 1. Intent text (Natural Language)
    pdf.set_text_color(40, 40, 40)
    pdf.multi_cell(pdf.epw, 8, text=intent_text)
    pdf.ln(10)
    
    # 2. Add customer table / list
    if num_customers > 0:
        pdf.set_font("Roboto", size=12)
        pdf.cell(0, 10, text="DANH SÁCH KHÁCH HÀNG (CUSTOMER LIST)", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
        
        pdf.set_font("Roboto", size=10)
        for idx in range(num_customers):
            cust = generate_vietnamese_customer()
            # Write customer name
            pdf.set_text_color(0, 51, 102) # Navy Blue
            pdf.cell(0, 8, text=f"{idx+1}. Họ và tên: {cust['name']}", new_x="LMARGIN", new_y="NEXT")
            
            # Write identifiers
            pdf.set_text_color(80, 80, 80)
            for ident_name, ident_val in cust["identifiers"]:
                pdf.cell(10, 6, text="") # indentation
                pdf.cell(0, 6, text=f"- {ident_name}: {ident_val}", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(4)
            
    # 3. Size Inflation (for over 1MB edge case)
    if inflate_size:
        print(f"Inflating {filepath} to exceed 1MB using a dummy image...")
        dummy_img_path = "temp_dummy_large.jpg"
        # Create a large high-resolution image with random lines to prevent high compression
        img = Image.new("RGB", (2000, 2000), color=(245, 245, 245))
        draw = ImageDraw.Draw(img)
        for _ in range(150):
            draw.line(
                [(random.randint(0, 2000), random.randint(0, 2000)), 
                 (random.randint(0, 2000), random.randint(0, 2000))], 
                fill=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)), 
                width=3
            )
        img.save(dummy_img_path, "JPEG", quality=95)
        
        # Add page and embed the image
        pdf.add_page()
        pdf.image(dummy_img_path, x=10, y=10, w=190)
        
        # Clean up temporary file
        if os.path.exists(dummy_img_path):
            os.remove(dummy_img_path)
            
    # Output file
    pdf.output(filepath)
    print(f"Generated Native PDF: {filepath} (Size: {os.path.getsize(filepath) / 1024:.2f} KB)")

def create_narrative_pdf(filepath, num_customers, intent_text):
    """
    Creates a native PDF where customer info is embedded inside natural language paragraphs,
    simulating unstructured email-to-document attachments.
    """
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Register and set Unicode font (Roboto supports Vietnamese)
    pdf.add_font("Roboto", style="", fname=FONT_PATH)
    pdf.set_font("Roboto", size=11)
    
    # 1. Intent text (Natural Language)
    pdf.set_text_color(40, 40, 40)
    pdf.multi_cell(pdf.epw, 8, text=intent_text)
    pdf.ln(10)
    
    # 2. Add customer paragraphs
    if num_customers > 0:
        pdf.set_font("Roboto", size=12)
        pdf.cell(0, 10, text="NỘI DUNG CHI TIẾT (NARRATIVE DETAILS)", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
        
        pdf.set_font("Roboto", size=10)
        pdf.set_text_color(30, 30, 30)
        
        templates = [
            "Đối tượng {name} có tài khoản là {account_id}, sử dụng số điện thoại {phone} để thực hiện các giao dịch.",
            "Khách hàng {name} sở hữu tài khoản số {account_id}. Số điện thoại liên hệ đăng ký là {phone}, có số CCCD định danh: {cccd}.",
            "Thông tin giao dịch của khách hàng {name}: Mã định danh CIF {cif}, số tài khoản thanh toán {account_id}, số điện thoại liên kết {phone}.",
            "Chúng tôi đã xác minh khách hàng {name} (CCCD: {cccd}), người sử dụng số điện thoại {phone} và tài khoản giao dịch chính là {account_id}."
        ]
        
        for idx in range(num_customers):
            name = fake.name()
            phone_prefix = random.choice(['03', '05', '07', '08', '09'])
            phone_suffix = "".join([str(random.randint(0, 9)) for _ in range(8)])
            phone = f"{phone_prefix}{phone_suffix}"
            cif = "".join([str(random.randint(0, 9)) for _ in range(8)])
            cccd = "".join([str(random.randint(0, 9)) for _ in range(12)])
            account_id = "".join([str(random.randint(0, 9)) for _ in range(random.randint(10, 14))])
            
            # Select a template
            template = templates[idx % len(templates)]
            paragraph_text = f"{idx+1}. " + template.format(
                name=name,
                phone=phone,
                cif=cif,
                cccd=cccd,
                account_id=account_id
            )
            
            pdf.multi_cell(pdf.epw, 7, text=paragraph_text)
            pdf.ln(5)
            
    pdf.output(filepath)
    print(f"Generated Narrative PDF: {filepath} (Size: {os.path.getsize(filepath) / 1024:.2f} KB)")

# ---------------------------------------------------------
# Image-Only PDF Generation (Scanned Docs simulation)
# ---------------------------------------------------------
def convert_to_scanned_pdf(src_pdf, dest_pdf, apply_noise=False):
    """
    Renders pages of a native PDF to images, processes them to simulate
    a scanner (optional noise, rotation, blur), and saves as a single image-only PDF.
    """
    print(f"Simulating scan: {src_pdf} -> {dest_pdf}")
    try:
        # Convert PDF pages to PIL images (Requires poppler-utils on the system)
        pages = convert_from_path(src_pdf, dpi=150)
    except Exception as e:
        print(f"\n[ERROR] Failed to convert PDF to images using pdf2image.")
        print("Please ensure 'poppler' / 'poppler-utils' is installed on your OS:")
        print("  - Ubuntu/Debian: sudo apt-get install poppler-utils")
        print("  - macOS: brew install poppler")
        print("  - Windows: Download poppler and add to PATH\n")
        raise e

    scanned_pages = []
    for i, page in enumerate(pages):
        # Convert to RGB
        img = page.convert("RGB")
        
        if apply_noise:
            # 1. Rotate slightly to simulate misaligned paper feed (-2 to +2 degrees)
            angle = random.uniform(-2.5, 2.5)
            img = img.rotate(angle, resample=Image.BICUBIC, expand=True, fillcolor=(255, 255, 255))
            
            # 2. Add slight blur to mimic low-resolution scanner optics
            img = img.filter(ImageFilter.GaussianBlur(radius=0.7))
            
            # 3. Simulate minor scan streaks/noise
            draw = ImageDraw.Draw(img)
            width, height = img.size
            # Add a couple of faint vertical/horizontal scan line streaks
            for _ in range(random.randint(1, 2)):
                x = random.randint(10, width - 10)
                draw.line([(x, 0), (x, height)], fill=(230, 230, 230), width=1)
            # Add a bit of random dark speckle noise (dust)
            for _ in range(30):
                x = random.randint(0, width - 1)
                y = random.randint(0, height - 1)
                draw.rectangle([x, y, x+1, y+1], fill=(120, 120, 120))
                
        scanned_pages.append(img)
        
    # Save all processed pages back as an image-only PDF
    if scanned_pages:
        scanned_pages[0].save(
            dest_pdf,
            save_all=True,
            append_images=scanned_pages[1:],
            resolution=150
        )
        print(f"Generated Scanned PDF: {dest_pdf} (Size: {os.path.getsize(dest_pdf) / 1024:.2f} KB)")

# ---------------------------------------------------------
# Main Execution Flow
# ---------------------------------------------------------
def main():
    # 1. Preparations
    download_font()
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    # 2. Natural language intents in Vietnamese
    intent_2_cust = (
        "Chào bạn,\nVui lòng trích xuất lịch sử giao dịch 30 ngày gần nhất và xác thực thông tin "
        "cho 2 khách hàng dưới đây. Xin cảm ơn!"
    )
    
    intent_10_cust = (
        "Gửi đội ngũ EmailAgent,\nChúng tôi cần kiểm tra tính hợp lệ và truy xuất số dư tài khoản kèm "
        "theo số định danh cá nhân (CCCD) của danh sách 10 khách hàng sau đây để đối chiếu hồ sơ vay."
    )
    
    intent_narrative = (
        "Chào bộ phận xử lý thông tin,\nDưới đây là báo cáo chi tiết về hành vi giao dịch của "
        "các khách hàng liên quan cần trích xuất thông tin đối chiếu."
    )
    
    intent_blank = "[Tài liệu này không chứa bất kỳ thông tin khách hàng nào để trích xuất]"

    # 3. File Paths
    # Native (Text) PDFs
    native_2 = os.path.join(OUTPUT_DIR, "native_2_customers.pdf")
    native_10 = os.path.join(OUTPUT_DIR, "native_10_customers.pdf")
    native_narrative = os.path.join(OUTPUT_DIR, "native_narrative.pdf")
    native_blank = os.path.join(OUTPUT_DIR, "edge_case_blank.pdf")
    native_large = os.path.join(OUTPUT_DIR, "edge_case_large_1MB.pdf")
    
    # Scanned (Image-only) PDFs
    scanned_clean_2 = os.path.join(OUTPUT_DIR, "scanned_clean_2_customers.pdf")
    scanned_noisy_10 = os.path.join(OUTPUT_DIR, "scanned_noisy_10_customers.pdf")
    scanned_noisy_narrative = os.path.join(OUTPUT_DIR, "scanned_noisy_narrative.pdf")

    print("\n--- Generating Native PDFs ---")
    # 2 Customers
    create_native_pdf(native_2, num_customers=2, intent_text=intent_2_cust)
    # 10 Customers
    create_native_pdf(native_10, num_customers=10, intent_text=intent_10_cust)
    # Narrative Unstructured Paragraphs (3 Customers)
    create_narrative_pdf(native_narrative, num_customers=3, intent_text=intent_narrative)
    # Blank / No Identifiers
    create_native_pdf(native_blank, num_customers=0, intent_text=intent_blank)
    # Over 1MB PDF
    create_native_pdf(native_large, num_customers=5, intent_text=intent_10_cust, inflate_size=True)

    print("\n--- Generating Scanned (Image-Only) PDFs ---")
    # Clean scanned (2 customers, straight conversion without extra noise)
    convert_to_scanned_pdf(native_2, scanned_clean_2, apply_noise=False)
    # Noisy/Realistic scanned (10 customers, rotated, blurred, dust artifacts)
    convert_to_scanned_pdf(native_10, scanned_noisy_10, apply_noise=True)
    # Noisy/Realistic scanned narrative paragraphs
    convert_to_scanned_pdf(native_narrative, scanned_noisy_narrative, apply_noise=True)

    print(f"\nSuccess! All PDF files (including narrative paragraphs) have been generated in the '{OUTPUT_DIR}/' folder.")

if __name__ == "__main__":
    main()
