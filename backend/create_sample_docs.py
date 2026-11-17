import os

def create_pdf(filename: str, title: str, sections: list):
    """
    Creates a standard, valid PDF-1.4 file using pure Python (zero external dependencies).
    """
    objects = []
    
    def add_object(content: str) -> int:
        objects.append(content.encode('latin1'))
        return len(objects)

    # Prepare stream content for the page
    stream_lines = [
        "BT",
        "/F1 18 Tf",
        "50 780 Td",
        f"({title}) Tj",
        "/F1 10 Tf",
        "0 -25 Td",
        "(PRAWIRA TOBACCO ENTERPRISE INTERNAL DOCUMENTATION - VERSI RESMI 2026) Tj",
        "0 -30 Td"
    ]

    for heading, paragraphs in sections:
        stream_lines.append("/F1 14 Tf")
        stream_lines.append(f"({heading}) Tj")
        stream_lines.append("/F1 10 Tf")
        stream_lines.append("0 -18 Td")
        for para in paragraphs:
            # Simple text wrap
            clean_para = para.replace("(", "\(").replace(")", "\)")
            words = clean_para.split()
            current_line = []
            for w in words:
                current_line.append(w)
                if len(" ".join(current_line)) > 75:
                    stream_lines.append(f"({' '.join(current_line)}) Tj")
                    stream_lines.append("0 -14 Td")
                    current_line = []
            if current_line:
                stream_lines.append(f"({' '.join(current_line)}) Tj")
                stream_lines.append("0 -14 Td")
            stream_lines.append("0 -10 Td")
        stream_lines.append("0 -10 Td")

    stream_lines.append("ET")
    stream_content = "\n".join(stream_lines).encode('latin1')
    
    # 1. Catalog
    # 2. Pages
    # 3. Page 1
    # 4. Font F1
    # 5. Content Stream
    
    content_obj = f"5 0 obj\n<< /Length {len(stream_content)} >>\nstream\n".encode('latin1') + stream_content + b"\nendstream\nendobj\n"
    
    font_obj = b"4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
    
    page_obj = b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 842] /Contents 5 0 R /Resources << /Font << /F1 4 0 R >> >> >>\nendobj\n"
    
    pages_obj = b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
    
    catalog_obj = b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"

    all_objs = [catalog_obj, pages_obj, page_obj, font_obj, content_obj]

    # Calculate xref
    header = b"%PDF-1.4\n"
    output = bytearray(header)
    offsets = []

    for obj in all_objs:
        offsets.append(len(output))
        output.extend(obj)

    xref_offset = len(output)
    output.extend(b"xref\n0 6\n0000000000 65535 f \n")
    for off in offsets:
        output.extend(f"{off:010d} 00000 n \n".encode('latin1'))

    output.extend(f"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode('latin1'))

    os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
    with open(filename, "wb") as f:
        f.write(output)
    print(f"Generated: {filename} ({len(output)} bytes)")

def generate_samples():
    sample_dir = os.path.join(os.path.dirname(__file__), "..", "sample_documents")
    
    # 1. SOP Dokumen
    sop_path = os.path.join(sample_dir, "SOP_Penyimpanan_dan_Garansi_Prawira.pdf")
    create_pdf(
        filename=sop_path,
        title="SOP PENYIMPANAN DAN GARANSI PRODUK PRAWIRA TOBACCO",
        sections=[
            (
                "BAB 1: STANDAR OPERASIONAL PROSEDUR PENYIMPANAN TEMBAKAU",
                [
                    "Kadar kelembaban (relative humidity) optimal untuk menjaga cita rasa dan kualitas tembakau adalah 65 persen hingga 70 persen pada suhu ruang 20 hingga 25 derajat Celcius.",
                    "Tembakau wajib disimpan dalam wadah kedap udara (airtight container atau pouch kedap) untuk mencegah pengeringan daun tembakau dan hilangnya aroma cengkeh alami.",
                    "Gunakan Boveda Humidipak 69 persen atau clay humidifier disc yang telah direndam air matang selama 5 menit jika tembakau terasa mulai getas atau kering berlebih.",
                    "Hindari paparan sinar matahari langsung dan simpan pada rak penyimpanan gudang minimal 15 cm di atas lantai berubin."
                ]
            ),
            (
                "BAB 2: KEBIJAKAN GARANSI DAN PENGEMBALIAN BARANG (RETUR)",
                [
                    "Prawira Tobacco memberikan Garansi Kepuasan Pelanggan 100 persen penggantian varian baru atau pengembalian dana penuh.",
                    "Klaim garansi berlaku jika produk mengalami cacat kemasan bocor, berjamur, atau kemasan sobek saat diterima dengan melampirkan video unboxing utuh.",
                    "Batas waktu pengajuan klaim garansi retur maksimal adalah 2x24 jam sejak paket dinyatakan tiba oleh kurir ekspedisi.",
                    "Proses verifikasi garansi dapat diproses cepat melalui WhatsApp Layanan Pelanggan di nomor 083132001855."
                ]
            )
        ]
    )

    # 2. Katalog Varian (100% Produk Nyata dari Supabase Prawira Tobacco)
    catalog_path = os.path.join(sample_dir, "Katalog_Varian_Prawira_Tobacco.pdf")
    create_pdf(
        filename=catalog_path,
        title="KATALOG RESMI PRODUK PRAWIRA TOBACCO (SYNC SUPABASE)",
        sections=[
            (
                "BAGIAN 1: VARIAN TEMBAKAU RASA BUAH, MANIS DAN DINGIN (ICE)",
                [
                    "1. Linting Melon Ice (SKU: PT-0031): Tembakau linting dengan rasa buah melon manis segar berpadu sensasi dingin menthol sejuk. Harga Rp 25.000 per pack.",
                    "2. Linting Strawberry (SKU: PT-0032): Tembakau linting manis fruity segar khas buah strawberry pilihan alami. Harga Rp 25.000 per pack.",
                    "3. Linting Cappucino (SKU: PT-0030): Tembakau manis creamy legit dengan aroma kopi cappucino hangat. Harga Rp 25.000 per pack.",
                    "4. Purple Ice Burst (SKU: PT-0042): Tembakau rasa anggur berry segar dengan sensasi ice burst dingin menyegarkan. Harga Rp 22.000 per pack.",
                    "5. Coklat Ice Premium (SKU: PT-0041): Varian tembakau coklat manis legit berpadu sensasi dingin mint menthol. Harga Rp 22.000 per pack.",
                    "6. Barrack Whiskey Ice (SKU: PT-0002): Tembakau Barrack dengan rasa whiskey harum berpadu sensasi dingin menyegarkan. Harga Rp 22.000 per pack."
                ]
            ),
            (
                "BAGIAN 2: VARIAN TEMBAKAU KRETEK, MILD DAN PREMIUM",
                [
                    "7. Linting Surya (SKU: PT-0044): Tembakau cengkeh aroma madu tebal gurih mantap khas karakter Surya. Harga Rp 23.000 per pack.",
                    "8. Linting Samsu (SKU: PT-0033): Tembakau kretek mantap aroma klasik khas tingwe tradisional. Harga Rp 23.000 per pack.",
                    "9. Linting Marlong (SKU: PT-0034): Tembakau cita rasa American blend mantap khas karakter Marlboro. Harga Rp 23.000 per pack.",
                    "10. Linting Mild (SKU: PT-0029): Tembakau ringan tarikan halus dan bersih khas rokok mild. Harga Rp 23.000 per pack.",
                    "11. Sampurna Premium (SKU: PT-0037): Tembakau premium racikan halus aroma rempah wangi pilihan. Harga Rp 30.000 per pack.",
                    "12. Magnum Premium (SKU: PT-0038): Tembakau kretek premium dengan tarikan padat berbobot. Harga Rp 30.000 per pack.",
                    "13. Barrack Soju (SKU: PT-0007): Tembakau linting Golden Virginia 50 gram aroma halus istimewa. Harga Rp 45.000 per pack.",
                    "14. Barrack Bayote (SKU: PT-0001) dan Barrack Melisa (SKU: PT-0008): Tembakau rasa Bayote dan kemasan Drum Original 50 gram. Harga Rp 18.000 per pack."
                ]
            ),
            (
                "BAGIAN 3: AKSESORIS DAN PERLENGKAPAN LINTING RESMI",
                [
                    "15. Papir (SKU: PT-0050 & PT-0048): Kertas papir linting berkualitas untuk tembakau tingwe. Tersedia harga Rp 2.000 hingga Rp 5.000 per pack.",
                    "16. Busa Filter Besar dan Kecil (SKU: PT-0045 & PT-0046): Busa filter acetate untuk tarikan lebih bersih dan halus. Harga Rp 5.000 hingga Rp 10.000 per pack.",
                    "17. Cengkeh (SKU: PT-0047): Rajangan cengkeh alami penambah gurih dan aroma tembakau nusantara. Harga Rp 3.000 per pack.",
                    "18. Lem Papir (SKU: PT-0049): Lem khusus kertas papir aman dan daya rekat kuat. Harga Rp 3.000 per botol."
                ]
            )
        ]
    )

if __name__ == "__main__":
    generate_samples()
