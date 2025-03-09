import streamlit as st
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.probability import FreqDist
from string import punctuation
import nltk
import os
import PyPDF2
import io

# Set page configuration
st.set_page_config(
    page_title="Aplikasi Perangkum Teks & PDF",
    page_icon="📝",
    layout="wide"
)

# Initialize NLTK downloads
@st.cache_resource
def download_nltk_resources():
    try:
        nltk.download('punkt')
        nltk.download('stopwords')
    except Exception as e:
        st.error(f"Error downloading NLTK resources: {str(e)}")

download_nltk_resources()

# Custom Indonesian stopwords
INDONESIAN_STOPWORDS = {
    'yang', 'di', 'ke', 'dari', 'pada', 'dalam', 'untuk', 'dengan', 'dan', 'atau',
    'ini', 'itu', 'juga', 'sudah', 'saya', 'anda', 'dia', 'mereka', 'kita', 'akan',
    'bisa', 'ada', 'tidak', 'saat', 'oleh', 'setelah', 'tentang', 'seperti', 'ketika',
    'bagi', 'sampai', 'karena', 'jika', 'namun', 'serta', 'dapat', 'apabila', 'melalui',
    'lain', 'sebuah', 'para', 'tetap', 'hingga', 'hal', 'tersebut', 'sebagai', 'masih',
    'telah', 'antara', 'begitu', 'setiap', 'sambil', 'yakni', 'menurut', 'hampir',
    'dimana', 'bagaimana', 'selama', 'siapa'
}

def extract_text_from_pdf(pdf_file):
    """Mengekstrak teks dari file PDF."""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        st.error(f"Error membaca PDF: {str(e)}")
        return None

def preprocess_text(text):
    """Membersihkan dan memproses teks sebelum dirangkum."""
    text = ''.join([char for char in text if char not in punctuation])
    text = text.lower()
    return text

def summarize_text(text, n_sentences=3):
    """Fungsi untuk merangkum teks dengan pembobotan kalimat."""
    if not text.strip():
        return ""
    
    cleaned_text = preprocess_text(text)
    sentences = sent_tokenize(text)
    if not sentences:
        return ""
    
    words = word_tokenize(cleaned_text)
    stop_words = INDONESIAN_STOPWORDS.union(set(punctuation))
    words = [word for word in words if word.lower() not in stop_words]
    
    freq_dist = FreqDist(words)
    
    sentence_scores = {}
    for sentence in sentences:
        if len(sentence.split()) <= 3:
            continue
        
        score = 0
        words_in_sentence = word_tokenize(preprocess_text(sentence))
        for word in words_in_sentence:
            if word in freq_dist:
                score += freq_dist[word]
        sentence_scores[sentence] = score / max(len(words_in_sentence), 1)
    
    n = min(n_sentences, len(sentence_scores))
    summary_sentences = sorted(sentence_scores.items(), key=lambda x: x[1], reverse=True)[:n]
    summary_sentences = [s[0] for s in summary_sentences]
    summary_sentences.sort(key=lambda x: sentences.index(x))
    
    return " ".join(summary_sentences)

def save_summary(summary, filename, format="txt"):
    """Menyimpan ringkasan ke file."""
    try:
        if format == "txt":
            with open(filename, "w", encoding="utf-8") as file:
                file.write(summary)
        elif format == "pdf":
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            
            c = canvas.Canvas(filename, pagesize=letter)
            width, height = letter
            
            # Membagi teks menjadi baris-baris
            words = summary.split()
            lines = []
            current_line = []
            
            for word in words:
                current_line.append(word)
                if len(' '.join(current_line)) > 70:  # Batasan lebar teks
                    lines.append(' '.join(current_line[:-1]))
                    current_line = [word]
            
            if current_line:
                lines.append(' '.join(current_line))
            
            # Menulis teks ke PDF
            y = height - 50
            c.setFont("Helvetica", 12)
            c.drawString(50, height - 30, "Hasil Ringkasan:")
            
            for line in lines:
                if y < 50:  # Jika mencapai batas bawah halaman
                    c.showPage()
                    y = height - 50
                    c.setFont("Helvetica", 12)
                
                c.drawString(50, y, line)
                y -= 15
            
            c.save()
        
        return True
    except Exception as e:
        st.error(f"Error menyimpan file: {str(e)}")
        return False

def main():
    st.title("📝 Aplikasi Perangkuman Teks & PDF")
    
    # Sidebar untuk konfigurasi
    with st.sidebar:
        st.header("Pengaturan")
        num_sentences = st.slider(
            "Jumlah kalimat ringkasan:",
            min_value=1,
            max_value=10,
            value=3,
            help="Pilih jumlah kalimat yang diinginkan dalam ringkasan"
        )
        save_format = st.selectbox(
            "Format penyimpanan:",
            ["txt", "pdf"],
            help="Pilih format file untuk menyimpan ringkasan"
        )
    
    # Tab untuk memilih metode input
    tab1, tab2 = st.tabs(["Input Teks", "Upload PDF"])
    
    with tab1:
        input_text = st.text_area(
            "Tempel atau ketik teks di sini:",
            height=200,
            help="Masukkan teks yang ingin diringkas"
        )
        
        if st.button("🔍 Ringkas Teks", key="summarize_text"):
            if input_text.strip():
                with st.spinner("Sedang merangkum..."):
                    summary = summarize_text(input_text, n_sentences=num_sentences)
                    st.session_state['current_summary'] = summary
                    st.subheader("Hasil Ringkasan:")
                    st.write(summary)
    
    with tab2:
        uploaded_file = st.file_uploader("Pilih file PDF", type="pdf")
        
        if uploaded_file is not None:
            if st.button("🔍 Ringkas PDF", key="summarize_pdf"):
                with st.spinner("Sedang membaca dan merangkum PDF..."):
                    pdf_text = extract_text_from_pdf(uploaded_file)
                    if pdf_text:
                        summary = summarize_text(pdf_text, n_sentences=num_sentences)
                        st.session_state['current_summary'] = summary
                        st.subheader("Hasil Ringkasan:")
                        st.write(summary)
    
    # Tombol untuk menyimpan ringkasan
    if 'current_summary' in st.session_state and st.session_state['current_summary']:
        col1, col2 = st.columns([2, 1])
        with col1:
            save_filename = st.text_input(
                "Nama file untuk disimpan:",
                f"ringkasan.{save_format}"
            )
        with col2:
            if st.button("💾 Simpan Ringkasan", use_container_width=True):
                if save_summary(st.session_state['current_summary'], save_filename, save_format):
                    st.success(f"✅ Ringkasan berhasil disimpan ke {save_filename}!")

if __name__ == "__main__":
    main()