from datetime import datetime, timedelta
import json
from pathlib import Path
import streamlit as st


def get_knowledge_path() -> Path:
    """Mencari lokasi strategy_cards.json secara dinamis dan aman."""
    candidates = [
        Path(__file__).resolve().parent.parent / "knowledge" / "strategy_cards.json",
        Path("knowledge/strategy_cards.json"),
        Path("SelarasBelajar-main/knowledge/strategy_cards.json"),
    ]
    for p in candidates:
        if p.exists():
            return p
    return candidates[0]


@st.cache_data
def load_strategy_cards() -> list[dict]:
    """Membaca knowledge/strategy_cards.json secara READ-ONLY."""
    path = get_knowledge_path()
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Gagal memuat kartu strategi dari {path}: {e}")
        return []


def format_duration(minutes: int) -> str:
    """Format menit menjadi jam dan menit yang ramah dibaca."""
    if minutes <= 0:
        return "0 menit"
    hours = minutes // 60
    remaining_minutes = minutes % 60
    if hours > 0 and remaining_minutes > 0:
        return f"{hours} jam {remaining_minutes} mnt"
    elif hours > 0:
        return f"{hours} jam"
    else:
        return f"{remaining_minutes} mnt"


def get_time_greeting() -> str:
    """Menghasilkan sapaan waktu sesuai jam lokal."""
    hour = datetime.now().hour
    if 4 <= hour < 11:
        return "Selamat Pagi"
    elif 11 <= hour < 15:
        return "Selamat Siang"
    elif 15 <= hour < 18:
        return "Selamat Sore"
    else:
        return "Selamat Malam"


def format_date_id(dt: datetime) -> str:
    """Format tanggal ke bahasa Indonesia ramah dibaca."""
    days = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
    months = [
        "Januari", "Februari", "Maret", "April", "Mei", "Juni",
        "Juli", "Agustus", "September", "Oktober", "November", "Desember"
    ]
    day_name = days[dt.weekday()]
    month_name = months[dt.month - 1]
    return f"{day_name}, {dt.day} {month_name} {dt.year}"


def format_datetime_short(dt: datetime) -> str:
    """Format tanggal dan jam ringkas."""
    months_short = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agt", "Sep", "Okt", "Nov", "Des"]
    return f"{dt.day} {months_short[dt.month - 1]} &bull; {dt.strftime('%H:%M')} WIB"


