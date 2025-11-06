import streamlit as st
import pandas as pd
from datetime import datetime
import os
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image as PILImage
import io

# Sayfa ayarları
st.set_page_config(
    page_title="Buldumlar Biber & Baharat - Fiyat Teklifi",
    page_icon="🌶️",
    layout="wide"
)

# CSS ile görünümü iyileştir
st.markdown("""
<style>
    .main-header {
        background-color: #2c1810;
        color: #dc3545;
        padding: 20px;
        text-align: center;
        border-radius: 10px;
        margin-bottom: 30px;
    }
    .stButton>button {
        background-color: #dc3545;
        color: white;
        border-radius: 5px;
        border: none;
        padding: 10px 20px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Türkçe font desteği
def setup_fonts():
    try:
        # Eğer fontları aynı klasöre koyduysan:
        normal_font_path = os.path.join(os.path.dirname(__file__), "DejaVuSans.ttf")
        bold_font_path = os.path.join(os.path.dirname(__file__), "DejaVuSans-Bold.ttf")

        # Eğer fonts klasörüne koyduysan, üsttekiler yerine şunu kullan:
        # normal_font_path = os.path.join(os.path.dirname(__file__), "fonts", "DejaVuSans.ttf")
        # bold_font_path   = os.path.join(os.path.dirname(__file__), "fonts", "DejaVuSans-Bold.ttf")

        pdfmetrics.registerFont(TTFont("DejaVuSans", normal_font_path))
        pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", bold_font_path))

        return "DejaVuSans", "DejaVuSans-Bold"

    except Exception as e:
        # Font yüklenemezse hata ver ama yine de PDF oluşsun
        st.warning(f"Türkçe font yüklenemedi: {e}. Standart font kullanılacak.")
        return "Helvetica", "Helvetica-Bold"


FONT_NORMAL, FONT_BOLD = setup_fonts()


# Başlık
st.markdown('<div class="main-header"><h1>🌶️ FİYAT TEKLİFİ OLUŞTURUCU</h1><p>Buldumlar Biber & Baharat Entegre Tesisleri</p></div>', unsafe_allow_html=True)

# Session state'de ürünler listesi
if 'products' not in st.session_state:
    st.session_state.products = []

if 'editing_index' not in st.session_state:
    st.session_state.editing_index = None

# Sidebar ile düzen
with st.sidebar:
    st.header("📋 İşlemler")
    
    if st.button("🗑️ Tüm Ürünleri Temizle"):
        if st.session_state.products:
            st.session_state.products.clear()
            st.session_state.editing_index = None
            st.success("Tüm ürünler silindi!")
        else:
            st.info("Zaten hiç ürün yok!")

# Ana içerik - 2 sütun
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("👥 Müşteri Bilgileri")
    customer_company = st.text_input("Müşteri Firma Adı", placeholder="Örnek: Saloon Burger")
    contact_person = st.text_input("İlgili Kişi", placeholder="Örnek: Mehmet Yılmaz")
    
    st.subheader("🛒 Ürün Ekle/Düzenle")
    
    # Düzenleme modunda mı kontrol et
        # Düzenleme / yeni ekleme için varsayılan değerler
    if st.session_state.editing_index is not None:
        editing_product = st.session_state.products[st.session_state.editing_index]
        default_name = editing_product['name']
        default_price = editing_product['unit_price']
        default_vat = editing_product['vat_rate']
        # Yeni eklenen alan: ambalaj kg
        default_package_kg = editing_product.get('package_kg', 0.0)
        button_text = "✏️ Ürünü Güncelle"
        button_color = "secondary"
    else:
        default_name = ""
        default_price = 0.0
        default_vat = 20.0
        default_package_kg = 0.0
        button_text = "➕ Ürün Ekle"
        button_color = "primary"
    
    # Ürün adı
    product_name = st.text_input("Ürün Adı", value=default_name, placeholder="Örnek: Karabiber")
    
    # KG fiyatı ve KDV
    col_price, col_vat = st.columns([2, 1])
    with col_price:
        unit_price = st.number_input(
            "Kilogram Fiyatı (KDV Hariç)",
            value=default_price,
            min_value=0.0,
            step=0.01
        )
    with col_vat:
        vat_rate = st.number_input(
            "KDV (%)",
            value=default_vat,
            min_value=0.0,
            max_value=100.0,
            step=1.0
        )
    
    # Ambalaj bilgisi (opsiyonel)
    package_kg = st.number_input(
        "Ambalaj (kg) - opsiyonel",
        value=default_package_kg,
        min_value=0.0,
        step=1.0,
        help="Sadece kilogram bazlı satılan ürünler için 0 bırakın. Örn: 5, 10, 20"
    )
    
    # Butonlar
    col_btn1, col_btn2 = st.columns([1, 1])
    
    with col_btn1:
        if st.button(button_text, type=button_color):
            if product_name.strip():
                # KG bazında KDV dahil fiyat
                vat_price = unit_price * (1 + vat_rate / 100)
                
                # Ambalaj fiyatı hesaplama
                if package_kg and package_kg > 0:
                    package_price_excl_vat = unit_price * package_kg
                    package_price_incl_vat = vat_price * package_kg
                else:
                    package_price_excl_vat = 0.0
                    package_price_incl_vat = 0.0
                
                # Ürün sözlüğü
                product = {
                    'name': product_name.strip(),
                    'unit_price': unit_price,
                    'vat_rate': vat_rate,
                    'vat_price': vat_price,
                    'package_kg': package_kg,
                    'package_price_excl_vat': package_price_excl_vat,
                    'package_price_incl_vat': package_price_incl_vat,
                }
                
                if st.session_state.editing_index is not None:
                    # Güncelleme
                    st.session_state.products[st.session_state.editing_index] = product
                    st.session_state.editing_index = None
                    st.success(f"'{product_name}' güncellendi!")
                    st.rerun()
                else:
                    # Yeni ekleme
                    st.session_state.products.append(product)
                    st.rerun()
            else:
                st.error("Ürün adı boş olamaz!")

    
    with col_btn2:
        if st.session_state.editing_index is not None:
            if st.button("❌ İptal"):
                st.session_state.editing_index = None
                st.rerun()

with col2:
    st.subheader("📦 Eklenen Ürünler")
    
    if st.session_state.products:
        # Ürünleri DataFrame olarak göster
        df_data = []
        for i, product in enumerate(st.session_state.products):
            package_kg = product.get('package_kg', 0.0) or 0.0
            if package_kg > 0:
                ambalaj_str = f"{package_kg:.0f} kg"
                pkg_excl = product.get(
                    'package_price_excl_vat',
                    product['unit_price'] * package_kg
                )
                pkg_incl = product.get(
                    'package_price_incl_vat',
                    product['vat_price'] * package_kg
                )
                pkg_excl_str = f"{pkg_excl:.2f}"
                pkg_incl_str = f"{pkg_incl:.2f}"
            else:
                ambalaj_str = ""
                pkg_excl_str = ""
                pkg_incl_str = ""
            
            df_data.append({
                'No': i + 1,
                'Ürün Adı': product['name'],
                'KG Fiyatı KDV Hariç (TL)': f"{product['unit_price']:.2f}",
                'KDV %': f"{product['vat_rate']:.0f}",
                'KG Fiyatı KDV Dahil (TL)': f"{product['vat_price']:.2f}",
                'Ambalaj (kg)': ambalaj_str,
                'Ambalaj Fiyatı KDV Hariç (TL)': pkg_excl_str,
                'Ambalaj Fiyatı KDV Dahil (TL)': pkg_incl_str,
            })
        
        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

        
        # Her ürün için düzenle/sil butonları
        st.write("**İşlemler:**")
        for i, product in enumerate(st.session_state.products):
            col_edit, col_delete, col_info = st.columns([1, 1, 3])
            
            with col_edit:
                if st.button(f"✏️", key=f"edit_{i}", help="Düzenle"):
                    st.session_state.editing_index = i
                    st.rerun()
            
            with col_delete:
                if st.button(f"🗑️", key=f"delete_{i}", help="Sil"):
                    st.session_state.products.pop(i)
                    if st.session_state.editing_index == i:
                        st.session_state.editing_index = None
                    elif st.session_state.editing_index is not None and st.session_state.editing_index > i:
                        st.session_state.editing_index -= 1
                    st.success(f"'{product['name']}' silindi!")
                    st.rerun()
            
            with col_info:
                st.write(f"{i+1}. {product['name']}")
        
        st.write(f"**Toplam: {len(st.session_state.products)} ürün**")
        
    else:
        st.info("Henüz ürün eklenmemiş. Soldan ürün bilgilerini doldurup 'Ürün Ekle' butonuna tıklayın.")

# PDF Oluşturma
st.divider()
st.subheader("📄 PDF Oluştur")

if st.session_state.products and customer_company.strip():
    if st.button("📋 PDF TEKLİFİ OLUŞTUR", type="primary", use_container_width=True):
        try:
            # PDF oluşturma fonksiyonları
            def find_logo_file():
                possible_names = ['logo.png', 'logo.jpg', 'logo.jpeg', 'Logo.png', 'LOGO.png']
                for name in possible_names:
                    if os.path.exists(name):
                        return name
                return None
            
            def create_watermark_logo():
                logo_file = find_logo_file()
                if not logo_file:
                    return None
                
                try:
                    with PILImage.open(logo_file) as original_img:
                        if original_img.mode != 'RGBA':
                            img = original_img.convert('RGBA')
                        else:
                            img = original_img.copy()
                        
                        max_size = 350
                        img.thumbnail((max_size, max_size), PILImage.Resampling.LANCZOS)
                        
                        canvas_size = 400
                        canvas = PILImage.new('RGBA', (canvas_size, canvas_size), (0, 0, 0, 0))
                        
                        x = (canvas_size - img.size[0]) // 2
                        y = (canvas_size - img.size[1]) // 2
                        canvas.paste(img, (x, y), img)
                        
                        pixels = canvas.load()
                        for i in range(canvas.size[0]):
                            for j in range(canvas.size[1]):
                                r, g, b, a = pixels[i, j]
                                pixels[i, j] = (r, g, b, int(a * 0.25))
                        
                        temp_logo_path = "temp_watermark.png"
                        canvas.save(temp_logo_path, 'PNG')
                        return temp_logo_path
                except:
                    return None
            
            # PDF oluştur
            filename = f"fiyat_teklifi_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
            doc = SimpleDocTemplate(filename, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm)
            story = []
            
            # PDF Stiller
            company_style = ParagraphStyle(
                'CompanyStyle',
                fontName=FONT_BOLD,
                fontSize=16,
                leading=20,  # <-- SATIR ARALIĞI (fontSize'tan büyük olsun)
                spaceAfter=25,
                alignment=TA_CENTER,
                textColor=colors.Color(0.86, 0.24, 0.26)
            )

            
            title_style = ParagraphStyle('TitleStyle', fontName=FONT_BOLD, fontSize=18,
                                        spaceAfter=20, alignment=TA_CENTER,
                                        textColor=colors.Color(0.86, 0.24, 0.26))
            
            left_style = ParagraphStyle('LeftStyle', fontName=FONT_NORMAL, fontSize=10,
                                       spaceAfter=4, alignment=TA_LEFT, leftIndent=0)
            
            heading_style = ParagraphStyle('HeadingStyle', fontName=FONT_BOLD, fontSize=12,
                                          spaceAfter=8, textColor=colors.Color(0.86, 0.24, 0.26))
            
            normal_style = ParagraphStyle('NormalStyle', fontName=FONT_NORMAL, fontSize=10, spaceAfter=6)
            
            # İçerik
            story.append(Paragraph("BULDUMLAR BİBER & BAHARAT<br/>ENTEGRE TESİSLERİ", company_style))
            story.append(Paragraph("FİYAT TEKLİFİ", title_style))
            story.append(Spacer(1, 15))
            
            today = datetime.now()
            story.append(Paragraph(f"<b>Tarih:</b> {today.strftime('%d/%m/%Y')}", left_style))
            story.append(Paragraph(f"<b>Teklif No:</b> BLD-{today.strftime('%Y%m%d')}-{today.strftime('%H%M')}", left_style))
            story.append(Spacer(1, 20))
            
            story.append(Paragraph("SAYIN", heading_style))
            customer_info = customer_company
            if contact_person.strip():
                customer_info += f"<br/>Att: {contact_person}"
            story.append(Paragraph(customer_info, normal_style))
            story.append(Spacer(1, 20))
            
            story.append(Paragraph("FİYAT LİSTESİ (KG ve Ambalaj Bazında)", heading_style))
            story.append(Spacer(1, 10))
            
            # Tablo başlıkları
            table_data = [
                [
                    'Ürün Adı',
                    'KG Fiyatı\n(KDV Hariç)',
                    'KDV %',
                    'KG Fiyatı\n(KDV Dahil)',
                    'Ambalaj',
                    'Ambalaj Fiyatı\n(KDV Dahil)'
                ]
            ]
            
            # Ürün satırları
            for product in st.session_state.products:
                package_kg = product.get('package_kg', 0.0) or 0.0
                if package_kg > 0:
                    ambalaj = f"{package_kg:.0f} kg"
                    pkg_incl = product.get(
                        'package_price_incl_vat',
                        product['vat_price'] * package_kg
                    )
                    pkg_incl_str = f"{pkg_incl:.2f} TL"
                else:
                    ambalaj = "-"
                    pkg_incl_str = "-"
                
                table_data.append([
                    product['name'],
                    f"{product['unit_price']:.2f} TL/kg",
                    f"%{product['vat_rate']:.0f}",
                    f"{product['vat_price']:.2f} TL/kg",
                    ambalaj,
                    pkg_incl_str
                ])
            
            # 6 kolon için genişlikleri yeniden ayarla
            product_table = Table(
                table_data,
                colWidths=[5*cm, 3*cm, 2*cm, 3*cm, 2.5*cm, 3*cm]
            )
            product_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.86, 0.24, 0.26)),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
                ('FONTNAME', (0, 1), (-1, -1), FONT_NORMAL),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.Color(1, 0.95, 0.95), colors.white]),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))

            product_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.86, 0.24, 0.26)),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
                ('FONTNAME', (0, 1), (-1, -1), FONT_NORMAL),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.Color(1, 0.95, 0.95), colors.white]),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            
            story.append(product_table)
            story.append(Spacer(1, 25))
            
            notes = """<b>NOTLAR:</b><br/>
            • Fiyatlar Türk Lirası cinsindendir.<br/>
            • Fiyatlar kilogram ve belirtilen ambalaj bazında verilmiştir.<br/>
            • Minimum sipariş miktarları için ayrıca bilgi verilecektir.<br/>
            • Teslim süresi sipariş onayından sonra belirlenecektir."""
            
            story.append(Paragraph(notes, normal_style))
            
            # Logo watermark
            def add_logo_watermark(canvas, doc):
                temp_logo_path = create_watermark_logo()
                if temp_logo_path and os.path.exists(temp_logo_path):
                    try:
                        page_width, page_height = A4
                        logo_size = 400
                        x = (page_width - logo_size) / 2
                        y = (page_height - logo_size) / 2
                        canvas.drawImage(temp_logo_path, x, y, width=logo_size, height=logo_size, 
                                       mask='auto', preserveAspectRatio=True)
                        os.remove(temp_logo_path)
                    except:
                        pass
            
            # PDF oluştur
            doc.build(story, onFirstPage=add_logo_watermark, onLaterPages=add_logo_watermark)
            
            # İndirme butonu
            with open(filename, "rb") as pdf_file:
                pdf_bytes = pdf_file.read()
            
            st.success("PDF başarıyla oluşturuldu!")
            st.download_button(
                label="📥 PDF'i İndir",
                data=pdf_bytes,
                file_name=filename,
                mime="application/pdf"
            )
            
            # Geçici dosyayı temizle
            if os.path.exists(filename):
                os.remove(filename)
                
        except Exception as e:
            st.error(f"PDF oluşturma hatası: {str(e)}")

else:
    if not st.session_state.products:
        st.warning("PDF oluşturmak için en az bir ürün ekleyin.")
    if not customer_company.strip():
        st.warning("PDF oluşturmak için müşteri firma adını girin.")





