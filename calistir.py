import streamlit as st
import pandas as pd
import sqlite3
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Türkçe karakterleri İngilizce'ye çevirme fonksiyonu
def turkish_to_english(text):
    replacements = {
        'ç': 'c', 'Ç': 'C', 'ğ': 'g', 'Ğ': 'G',
        'ı': 'i', 'İ': 'I', 'ö': 'o', 'Ö': 'O',
        'ş': 's', 'Ş': 'S', 'ü': 'u', 'Ü': 'U'
    }
    for tr_char, en_char in replacements.items():
        text = text.replace(tr_char, en_char)
    return text

# Veritabanı bağlantısı fonksiyonu
def get_db_connection():
    conn = sqlite3.connect('deprem_ihbar.db')
    return conn

# Tablo oluşturma fonksiyonu
def create_table():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS ihbarlar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ad TEXT,
            soyad TEXT,
            adres TEXT,
            telefon TEXT,
            il TEXT,
            ilce TEXT
        )
    ''')
    conn.commit()
    conn.close()

# PDF oluşturma fonksiyonu
def create_pdf(df):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Başlık
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, height - 50, "Deprem İhbar Raporu")

    # İçerik
    c.setFont("Helvetica", 10)
    y_position = height - 80

    for index, row in df.iterrows():
        line = (f"Ad: {row['ad']}, Soyad: {row['soyad']}, Adres: {row['adres']}, "
                f"Telefon: {row['telefon']}, İl: {row['il']}, İlçe: {row['ilce']}, "
                f"Tekrar Sayısı: {row['Tekrar Sayısı']}")  # Düzeltildi
        c.drawString(100, y_position, line)
        y_position -= 20
        if y_position < 100:
            c.showPage()
            c.setFont("Helvetica", 10)
            y_position = height - 50

    c.save()
    buffer.seek(0)
    return buffer

# Sayfa başlığını ve giriş metnini ayarlayın
st.title("Deprem İhbar Kaydı Sistemi")
st.write("Kullanıcı bilgilerini girerek ihbar kaydı oluşturabilirsiniz.")

# Tabloyu oluştur
create_table()

# Kullanıcıdan giriş al
ad = turkish_to_english(st.text_input("Ad", placeholder="Adınızı giriniz"))
soyad = turkish_to_english(st.text_input("Soyad", placeholder="Soyadınızı giriniz"))
adres = turkish_to_english(st.text_input("Adres", placeholder="Adresinizi giriniz"))
telefon = turkish_to_english(st.text_input("Telefon", placeholder="Telefon numaranızı giriniz"))
il = turkish_to_english(st.text_input("İl", placeholder="Bulunduğunuz ili giriniz"))
ilce = turkish_to_english(st.text_input("İlçe", placeholder="Bulunduğunuz ilçeyi giriniz"))

# Veriyi ekle
if st.button("Kaydı Oluştur"):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO ihbarlar (ad, soyad, adres, telefon, il, ilce)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (ad, soyad, adres, telefon, il, ilce))
    conn.commit()
    conn.close()
    st.success("İhbar kaydı başarıyla oluşturuldu!")

# Kayıtları görüntüle
conn = get_db_connection()
ihbarlar = pd.read_sql_query("SELECT * FROM ihbarlar", conn)
conn.close()

# Toplam ihbar sayısını göster
st.write(f"Toplam ihbar sayısı: {len(ihbarlar)}")

# Adreslerin tekrarlama sayısını hesapla ve yeni bir sütun olarak ekle
ihbarlar['Tekrar Sayısı'] = ihbarlar.groupby('adres')['adres'].transform('count')  # Düzeltildi

# Aynı adreslerin olup olmadığını kontrol et ve renklendir
def highlight_duplicates(row):
    return ['background-color: yellow' if row['Tekrar Sayısı'] > 1 else '' for _ in row]

st.dataframe(ihbarlar.style.apply(highlight_duplicates, axis=1))

# PDF Raporu İndirme
if st.button("PDF Raporu İndir"):
    pdf_buffer = create_pdf(ihbarlar)
    st.download_button(
        label="PDF Raporu İndir",
        data=pdf_buffer,
        file_name="ihbar_raporu.pdf",
        mime="application/pdf"
    )