VARK_QUESTIONS = [
    {
        "id": 1,
        "question": "Ketika dosen memaparkan konsep teori baru yang abstrak di kelas, cara apa yang paling cepat membantumu menangkap alur logikanya?",
        "options": [
            ("Diagram skematis, bagan keterhubungan konsep, atau visual slide di proyektor.", "Visual"),
            ("Mendengarkan elaborasi lisan dosen, analogi verbal, serta sesi tanya-jawab kelas.", "Aural"),
            ("Membaca buku teks referensi, diktat resmi, atau handout catatan terstruktur.", "Read/Write"),
            ("Mencoba latihan soal konkret, studi kasus terapan, atau simulasi mandiri.", "Kinesthetic"),
        ],
    },
    {
        "id": 2,
        "question": "Saat sedang mempersiapkan diri menghadapi Ujian Tengah Semester (UTS), strategi belajar apa yang membuatmu paling siap?",
        "options": [
            ("Membuat ringkasan visual dengan peta pikiran (mind map) atau bagan komparasi berwarna.", "Visual"),
            ("Membahas materi bersama teman kelompok atau mengajar ulang topik kepada orang lain secara lisan.", "Aural"),
            ("Membaca kembali catatan kuliah dan menuliskan ulang poin-poin kunci dalam bentuk daftar.", "Read/Write"),
            ("Mengerjakan bank soal tahun-tahun sebelumnya dan mempraktikkan langkah pemecahan secara riil.", "Kinesthetic"),
        ],
    },
    {
        "id": 3,
        "question": "Ketika kamu mengerjakan tugas praktikum atau proyek pemrograman dan mengalami error/stuck, apa langkah pertamamu?",
        "options": [
            ("Menelusuri diagram arsitektur alur data atau menganalisis grafik visual pemanggilan modul.", "Visual"),
            ("Mengonsultasikan kendala tersebut dengan asisten praktikum atau berdiskusi dengan rekan setim.", "Aural"),
            ("Membaca dokumentasi teknis resmi (API docs), spesifikasi sistem, atau manual referensi.", "Read/Write"),
            ("Melakukan uji coba langsung (trial and error) dengan mengganti parameter secara terukur.", "Kinesthetic"),
        ],
    },
    {
        "id": 4,
        "question": "Jika kamu ditugaskan menyampaikan presentasi tugas akhir kelompok, format pendukung presentasi mana yang paling kamu sukai?",
        "options": [
            ("Slide presentasi dengan infografis terstruktur, tata letak visual bersih, dan minim paragraf.", "Visual"),
            ("Penyampaian lisan yang lugas dengan banyak ruang untuk tanya jawab dan diskusi interaktif.", "Aural"),
            ("Makalah naskah lengkap atau executive summary tertulis yang dibagikan kepada audiens.", "Read/Write"),
            ("Demonstrasi langsung prototipe fungsional atau simulasi perangkat secara live di hadapan audiens.", "Kinesthetic"),
        ],
    },
    {
        "id": 5,
        "question": "Saat kamu diminta menelaah jurnal ilmiah untuk tinjauan pustaka makalah, dari mana kamu mulai mencerna isinya?",
        "options": [
            ("Mencermati diagram model konseptual, gambar grafik hasil eksperimen, dan visualisasi data.", "Visual"),
            ("Mendengarkan rekaman bedah jurnal/webinar atau berdiskusi dengan kolega penelitian.", "Aural"),
            ("Membaca abstrak, pendahuluan, metodologi teks, dan membuat anotasi di margin halaman.", "Read/Write"),
            ("Menguji formula atau metode penelitian tersebut langsung ke dalam spreadsheet atau prototipe kode.", "Kinesthetic"),
        ],
    },
    {
        "id": 6,
        "question": "Dalam pengerjaan tugas proyek tim, kontribusi mana yang terasa paling sesuai dengan ritme kerjamu?",
        "options": [
            ("Merancang skema visual sistem, presentasi pitch desk, atau diagram arsitektur proyek.", "Visual"),
            ("Mengkoordinasikan ide, memoderasi rapat sinkronisasi, dan merumuskan konsensus tim.", "Aural"),
            ("Menyusun laporan akhir tertulis, merapikan kaidah bahasa ilmiah, dan menyusun sitasi.", "Read/Write"),
            ("Membangun prototipe kerja, menangani aspek operasional teknis, dan menguji kelayakan.", "Kinesthetic"),
        ],
    },
    {
        "id": 7,
        "question": "Ketika kamu mengingat kembali materi kuliah dari minggu sebelumnya, memori apa yang paling kuat bertahan?",
        "options": [
            ("Tata letak halaman slide, coretan bagan di papan tulis, atau grafik yang ditampilkan dosen.", "Visual"),
            ("Kalimat penekanan dosen, intonasi suara saat menjelaskan poin krusial, atau diskusi kelas.", "Aural"),
            ("Daftar istilah penting, kutipan definisi tertulis, dan catatan terstruktur yang kamu tulis.", "Read/Write"),
            ("Aktivitas praktik di laboratorium, gerakan saat demo materi, atau eksperimen langsung.", "Kinesthetic"),
        ],
    },
    {
        "id": 8,
        "question": "Bagaimana lingkungan belajar ideal yang paling membantumu fokus saat menyelesaikan tugas berbobot tinggi?",
        "options": [
            ("Ruang rapi dengan papan tulis kecil atau monitor sekunder untuk memetakan alur kerja secara visual.", "Visual"),
            ("Ruang dengan latar suara tenang atau memungkinkan berbisik menjelaskan materi kepada diri sendiri.", "Aural"),
            ("Meja hening dengan buku referensi, binder catatan rapi, dan minim distraksi visual.", "Read/Write"),
            ("Ruang yang memungkinkan bergerak santai di sela waktu belajar atau berdiri sejenak untuk memikirkan solusi.", "Kinesthetic"),
        ],
    },
]


def calculate_vark_scores(answers: dict[int, str]) -> tuple[dict[str, int], str]:
    """
    Menghitung skor distribusi VARK berdasarkan jawaban pengguna.
    Mengembalikan: (dict_skor, modalitas_dominan)
    """
    scores = {"Visual": 0, "Aural": 0, "Read/Write": 0, "Kinesthetic": 0}
    for q_id, modality in answers.items():
        if modality in scores:
            scores[modality] += 1

    dominant = max(scores, key=lambda k: scores[k])
    return scores, dominant


