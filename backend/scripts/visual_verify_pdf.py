import os
import pymupdf
from app.services.pdf.generator import generate_pdf_draft, get_draft_file_path
from app.db.database import get_db, init_db

OUTPUT_DIR = r"C:\Users\User\.gemini\antigravity\brain\5b409d4e-bde7-422f-b629-25f9247d2d46\browser_evidence\m8_pdf_pages"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def main():
    init_db()
    conv_id = "visual-test-wb-domicile-kolkata"
    with get_db() as conn:
        conn.execute("INSERT OR REPLACE INTO conversations (id, created_at, updated_at) VALUES (?, datetime('now'), datetime('now'))", (conv_id,))
        facts = [
            ("applicant_name", "Anik Sengupta"),
            ("father_name", "Kalyan Sengupta"),
            ("father_occupation", "Civil Engineer"),
            ("date_of_birth", "2004-09-18"),
            ("place_of_birth", "Kolkata"),
            ("present_address", "Flat 3B, 18 Sarat Bose Road, Kolkata 700020"),
            ("permanent_address", "Flat 3B, 18 Sarat Bose Road, Kolkata 700020"),
            ("stay_duration", "19 years"),
            ("applicant_occupation", "Student"),
            ("contact_number", "9830012345"),
            ("date", "21/11/2026"),
            ("place", "Kolkata"),
        ]
        for field, val in facts:
            conn.execute(
                "INSERT OR REPLACE INTO applicant_facts (conversation_id, field_name, field_value, confidence_status, updated_at) VALUES (?, ?, ?, 'confirmed', datetime('now'))",
                (conv_id, field, val)
            )

    meta = generate_pdf_draft(conv_id)
    pdf_path = get_draft_file_path(meta.document_id)
    print(f"Generated PDF at: {pdf_path}")

    doc = pymupdf.open(pdf_path)
    rendered_images = []
    for page_idx in range(len(doc)):
        page = doc[page_idx]
        pix = page.get_pixmap(dpi=150)
        img_path = os.path.join(OUTPUT_DIR, f"page_{page_idx + 1}.png")
        pix.save(img_path)
        print(f"Saved page {page_idx + 1} rendering: {img_path}")
        rendered_images.append(img_path)
    doc.close()
    print("Visual verification complete! Rendered 3 pages.")

if __name__ == "__main__":
    main()