def init_session_state():
    """Inisialisasi seluruh st.session_state yang dibutuhkan UI."""
    now = datetime.now()
    today_base = datetime(now.year, now.month, now.day, 8, 0)

    # 1. State Profil Mahasiswa
    if "user" not in st.session_state:
        st.session_state.user = {
            "name": "Intan Citra Permatasari",
            "study_program": "Teknik Informatika",
            "semester": 5,
            "has_tested": True,
            "vark_scores": {"Visual": 5, "Aural": 3, "Read/Write": 4, "Kinesthetic": 2},
            "dominant_preference": "Visual",
            "max_block_minutes": 60,
        }

    # 2. State Navigasi
    if "current_page" not in st.session_state:
        st.session_state.current_page = "Dashboard"

    # 3. State Tugas (Data Awal Realistis Akademik)
    if "tasks" not in st.session_state:
        st.session_state.tasks = [
            {
                "id": 1,
                "nama": "Laporan Praktikum Kecerdasan Buatan: A* Search",
                "matkul": "Kecerdasan Buatan",
                "jenis": "laporan_praktikum",
                "bobot": 0.3,
                "estimasi_menit": 234,
                "tenggat": today_base + timedelta(days=2, hours=10),
                "status": "Sedang Dikerjakan",
            },
            {
                "id": 2,
                "nama": "Makalah Studi Kasus Normalisasi Basis Data Perbankan",
                "matkul": "Basis Data Lanjut",
                "jenis": "makalah",
                "bobot": 0.5,
                "estimasi_menit": 360,
                "tenggat": today_base + timedelta(days=4, hours=9),
                "status": "Belum Dimulai",
            },
            {
                "id": 3,
                "nama": "Rangkuman Modul 6 Kriptografi Kunci Publik RSA",
                "matkul": "Keamanan Informasi",
                "jenis": "rangkuman",
                "bobot": 0.2,
                "estimasi_menit": 108,
                "tenggat": today_base + timedelta(days=1, hours=8),
                "status": "Sedang Dikerjakan",
            },
            {
                "id": 4,
                "nama": "Slide Presentasi Arsitektur Clean Architecture",
                "matkul": "Rekayasa Perangkat Lunak",
                "jenis": "presentasi",
                "bobot": 0.2,
                "estimasi_menit": 180,
                "tenggat": today_base + timedelta(days=6, hours=2),
                "status": "Belum Dimulai",
            },
            {
                "id": 5,
                "nama": "Kuis Mandiri Struktur Data Tree & Heap",
                "matkul": "Struktur Data",
                "jenis": "kuis",
                "bobot": 0.0,
                "estimasi_menit": 60,
                "tenggat": today_base + timedelta(days=1, hours=2),
                "status": "Selesai",
            },
        ]

    # 4. State Slot Kosong (Free Slots Mahasiswa)
    if "free_slots" not in st.session_state:
        st.session_state.free_slots = [
            (today_base + timedelta(days=0, hours=6), today_base + timedelta(days=0, hours=9)),     # Hari ini 14:00 - 17:00 (180m)
            (today_base + timedelta(days=1, hours=1), today_base + timedelta(days=1, hours=4)),     # Besok 09:00 - 12:00 (180m)
            (today_base + timedelta(days=1, hours=6), today_base + timedelta(days=1, hours=9)),     # Besok 14:00 - 17:00 (180m)
            (today_base + timedelta(days=2, hours=1), today_base + timedelta(days=2, hours=4)),     # Lusa 09:00 - 12:00 (180m)
            (today_base + timedelta(days=2, hours=5), today_base + timedelta(days=2, hours=8)),     # Lusa 13:00 - 16:00 (180m)
        ]

    # 5. State Hasil Rencana Penjadwalan Terakhir
    if "current_plan" not in st.session_state:
        st.session_state.current_plan = None

    if "selected_task_id" not in st.session_state:
        st.session_state.selected_task_id = 1

    # 6. State AI Assistant (Chat History)
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            {
                "role": "assistant",
                "content": (
                    "Halo Intan! Saya **AI Selaras**, pendamping manajemen tugas dan ritme belajar akademikmu. "
                    "Saya dapat membantumu membedah beban tugas, merekomendasikan strategi studi berdasarkan preferensi "
                    "Visualmu, atau mengecek kecukupan waktu sebelum tenggat. "
                    "Ada tugas atau perencanaan yang ingin kamu konsultasikan hari ini?"
                ),
            }
        ]

    # 7. State Refleksi Mingguan
    if "reflections" not in st.session_state:
        st.session_state.reflections = [
            {
                "tanggal": "14 November 2026",
                "strategi_terbantu": "V01 - Mind Mapping",
                "hambatan": "Sering terdistraksi saat mengerjakan tugas yang durasinya melebihi 60 menit berturut-turut tanpa jeda.",
                "perbaikan": "Membatasi sesi pengerjaan tugas menjadi maksimal 45-60 menit menggunakan fitur penjadwalan blok otomatis.",
                "skor_kepuasan": 4,
            }
        ]
