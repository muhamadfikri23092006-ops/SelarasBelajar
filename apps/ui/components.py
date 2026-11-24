from datetime import datetime, timedelta, time
import streamlit as st

from services.tools.effort import estimate_effort, MENIT_DASAR
from services.tools.capacity import check_capacity
from services.tools.scheduler import schedule_blocks, hitung_menit_tersedia
from services.verifier.schedule_check import verify_schedule
from services.agent.planner import plan_task

from apps.ui.data import (
    load_strategy_cards,
    format_duration,
    get_time_greeting,
    format_date_id,
    format_datetime_short,
    VARK_QUESTIONS,
    calculate_vark_scores,
)


def inject_custom_css():
    """
    Menyuntikkan design system editorial academic:
    - Palet: Warm ivory, soft beige, deep navy, charcoal, dan muted teal aksen.
    - Typography yang tajam, konsisten, dan berkarakter akademik.
    - Whitespace lega, kartu rounded dengan border tipis dan bayangan halus.
    - Menghilangkan bullet radio bawaan Streamlit.
    """
    st.markdown(
        """
        <style>
        /* ==========================================
           1. RESET & WARNA DASAR (EDITORIAL PALETTE)
           ========================================== */
        :root {
            --bg-canvas: #FAF9F5;
            --bg-surface: #FFFFFF;
            --bg-sidebar: #F2EFE9;
            --bg-subtle: #F6F4EE;
            --border-soft: #E6E3DB;
            --border-medium: #D6D2C4;
            --text-primary: #181D20;
            --text-secondary: #58626E;
            --text-muted: #8B95A0;
            --accent-teal: #18524B;
            --accent-teal-hover: #123F39;
            --accent-teal-subtle: #EDF5F4;
            --accent-navy: #1B2D45;
        }

        html, body, [class*="css"] {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            color: #181D20;
            background-color: #FAF9F5;
        }

        [data-testid="stAppViewContainer"] {
            background-color: #FAF9F5 !important;
        }

        /* Layout Container Tengah */
        .main .block-container {
            max-width: 1140px;
            padding-top: 2rem;
            padding-bottom: 4rem;
            padding-left: 2.5rem;
            padding-right: 2.5rem;
        }

        /* ==========================================
           2. SIDEBAR BESPOKE & NAVIGASI
           ========================================== */
        [data-testid="stSidebar"] {
            background-color: #F2EFE9 !important;
            border-right: 1px solid #E6E3DB !important;
        }

        /* Tombol Navigasi di Sidebar (Kustom Full-Width) */
        [data-testid="stSidebar"] .stButton > button {
            display: flex !important;
            justify-content: flex-start !important;
            text-align: left !important;
            padding: 0.55rem 0.85rem !important;
            border-radius: 8px !important;
            font-size: 0.875rem !important;
            gap: 10px !important;
            margin-bottom: 3px !important;
            width: 100% !important;
            border: 1px solid transparent !important;
            background-color: transparent !important;
            color: #4A5568 !important;
            transition: all 0.15s ease-in-out !important;
        }

        [data-testid="stSidebar"] .stButton > button p {
            font-size: 0.875rem !important;
            margin: 0 !important;
            text-align: left !important;
        }

        [data-testid="stSidebar"] .stButton > button:hover {
            background-color: #E8E4DA !important;
            color: #181D20 !important;
            border: 1px solid #DDD8CD !important;
        }

        /* State Navigasi Aktif */
        [data-testid="stSidebar"] .stButton > button[kind="primary"] {
            background-color: #FFFFFF !important;
            color: #18524B !important;
            border: 1px solid #D6D2C4 !important;
            border-left: 4px solid #18524B !important;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04) !important;
            font-weight: 600 !important;
        }

        [data-testid="stSidebar"] .stButton > button[kind="primary"] p {
            color: #18524B !important;
            font-weight: 600 !important;
        }

        /* Section Header di Sidebar */
        .sidebar-section-title {
            font-size: 0.685rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #8C95A0;
            margin: 1.15rem 0 0.35rem 0.4rem;
        }

        /* ==========================================
           3. KARTU & VISUAL CONTAINER
           ========================================== */
        .editorial-card {
            background-color: #FFFFFF;
            border: 1px solid #E6E3DB;
            border-radius: 12px;
            padding: 1.35rem 1.6rem;
            margin-bottom: 1.15rem;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02), 0 4px 14px rgba(0, 0, 0, 0.015);
            transition: border-color 0.15s ease;
        }

        .editorial-card-highlight {
            border-left: 4px solid #18524B;
        }

        .editorial-card-warning {
            border-left: 4px solid #D9822B;
        }

        .editorial-card:hover {
            border-color: #D6D2C4;
        }

        /* Header Subtitle Akademik */
        .editorial-header-title {
            font-size: 1.85rem;
            font-weight: 700;
            color: #181D20;
            letter-spacing: -0.02em;
            margin-bottom: 0.25rem;
        }

        .editorial-header-sub {
            font-size: 0.95rem;
            color: #58626E;
            margin-bottom: 1.65rem;
            line-height: 1.5;
        }

        /* ==========================================
           4. BADGE STATUS & PILLS
           ========================================== */
        .academic-pill {
            display: inline-block;
            padding: 0.22rem 0.6rem;
            font-size: 0.725rem;
            font-weight: 600;
            border-radius: 5px;
            letter-spacing: 0.03em;
            text-transform: uppercase;
        }

        .pill-selesai {
            background-color: #EDF7EE;
            color: #1B6122;
            border: 1px solid #C5E5C7;
        }

        .pill-progress {
            background-color: #FFF9E6;
            color: #9C6300;
            border: 1px solid #FFE494;
        }

        .pill-pending {
            background-color: #F3F2EE;
            color: #58626E;
            border: 1px solid #DDD9D0;
        }

        .pill-late {
            background-color: #FDF1F0;
            color: #A83228;
            border: 1px solid #F8C6C1;
        }

        .pill-tag {
            background-color: #EDF5F4;
            color: #18524B;
            border: 1px solid #D0E5E3;
            font-size: 0.725rem;
            font-weight: 600;
            border-radius: 4px;
            padding: 0.15rem 0.5rem;
        }

        /* Kotak Catatan / Disclaimer Akademik */
        .academic-notice {
            background-color: #F6F4EE;
            border-left: 3px solid #18524B;
            padding: 0.85rem 1.15rem;
            border-radius: 0 8px 8px 0;
            font-size: 0.875rem;
            color: #38424D;
            margin-bottom: 1.35rem;
            line-height: 1.55;
            border-top: 1px solid #EBE8E0;
            border-right: 1px solid #EBE8E0;
            border-bottom: 1px solid #EBE8E0;
        }

        /* ==========================================
           5. METRICS BESPOKE
           ========================================== */
        .metric-card {
            background-color: #FFFFFF;
            border: 1px solid #E6E3DB;
            border-radius: 10px;
            padding: 1.15rem 1.25rem;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
            height: 100%;
        }

        .metric-label {
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: #7A8490;
            margin-bottom: 0.35rem;
        }

        .metric-val {
            font-size: 1.65rem;
            font-weight: 700;
            color: #181D20;
            letter-spacing: -0.02em;
            line-height: 1.2;
            margin-bottom: 0.3rem;
            white-space: nowrap;
            overflow: visible;
        }

        .metric-delta {
            font-size: 0.8rem;
            color: #58626E;
            font-weight: 500;
        }

        /* ==========================================
           6. TIME-BLOCK TIMELINE ITEM
           ========================================== */
        .time-block-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0.75rem 1rem;
            background: #FFFFFF;
            border: 1px solid #E8E5DD;
            border-left: 3.5px solid #18524B;
            border-radius: 0 8px 8px 0;
            margin-bottom: 0.55rem;
            transition: all 0.15s ease;
        }

        .time-block-row:hover {
            border-color: #D6D2C4;
            background: #FCFBF9;
        }

        /* Streamlit Button Tweaks (Canvas) */
        .stButton > button {
            border-radius: 8px !important;
            font-weight: 500 !important;
            font-size: 0.875rem !important;
            border: 1px solid #D6D2C4 !important;
            background-color: #FFFFFF !important;
            color: #2D3748 !important;
        }

        .stButton > button:hover {
            background-color: #F6F4EE !important;
            border-color: #BAB4A5 !important;
            color: #181D20 !important;
        }

        .stButton > button[kind="primary"] {
            background-color: #18524B !important;
            color: #FFFFFF !important;
            border: 1px solid #14443E !important;
            box-shadow: 0 1px 3px rgba(24, 82, 75, 0.2) !important;
            font-weight: 600 !important;
        }

        .stButton > button[kind="primary"]:hover {
            background-color: #123F39 !important;
            border-color: #0E322D !important;
        }

        /* Streamlit Tabs Custom Styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 10px !important;
            border-bottom: 1px solid #E6E3DB !important;
            background-color: transparent !important;
            padding-bottom: 2px !important;
        }

        .stTabs [data-baseweb="tab"] {
            border-radius: 6px 6px 0 0 !important;
            padding: 8px 16px !important;
            font-size: 0.88rem !important;
            font-weight: 500 !important;
            color: #718096 !important;
            background: transparent !important;
            border: none !important;
        }

        .stTabs [aria-selected="true"] {
            color: #18524B !important;
            font-weight: 600 !important;
            border-bottom: 2.5px solid #18524B !important;
        }

        /* Form Inputs */
        .stTextInput > div > div > input,
        .stSelectbox > div > div,
        .stTextArea > div > div > textarea {
            border-radius: 8px !important;
            border: 1px solid #D6D2C4 !important;
            background-color: #FFFFFF !important;
            color: #181D20 !important;
            font-size: 0.9rem !important;
        }

        .stTextInput > div > div > input:focus,
        .stSelectbox > div > div:focus,
        .stTextArea > div > div > textarea:focus {
            border-color: #18524B !important;
            box-shadow: 0 0 0 1px #18524B !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ==========================================
# 1. LANDING PAGE
# ==========================================
def render_landing():
    st.markdown("<div class='editorial-header-title'>SelarasBelajar.Lab</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='editorial-header-sub'>Sistem Manajemen Tugas Kuliah Berdasarkan Preferensi Belajar & Algoritma Penjadwalan Terverifikasi</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class='editorial-card' style='padding: 2rem 2.25rem; border-top: 4px solid #18524B;'>
            <div style='font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: #18524B; margin-bottom: 0.5rem;'>
                Inisiatif Manajemen Belajar Mandiri
            </div>
            <h2 style='margin-top: 0; color: #181D20; font-size: 1.65rem; font-weight: 700; letter-spacing: -0.02em;'>
                Menyelaraskan ritme belajar, beban tugas kuliah, dan kapasitas waktu nyata secara presisi.
            </h2>
            <p style='color: #58626E; font-size: 0.98rem; line-height: 1.65; margin-bottom: 0;'>
                SelarasBelajar.Lab menggabungkan pemetaan modalitas belajar dinamis (VARK) dengan algoritma kalkulasi 
                effort terstandarisasi. Aplikasi ini membantu mahasiswa mengalokasikan sesi pengerjaan tugas secara realistis 
                tanpa rasa kelelahan akademik (burnout).
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            """
            <div class='editorial-card' style='height: 100%;'>
                <div style='font-size: 1.25rem; margin-bottom: 0.75rem; color: #18524B; font-weight: 700;'>01</div>
                <h4 style='color: #181D20; margin-top: 0; margin-bottom: 0.5rem;'>Preferensi Dinamis</h4>
                <p style='font-size: 0.875rem; color: #58626E; line-height: 1.55; margin: 0;'>
                    Modalitas VARK diposisikan sebagai preferensi cara belajar saat ini yang fleksibel, 
                    bukan penentu kecerdasan atau label kemampuan permanen.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            """
            <div class='editorial-card' style='height: 100%;'>
                <div style='font-size: 1.25rem; margin-bottom: 0.75rem; color: #18524B; font-weight: 700;'>02</div>
                <h4 style='color: #181D20; margin-top: 0; margin-bottom: 0.5rem;'>Estimasi Terstandar</h4>
                <p style='font-size: 0.875rem; color: #58626E; line-height: 1.55; margin: 0;'>
                    Menghitung durasi pengerjaan tugas secara objektif berbasis menit dasar (MENIT_DASAR) 
                    dan koefisien bobot kesulitan tugas.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            """
            <div class='editorial-card' style='height: 100%;'>
                <div style='font-size: 1.25rem; margin-bottom: 0.75rem; color: #18524B; font-weight: 700;'>03</div>
                <h4 style='color: #181D20; margin-top: 0; margin-bottom: 0.5rem;'>Jadwal Terverifikasi</h4>
                <p style='font-size: 0.875rem; color: #58626E; line-height: 1.55; margin: 0;'>
                    Modul verifier otomatis memvalidasi jadwal terhadap 5 aturan keras: batas blok waktu, 
                    kepatuhan tenggat, dan ketiadaan bentrok waktu.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    cta_col1, cta_col2, _ = st.columns([1.2, 1.2, 2.0])
    with cta_col1:
        if st.button("Mulai Pemetaan Preferensi", type="primary", use_container_width=True):
            st.session_state.current_page = "Tes Preferensi"
            st.rerun()
    with cta_col2:
        if st.button("Buka Dashboard Mahasiswa", use_container_width=True):
            st.session_state.current_page = "Dashboard"
            st.rerun()


# ==========================================
# 2. TES PREFERENSI BELAJAR
# ==========================================
def render_test_vark():
    st.markdown("<div class='editorial-header-title'>Tes Preferensi Belajar (VARK)</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='editorial-header-sub'>Kuesioner refleksi untuk memetakan kecenderungan cara menyerap dan mengolah materi kuliahmu saat ini.</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class='academic-notice'>
            <strong>Pernyataan Instrumen Akademik:</strong> Kuesioner ini merupakan instrumen alternatif untuk memetakan preferensi belajar 
            dan belum tervalidasi secara ilmiah. Hasilnya menggambarkan kecenderungan saat ini dan dapat berkembang 
            seiring perubahan mata kuliah, materi ajar, dan pengalaman belajarmu.
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("form_vark_redesign"):
        answers = {}
        for idx, item in enumerate(VARK_QUESTIONS):
            st.markdown(
                f"""
                <div style='font-size: 0.95rem; font-weight: 600; color: #181D20; margin-bottom: 0.5rem;'>
                    {idx + 1}. {item['question']}
                </div>
                """,
                unsafe_allow_html=True,
            )
            choice_labels = [opt[0] for opt in item["options"]]
            selected_label = st.radio(
                label=f"Pilihan {idx + 1}",
                options=choice_labels,
                index=0,
                key=f"q_{item['id']}",
                label_visibility="collapsed",
            )
            for label, modality in item["options"]:
                if label == selected_label:
                    answers[item["id"]] = modality
                    break
            st.markdown("<div style='height: 1px; background: #EAE7DF; margin: 1.15rem 0 1.35rem 0;'></div>", unsafe_allow_html=True)

        submitted = st.form_submit_button("Hitung & Simpan Preferensi Belajar", type="primary")
        if submitted:
            scores, dominant = calculate_vark_scores(answers)
            st.session_state.user["vark_scores"] = scores
            st.session_state.user["dominant_preference"] = dominant
            st.session_state.user["has_tested"] = True
            st.session_state.current_page = "Hasil Preferensi"
            st.rerun()


# ==========================================
# 3. HASIL PREFERENSI
# ==========================================
def render_result_vark():
    st.markdown("<div class='editorial-header-title'>Profil Preferensi Belajar Anda</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='editorial-header-sub'>Distribusi modalitas belajar berdasarkan instrumen refleksi terkini.</div>",
        unsafe_allow_html=True,
    )

    user = st.session_state.user
    scores = user.get("vark_scores", {"Visual": 0, "Aural": 0, "Read/Write": 0, "Kinesthetic": 0})
    dominant = user.get("dominant_preference", "Visual")
    total_answers = max(sum(scores.values()), 1)

    st.markdown(
        f"""
        <div class='editorial-card editorial-card-highlight' style='padding: 1.75rem 2rem;'>
            <div style='font-size: 0.75rem; color: #18524B; text-transform: uppercase; font-weight: 700; letter-spacing: 0.08em; margin-bottom: 0.35rem;'>
                Hasil Kecenderungan Dominan
            </div>
            <div style='font-size: 1.65rem; font-weight: 700; color: #181D20; margin-bottom: 0.5rem;'>
                Preferensi {dominant} kamu saat ini lebih dominan.
            </div>
            <p style='color: #58626E; font-size: 0.95rem; line-height: 1.6; margin: 0;'>
                Kamu cenderung lebih nyaman dan efisien menyerap konsep abstrak melalui representasi dan sarana <strong>{dominant.lower()}</strong>. 
                Gunakan kecenderungan ini untuk memilih strategi studi yang selaras dengan mata kuliah aktifmu.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class='academic-notice'>
            <strong>Pernyataan Etis:</strong> Hasil ini menggambarkan preferensi belajar saat ini dan digunakan sebagai 
            salah satu pertimbangan dalam memberikan rekomendasi strategi belajar. Hasil ini bukan label kemampuan 
            atau batasan cara belajar.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div style='font-size: 1.15rem; font-weight: 700; color: #181D20; margin-bottom: 0.85rem;'>Breakdown Distribusi Modalitas</div>", unsafe_allow_html=True)
    cols = st.columns(4)
    aspects = [
        ("Visual", scores.get("Visual", 0), "Bagan, mind map, diagram alir"),
        ("Aural / Auditori", scores.get("Aural", 0), "Diskusi lisan, analogi verbal"),
        ("Read / Write", scores.get("Read/Write", 0), "Catatan teks, sintesis literatur"),
        ("Kinestetik", scores.get("Kinesthetic", 0), "Simulasi nyata, studi kasus terapan"),
    ]

    for col, (name, val, desc) in zip(cols, aspects):
        with col:
            pct = int((val / total_answers) * 100)
            st.markdown(
                f"""
                <div class='metric-card'>
                    <div class='metric-label'>{name}</div>
                    <div class='metric-val'>{val} <span style='font-size: 1rem; font-weight: 500; color: #58626E;'>poin</span></div>
                    <div class='metric-delta'>{pct}% dari total refleksi</div>
                    <div style='font-size: 0.775rem; color: #8B95A0; margin-top: 0.4rem;'>{desc}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.progress(val / total_answers)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<div style='font-size: 1.15rem; font-weight: 700; color: #181D20; margin-bottom: 0.85rem;'>Rekomendasi Strategi Awal untuk Dieksplorasi</div>", unsafe_allow_html=True)
    cards = load_strategy_cards()
    recommended_cards = [c for c in cards if dominant.lower() in c.get("modality", "").lower()][:2]

    card_cols = st.columns(len(recommended_cards) if recommended_cards else 1)
    for col, c in zip(card_cols, recommended_cards):
        with col:
            st.markdown(
                f"""
                <div class='editorial-card'>
                    <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;'>
                        <span class='academic-pill pill-tag'>{c.get('id', '')} &bull; {c.get('modality', '')}</span>
                        <span class='academic-pill pill-selesai'>Disarankan</span>
                    </div>
                    <h4 style='margin: 0.25rem 0 0.5rem 0; color: #181D20;'>{c.get('strategy_name', '')}</h4>
                    <p style='font-size: 0.875rem; color: #58626E; line-height: 1.5; margin-bottom: 0.75rem;'>{c.get('description', '')}</p>
                    <div style='background: #F6F4EE; padding: 0.6rem 0.85rem; border-radius: 6px; font-size: 0.825rem; color: #38424D;'>
                        <strong>Contoh kuliah:</strong> {c.get('example_for_college_task', '-')}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)
    b1, b2, b3 = st.columns([1.2, 1.2, 1.2])
    with b1:
        if st.button("Katalog Strategi Lengkap", type="primary", use_container_width=True):
            st.session_state.current_page = "Strategi"
            st.rerun()
    with b2:
        if st.button("Lihat Tugas & Rencana", use_container_width=True):
            st.session_state.current_page = "Tugas"
            st.rerun()
    with b3:
        if st.button("Ulangi Kuesioner", use_container_width=True):
            st.session_state.current_page = "Tes Preferensi"
            st.rerun()


# ==========================================
# 4. DASHBOARD (EDITORIAL PRODUCTIVITY)
# ==========================================
def render_dashboard():
    user = st.session_state.user
    tasks = st.session_state.tasks

    greeting = get_time_greeting()
    today_str = format_date_id(datetime.now())

    st.markdown(f"<div class='editorial-header-title'>{greeting}, {user.get('name', 'Mahasiswa')}</div>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='editorial-header-sub'>Pekan Akademik ke-9 &bull; {today_str} &bull; {user.get('study_program', 'Informatika')}</div>",
        unsafe_allow_html=True,
    )

    active_tasks = [t for t in tasks if t.get("status") != "Selesai"]
    completed_tasks = [t for t in tasks if t.get("status") == "Selesai"]
    total_active_minutes = sum(t.get("estimasi_menit", 0) for t in active_tasks)

    sorted_active = sorted(active_tasks, key=lambda x: x["tenggat"])
    nearest_task = sorted_active[0] if sorted_active else None

    # Baris Compact Metric Cards (4 Kolom Terencana)
    m1, m2, m3, m4 = st.columns(4)

    with m1:
        total_t = len(tasks)
        done_t = len(completed_tasks)
        pct_done = int((done_t / total_t) * 100) if total_t > 0 else 0
        st.markdown(
            f"""
            <div class='metric-card'>
                <div class='metric-label'>Tugas Aktif</div>
                <div class='metric-val'>{len(active_tasks)} <span style='font-size: 1rem; font-weight: 500; color: #58626E;'>tugas</span></div>
                <div class='metric-delta'>{done_t} selesai &bull; {pct_done}% progress</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with m2:
        if nearest_task:
            days_left = (nearest_task["tenggat"] - datetime.now()).days
            status_text = f"{days_left} hari lagi" if days_left >= 0 else "Lewat tenggat"
            st.markdown(
                f"""
                <div class='metric-card'>
                    <div class='metric-label'>Deadline Terdekat</div>
                    <div class='metric-val' style='font-size: 1.15rem; font-weight: 700; white-space: normal; line-height: 1.3;'>{nearest_task['matkul']}</div>
                    <div class='metric-delta'><span class='academic-pill pill-progress'>{status_text}</span> &bull; {nearest_task['tenggat'].strftime('%d %b')}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
                <div class='metric-card'>
                    <div class='metric-label'>Deadline Terdekat</div>
                    <div class='metric-val' style='font-size: 1.25rem;'>Tuntas</div>
                    <div class='metric-delta'>Semua tugas terselesaikan</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with m3:
        st.markdown(
            f"""
            <div class='metric-card'>
                <div class='metric-label'>Total Waktu Belajar</div>
                <div class='metric-val'>{format_duration(total_active_minutes)}</div>
                <div class='metric-delta'>Kebutuhan tugas aktif</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with m4:
        dom = user.get("dominant_preference", "Visual")
        st.markdown(
            f"""
            <div class='metric-card'>
                <div class='metric-label'>Modalitas Dominan</div>
                <div class='metric-val' style='color: #18524B;'>{dom}</div>
                <div class='metric-delta'>Preferensi aktif saat ini</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Balanced Two-Column Composition
    col_left, col_right = st.columns([1.35, 1.0])

    with col_left:
        st.markdown(
            "<div style='font-size: 1.15rem; font-weight: 700; color: #181D20; margin-bottom: 0.75rem;'>Agenda Prioritas: Apa yang Harus Dikerjakan?</div>",
            unsafe_allow_html=True,
        )
        if nearest_task:
            task_type_clean = nearest_task["jenis"].replace("_", " ").title()
            st.markdown(
                f"""
                <div class='editorial-card editorial-card-warning' style='padding: 1.5rem 1.75rem;'>
                    <div style='display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.5rem;'>
                        <span class='academic-pill pill-tag'>{nearest_task['matkul']}</span>
                        <span class='academic-pill pill-progress'>{nearest_task['status']}</span>
                    </div>
                    <h3 style='margin: 0.35rem 0 0.5rem 0; color: #181D20; font-size: 1.25rem; font-weight: 700;'>
                        {nearest_task['nama']}
                    </h3>
                    <div style='display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 0.85rem;'>
                        <span class='academic-pill pill-pending'>Jenis: {task_type_clean}</span>
                        <span class='academic-pill pill-pending'>Bobot: {nearest_task['bobot']}</span>
                        <span class='academic-pill pill-pending'>Durasi: {format_duration(nearest_task['estimasi_menit'])}</span>
                    </div>
                    <div style='font-size: 0.875rem; color: #58626E; margin-bottom: 1rem;'>
                        Tenggat pengumpulan: <strong>{nearest_task['tenggat'].strftime('%A, %d %B %Y, %H:%M WIB')}</strong>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            act_col1, act_col2 = st.columns([1.3, 1.0])
            with act_col1:
                if st.button("Jadwalkan Tugas Ini di Planner", type="primary", use_container_width=True):
                    st.session_state.selected_task_id = nearest_task["id"]
                    st.session_state.current_page = "Rencana"
                    st.rerun()
            with act_col2:
                if nearest_task["status"] != "Selesai":
                    if st.button("Tandai Selesai", use_container_width=True):
                        nearest_task["status"] = "Selesai"
                        st.rerun()
        else:
            st.markdown(
                """
                <div class='editorial-card'>
                    <h4 style='color: #18524B; margin-top: 0;'>Tidak ada tugas mendesak</h4>
                    <p style='color: #58626E; font-size: 0.9rem; margin: 0;'>Seluruh tugas terdaftar telah berhasil diselesaikan. Waktu yang baik untuk refleksi atau mengeksplorasi strategi belajar.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            "<div style='font-size: 1.15rem; font-weight: 700; color: #181D20; margin-bottom: 0.75rem;'>Daftar Tugas Pekan Ini</div>",
            unsafe_allow_html=True,
        )
        for t in sorted_active[1:4]:
            t_type = t["jenis"].replace("_", " ").title()
            st.markdown(
                f"""
                <div style='background: #FFFFFF; border: 1px solid #E6E3DB; border-radius: 8px; padding: 0.85rem 1.15rem; margin-bottom: 0.5rem; display: flex; justify-content: space-between; align-items: center;'>
                    <div>
                        <div style='font-weight: 600; font-size: 0.925rem; color: #181D20;'>{t['nama']}</div>
                        <div style='font-size: 0.8rem; color: #58626E; margin-top: 0.2rem;'>
                            {t['matkul']} &bull; {t_type} &bull; {format_duration(t['estimasi_menit'])}
                        </div>
                    </div>
                    <div style='text-align: right;'>
                        <span class='academic-pill pill-pending'>{t['tenggat'].strftime('%d %b %H:%M')}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        if st.button("Lihat Seluruh Daftar Tugas", use_container_width=True):
            st.session_state.current_page = "Tugas"
            st.rerun()

    with col_right:
        st.markdown(
            "<div style='font-size: 1.15rem; font-weight: 700; color: #181D20; margin-bottom: 0.75rem;'>Rekomendasi Strategi Belajar</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<p style='font-size: 0.85rem; color: #58626E; margin-top: -0.4rem; margin-bottom: 0.85rem;'>Disesuaikan dengan preferensi dominan dan konteks tugas.</p>",
            unsafe_allow_html=True,
        )
        cards = load_strategy_cards()
        dom = user.get("dominant_preference", "Visual")
        filtered_cards = [c for c in cards if dom.lower() in c.get("modality", "").lower()]
        card_recs = filtered_cards[:2] if filtered_cards else cards[:2]

        for c in card_recs:
            st.markdown(
                f"""
                <div class='editorial-card' style='padding: 1.15rem 1.35rem;'>
                    <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem;'>
                        <span class='academic-pill pill-tag'>{c.get('id', '')} &bull; {c.get('modality', '')}</span>
                        <span style='font-size: 0.75rem; color: #18524B; font-weight: 600;'>Sesuai Preferensi</span>
                    </div>
                    <h4 style='margin: 0.25rem 0 0.4rem 0; color: #181D20; font-size: 1.05rem;'>{c.get('strategy_name', '')}</h4>
                    <p style='font-size: 0.85rem; color: #58626E; line-height: 1.5; margin-bottom: 0.65rem;'>
                        {c.get('description', '')}
                    </p>
                    <div style='background: #F6F4EE; padding: 0.5rem 0.75rem; border-radius: 6px; font-size: 0.8rem; color: #38424D;'>
                        <strong>Contoh:</strong> {c.get('example_for_college_task', '-')}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        if st.button("Eksplorasi Katalog Strategi", use_container_width=True):
            st.session_state.current_page = "Strategi"
            st.rerun()


# ==========================================
# 5. TUGAS (TASK MANAGEMENT)
# ==========================================
def render_tasks():
    st.markdown("<div class='editorial-header-title'>Manajemen Tugas Kuliah</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='editorial-header-sub'>Pantau tenggat akademik, atur bobot pengerjaan, dan hitung estimasi beban waktu secara objektif.</div>",
        unsafe_allow_html=True,
    )

    tab_list, tab_add = st.tabs(["Daftar Tugas", "Tambah Tugas Baru"])

    with tab_list:
        tasks = st.session_state.tasks
        if not tasks:
            st.info("Belum ada tugas kuliah tersimpan. Gunakan tab 'Tambah Tugas Baru' untuk mencatat tugas.")
        else:
            filter_mode = st.pills("Filter Tampilan", ["Semua", "Sedang Dikerjakan", "Belum Dimulai", "Selesai"], default="Semua")
            filtered_tasks = tasks
            if filter_mode != "Semua":
                filtered_tasks = [t for t in tasks if t.get("status") == filter_mode]

            for t in filtered_tasks:
                status_pill = {
                    "Selesai": "pill-selesai",
                    "Sedang Dikerjakan": "pill-progress",
                    "Belum Dimulai": "pill-pending",
                    "Terlambat": "pill-late",
                }.get(t["status"], "pill-pending")

                t_type = t["jenis"].replace("_", " ").title()

                st.markdown(
                    f"""
                    <div class='editorial-card'>
                        <div style='display: flex; justify-content: space-between; align-items: flex-start;'>
                            <div>
                                <span class='academic-pill pill-tag'>{t['matkul']}</span>
                                <h3 style='margin: 0.35rem 0 0.45rem 0; color: #181D20; font-size: 1.15rem; font-weight: 700;'>
                                    {t['nama']}
                                </h3>
                            </div>
                            <span class='academic-pill {status_pill}'>{t['status']}</span>
                        </div>
                        <div style='display: flex; gap: 8px; flex-wrap: wrap; margin: 0.5rem 0 0.75rem 0;'>
                            <span class='academic-pill pill-pending'>Jenis: {t_type}</span>
                            <span class='academic-pill pill-pending'>Bobot: {t['bobot']}</span>
                            <span class='academic-pill pill-pending'>Estimasi: {format_duration(t['estimasi_menit'])} ({t['estimasi_menit']} mnt)</span>
                            <span class='academic-pill pill-pending'>Tenggat: {t['tenggat'].strftime('%d %b %Y, %H:%M')}</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                b_c1, b_c2, b_c3, _ = st.columns([1.2, 1.2, 1.0, 2.5])
                with b_c1:
                    if st.button("Rancang Jadwal", key=f"plan_{t['id']}", use_container_width=True):
                        st.session_state.selected_task_id = t["id"]
                        st.session_state.current_page = "Rencana"
                        st.rerun()
                with b_c2:
                    if t["status"] != "Selesai":
                        if st.button("Tandai Selesai", key=f"done_{t['id']}", use_container_width=True):
                            t["status"] = "Selesai"
                            st.rerun()
                    else:
                        if st.button("Buka Kembali", key=f"reopen_{t['id']}", use_container_width=True):
                            t["status"] = "Sedang Dikerjakan"
                            st.rerun()
                with b_c3:
                    if st.button("Hapus", key=f"del_{t['id']}", use_container_width=True):
                        st.session_state.tasks = [item for item in st.session_state.tasks if item["id"] != t["id"]]
                        st.rerun()

    with tab_add:
        st.markdown(
            """
            <div class='academic-notice'>
                <strong>Ketentuan Estimasi Backend:</strong> Opsi jenis tugas mengambil langsung dari pustaka resmi 
                <code>services.tools.effort.MENIT_DASAR</code>. Estimasi menit dihitung secara real-time via 
                <code>estimate_effort(jenis, bobot)</code>.
            </div>
            """,
            unsafe_allow_html=True,
        )

        jenis_options = list(MENIT_DASAR.keys())

        with st.form("form_tambah_tugas_editorial"):
            f_nama = st.text_input("Nama / Judul Tugas Kuliah", placeholder="Contoh: Laporan Akhir Analisis Jaringan Komputer")
            f_matkul = st.text_input("Nama Mata Kuliah", placeholder="Contoh: Komunikasi Data dan Jaringan")

            col_jenis, col_bobot = st.columns(2)
            with col_jenis:
                f_jenis = st.selectbox(
                    "Jenis Tugas (Standar Backend)",
                    options=jenis_options,
                    format_func=lambda x: f"{x.replace('_', ' ').title()} (Menit Dasar: {MENIT_DASAR[x]}m)",
                )
            with col_bobot:
                f_bobot = st.slider(
                    "Bobot Kesulitan Tugas (0.0 = Ringan, 1.0 = Sangat Kompleks)",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.25,
                    step=0.05,
                )

            # Hitung estimasi real-time dari backend asli
            estimasi_kalkulasi = estimate_effort(jenis=f_jenis, bobot=f_bobot)
            st.markdown(
                f"""
                <div style='background: #EDF5F4; border: 1px solid #D0E5E3; border-radius: 8px; padding: 0.85rem 1.15rem; margin: 0.5rem 0 1rem 0;'>
                    <div style='font-size: 0.775rem; text-transform: uppercase; font-weight: 700; color: #18524B; letter-spacing: 0.05em;'>
                        Hasil Perhitungan estimate_effort
                    </div>
                    <div style='font-size: 1.25rem; font-weight: 700; color: #18524B;'>
                        {format_duration(estimasi_kalkulasi)} <span style='font-size: 0.9rem; font-weight: 500;'>({estimasi_kalkulasi} menit)</span>
                    </div>
                    <div style='font-size: 0.8rem; color: #58626E;'>Formula: ceil({MENIT_DASAR[f_jenis]}m &times; (1 + {f_bobot}))</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            col_tgl, col_jam = st.columns(2)
            with col_tgl:
                f_tgl = st.date_input("Tanggal Tenggat (Deadline)", value=datetime.now().date() + timedelta(days=3))
            with col_jam:
                f_jam = st.time_input("Jam Tenggat", value=time(23, 59))

            f_status = st.selectbox(
                "Status Pengerjaan Awal",
                options=["Belum Dimulai", "Sedang Dikerjakan", "Selesai", "Terlambat"],
                index=0,
            )

            submit_tugas = st.form_submit_button("Simpan Tugas Baru", type="primary")

            if submit_tugas:
                if not f_nama.strip() or not f_matkul.strip():
                    st.error("Nama tugas dan nama mata kuliah wajib diisi.")
                else:
                    tenggat_dt = datetime.combine(f_tgl, f_jam)
                    new_id = max([t["id"] for t in st.session_state.tasks], default=0) + 1
                    new_task = {
                        "id": new_id,
                        "nama": f_nama.strip(),
                        "matkul": f_matkul.strip(),
                        "jenis": f_jenis,
                        "bobot": float(f_bobot),
                        "estimasi_menit": estimasi_kalkulasi,
                        "tenggat": tenggat_dt,
                        "status": f_status,
                    }
                    st.session_state.tasks.append(new_task)
                    st.success(f"Tugas '{f_nama}' berhasil ditambahkan ke sistem!")
                    st.rerun()


# ==========================================
# 6. RENCANA (PLANNER & SCHEDULER)
# ==========================================
def render_planner():
    st.markdown("<div class='editorial-header-title'>Rancang Jadwal Belajar (Planner)</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='editorial-header-sub'>Alokasikan sesi pengerjaan tugas ke dalam slot waktu luang dengan validasi aturan constraint RB-05.</div>",
        unsafe_allow_html=True,
    )

    tasks = st.session_state.tasks
    if not tasks:
        st.info("Belum ada tugas kuliah yang terdaftar. Buat tugas terlebih dahulu di halaman Tugas.")
        return

    task_map = {f"{t['nama']} ({t['matkul']})": t["id"] for t in tasks}
    selected_id = st.session_state.selected_task_id
    default_index = 0
    for idx, (label, tid) in enumerate(task_map.items()):
        if tid == selected_id:
            default_index = idx
            break

    selected_label = st.selectbox("Pilih Tugas yang Ingin Dijadwalkan", options=list(task_map.keys()), index=default_index)
    current_task = next(t for t in tasks if t["id"] == task_map[selected_label])
    st.session_state.selected_task_id = current_task["id"]

    t_type = current_task["jenis"].replace("_", " ").title()

    # Detail Tugas Card
    st.markdown(
        f"""
        <div class='editorial-card' style='border-top: 3px solid #18524B;'>
            <div style='display: flex; justify-content: space-between; align-items: flex-start;'>
                <div>
                    <span class='academic-pill pill-tag'>{current_task['matkul']}</span>
                    <h3 style='margin: 0.35rem 0 0.35rem 0; color: #181D20;'>{current_task['nama']}</h3>
                    <div style='font-size: 0.85rem; color: #58626E;'>
                        Jenis: {t_type} &bull; Bobot: {current_task['bobot']} &bull; Tenggat: <strong>{current_task['tenggat'].strftime('%d %B %Y, %H:%M WIB')}</strong>
                    </div>
                </div>
                <div style='text-align: right;'>
                    <div style='font-size: 0.75rem; text-transform: uppercase; color: #8B95A0; font-weight: 700;'>Kebutuhan Durasi</div>
                    <div style='font-size: 1.35rem; font-weight: 700; color: #18524B;'>{format_duration(current_task['estimasi_menit'])}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Analisis Kapasitas Real-Time
    free_slots = st.session_state.free_slots
    menit_tersedia = hitung_menit_tersedia(
        slot_kosong=free_slots,
        tenggat=current_task["tenggat"],
    )
    kapasitas = check_capacity(
        menit_tersedia=menit_tersedia,
        total_estimasi_menit=current_task["estimasi_menit"],
    )

    col_slot_left, col_slot_right = st.columns([1.3, 1.0])

    with col_slot_left:
        st.markdown("<div style='font-size: 1.05rem; font-weight: 700; color: #181D20; margin-bottom: 0.5rem;'>Jendela Slot Waktu Luang Mahasiswa</div>", unsafe_allow_html=True)
        st.caption("Daftar waktu luang yang dialokasikan sebelum tenggat tugas.")

        if not free_slots:
            st.warning("Belum ada slot waktu luang yang dialokasikan.")
        else:
            for i, (start, end) in enumerate(free_slots):
                durasi = int((end - start).total_seconds() / 60)
                is_before_deadline = end <= current_task["tenggat"]
                tag_deadline = "<span class='academic-pill pill-selesai'>Sebelum Tenggat</span>" if is_before_deadline else "<span class='academic-pill pill-late'>Melewati Tenggat</span>"

                st.markdown(
                    f"""
                    <div class='time-block-row'>
                        <div>
                            <strong>Slot {i + 1}:</strong> {start.strftime('%a, %d %b %Y')} &bull; {start.strftime('%H:%M')} &mdash; {end.strftime('%H:%M')} WIB
                        </div>
                        <div style='display: flex; gap: 8px; align-items: center;'>
                            <span style='font-size: 0.825rem; font-weight: 600; color: #58626E;'>{durasi} mnt</span>
                            {tag_deadline}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.markdown("<br>", unsafe_allow_html=True)
        # Visual Kapasitas Progress Bar
        need_m = current_task["estimasi_menit"]
        ratio = min(menit_tersedia / need_m, 1.0) if need_m > 0 else 1.0

        st.markdown(f"**Rasio Kecukupan Waktu:** {menit_tersedia} mnt tersedia / {need_m} mnt dibutuhkan")
        st.progress(ratio)

        c_status_class = "pill-selesai" if kapasitas["cukup"] else "pill-late"
        c_status_label = f"Waktu Cukup (+{kapasitas['selisih']} mnt)" if kapasitas["cukup"] else f"Waktu Kurang ({kapasitas['selisih']} mnt)"
        st.markdown(f"Status Kapasitas: <span class='academic-pill {c_status_class}'>{c_status_label}</span>", unsafe_allow_html=True)

    with col_slot_right:
        st.markdown("<div style='font-size: 1.05rem; font-weight: 700; color: #181D20; margin-bottom: 0.5rem;'>Tambah Slot Waktu Luang</div>", unsafe_allow_html=True)
        with st.form("form_slot_baru"):
            s_tgl = st.date_input("Tanggal Sesi", value=datetime.now().date() + timedelta(days=1))
            s_mulai = st.time_input("Mulai Pukul", value=time(9, 0))
            s_selesai = st.time_input("Selesai Pukul", value=time(12, 0))

            submit_slot = st.form_submit_button("Tambahkan Jendela Waktu", use_container_width=True)
            if submit_slot:
                dt_mulai = datetime.combine(s_tgl, s_mulai)
                dt_selesai = datetime.combine(s_tgl, s_selesai)
                if dt_mulai >= dt_selesai:
                    st.error("Waktu mulai harus lebih awal dari waktu selesai.")
                else:
                    st.session_state.free_slots.append((dt_mulai, dt_selesai))
                    st.success("Slot waktu luang berhasil ditambahkan!")
                    st.rerun()

        if st.button("Reset ke Slot Bawaan", use_container_width=True):
            now_dt = datetime.now()
            today_base = datetime(now_dt.year, now_dt.month, now_dt.day, 8, 0)
            st.session_state.free_slots = [
                (today_base + timedelta(days=0, hours=6), today_base + timedelta(days=0, hours=9)),
                (today_base + timedelta(days=1, hours=1), today_base + timedelta(days=1, hours=4)),
                (today_base + timedelta(days=1, hours=6), today_base + timedelta(days=1, hours=9)),
                (today_base + timedelta(days=2, hours=1), today_base + timedelta(days=2, hours=4)),
            ]
            st.rerun()

    st.markdown("<br><hr style='border: none; border-top: 1px solid #E6E3DB;'><br>", unsafe_allow_html=True)

    # Eksekusi Auto-Planner
    st.markdown("<div style='font-size: 1.15rem; font-weight: 700; color: #181D20; margin-bottom: 0.5rem;'>Eksekusi Penjadwalan Terverifikasi (Auto-Planner)</div>", unsafe_allow_html=True)
    c_p1, c_p2 = st.columns([1.3, 1.0])
    with c_p1:
        maks_blok = st.slider(
            "Batas Maksimal Durasi per Blok Belajar (Menit)",
            min_value=15,
            max_value=120,
            value=st.session_state.user.get("max_block_minutes", 60),
            step=15,
            help="Menjaga fokus belajar tetap optimal dengan membatasi sesi pengerjaan maksimal 45-60 menit.",
        )
    with c_p2:
        st.write("")
        st.write("")
        jalankan = st.button("Rancang Jadwal dengan Auto-Planner", type="primary", use_container_width=True)

    if jalankan:
        with st.spinner("Menjalankan pipeline plan_task (estimasi, kapasitas, pembagian blok, dan verifikasi RB-05)..."):
            try:
                plan_result = plan_task(
                    jenis=current_task["jenis"],
                    bobot=current_task["bobot"],
                    slot_kosong=st.session_state.free_slots,
                    tenggat=current_task["tenggat"],
                    maks_blok_menit=maks_blok,
                )
                st.session_state.current_plan = plan_result
            except Exception as e:
                st.error(f"Terjadi kesalahan saat memanggil planner backend: {e}")

    # Tampilkan Hasil Penjadwalan
    if st.session_state.current_plan:
        plan = st.session_state.current_plan
        status = plan["status"]

        st.markdown("<br>", unsafe_allow_html=True)

        if status == "TERJADWAL":
            st.markdown(
                """
                <div class='editorial-card editorial-card-highlight' style='background: #F4F9F6;'>
                    <h4 style='color: #1B6122; margin-top: 0; margin-bottom: 0.35rem;'>Status: TERJADWAL &mdash; Jadwal Berhasil Dirancang</h4>
                    <p style='color: #38424D; font-size: 0.9rem; margin: 0;'>
                        Seluruh kebutuhan waktu tugas berhasil dialokasikan ke dalam jendela waktu luang dan memenuhi semua aturan constraint verifier.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        elif status == "WAKTU_TIDAK_CUKUP":
            selisih = plan["kecukupan"]["selisih"]
            st.markdown(
                f"""
                <div class='editorial-card editorial-card-warning' style='background: #FFFBF2;'>
                    <h4 style='color: #9C6300; margin-top: 0; margin-bottom: 0.35rem;'>Status: WAKTU TIDAK CUKUP</h4>
                    <p style='color: #38424D; font-size: 0.9rem; margin: 0;'>
                        Total waktu luang sebelum tenggat ({plan['menit_tersedia']} menit) kurang {abs(selisih)} menit dari kebutuhan tugas ({plan['estimasi_menit']} menit). 
                        Sesi belajar di bawah ini dialokasikan semaksimal mungkin sesuai slot yang tersedia.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        elif status == "GAGAL_VERIFIKASI":
            pelanggaran_list = plan["verifikasi"].get("pelanggaran", [])
            st.markdown(
                f"""
                <div class='editorial-card' style='border-left: 4px solid #A83228; background: #FDF6F5;'>
                    <h4 style='color: #A83228; margin-top: 0; margin-bottom: 0.35rem;'>Status: GAGAL VERIFIKASI</h4>
                    <p style='color: #38424D; font-size: 0.9rem; margin: 0;'>
                        Rencana jadwal melanggar aturan constraint: {', '.join(pelanggaran_list)}.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        blok_list = plan.get("blok", [])
        if not blok_list:
            st.info("Tidak ada sesi yang dapat dijadwalkan pada slot waktu yang ada.")
        else:
            st.markdown(f"**Alokasi Blok Waktu Terjadwal ({len(blok_list)} Sesi Belajar):**")
            total_terjadwal = 0
            for i, (b_start, b_end) in enumerate(blok_list):
                b_dur = int((b_end - b_start).total_seconds() / 60)
                total_terjadwal += b_dur
                st.markdown(
                    f"""
                    <div class='editorial-card' style='padding: 0.95rem 1.25rem; margin-bottom: 0.5rem;'>
                        <div style='display: flex; justify-content: space-between; align-items: center;'>
                            <div>
                                <span class='academic-pill pill-tag'>Sesi {i + 1}</span>
                                <strong style='font-size: 0.95rem; color: #181D20; margin-left: 0.5rem;'>{b_start.strftime('%A, %d %B %Y')}</strong>
                            </div>
                            <span class='academic-pill pill-pending'>{b_dur} Menit</span>
                        </div>
                        <div style='font-size: 0.85rem; color: #58626E; margin-top: 0.35rem;'>
                            Waktu: <strong>{b_start.strftime('%H:%M')} &mdash; {b_end.strftime('%H:%M')} WIB</strong>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            st.caption(f"Total durasi sesi terjadwal: **{format_duration(total_terjadwal)}** ({total_terjadwal} menit).")

        verif = plan.get("verifikasi", {})
        with st.expander("Laporan Verifikasi Aturan (Schedule Verifier)"):
            st.write(f"- Status Valid: `{verif.get('valid')}`")
            pelanggaran = verif.get("pelanggaran", [])
            if not pelanggaran:
                st.write("- Seluruh constraint terpenuhi: durasi per blok tidak melebihi batas, tidak ada tumpang tindih, dan tidak melewati tenggat waktu.")
            else:
                st.write("- Pelanggaran yang terdeteksi:")
                for p in pelanggaran:
                    st.write(f"  * `{p}`")


# ==========================================
# 7. STRATEGI BELAJAR (KNOWLEDGE BASE)
# ==========================================
def render_strategies():
    st.markdown("<div class='editorial-header-title'>Katalog Strategi Belajar (VARK)</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='editorial-header-sub'>Basis pengetahuan 20 kartu panduan belajar mandiri untuk memperkaya cara menyerap materi perkuliahan.</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class='academic-notice'>
            <strong>Pedoman Penggunaan:</strong> Strategi yang disarankan berdasarkan preferensi dan konteks tugas. 
            Setiap mahasiswa bebas mengeksplorasi dan mengombinasikan strategi sesuai kenyamanan pribadi.
        </div>
        """,
        unsafe_allow_html=True,
    )

    cards = load_strategy_cards()
    user_dom = st.session_state.user.get("dominant_preference", "Visual")

    tab_labels = ["Semua", "Visual", "Aural/Auditory", "Read/Write", "Kinesthetic"]
    tabs = st.tabs(tab_labels)

    for tab, label in zip(tabs, tab_labels):
        with tab:
            if label == "Semua":
                filtered = cards
            else:
                filtered = [c for c in cards if label.lower() in c.get("modality", "").lower()]

            search_query = st.text_input(
                f"Cari strategi ({label})",
                placeholder="Ketik kata kunci nama strategi, mata kuliah, atau kata kunci...",
                key=f"search_input_{label}",
            )
            if search_query.strip():
                q = search_query.lower()
                filtered = [
                    c for c in filtered
                    if q in c.get("strategy_name", "").lower()
                    or q in c.get("description", "").lower()
                    or q in c.get("example_for_college_task", "").lower()
                ]

            if not filtered:
                st.info("Tidak ada strategi yang sesuai dengan kata kunci pencarian.")
            else:
                for c in filtered:
                    is_dom = user_dom.lower() in c.get("modality", "").lower()
                    badge_pref = "<span class='academic-pill pill-selesai'>Sesuai Preferensi Aktif</span>" if is_dom else ""

                    html_card = (
                        f"<div class='editorial-card'>"
                        f"<div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem;'>"
                        f"<div>"
                        f"<span class='academic-pill pill-tag'>{c.get('id', '')} &bull; {c.get('modality', '')}</span>"
                        f"<span style='font-size: 1.15rem; font-weight: 700; color: #181D20; margin-left: 0.5rem;'>"
                        f"{c.get('strategy_name', '')}"
                        f"</span>"
                        f"</div>"
                        f"{badge_pref}"
                        f"</div>"
                        f"<p style='color: #58626E; font-size: 0.925rem; line-height: 1.6; margin-bottom: 0.75rem;'>"
                        f"{c.get('description', '')}"
                        f"</p>"
                        f"<div style='background: #F6F4EE; padding: 0.75rem 1rem; border-radius: 8px; font-size: 0.85rem; color: #38424D; margin-bottom: 0.5rem;'>"
                        f"<div><strong>Cocok untuk:</strong> {c.get('suitable_for', '-')}</div>"
                        f"<div style='margin-top: 0.25rem;'><strong>Contoh tugas:</strong> {c.get('example_for_college_task', '-')}</div>"
                        f"</div>"
                        f"</div>"
                    )
                    st.markdown(html_card, unsafe_allow_html=True)
                    with st.expander(f"Langkah Penerapan Praktis: {c.get('strategy_name', '')}"):
                        for idx, step in enumerate(c.get("how_to_apply", []), start=1):
                            st.write(f"{idx}. {step}")


# ==========================================
# 8. AI SELARAS (STUDY COMPANION)
# ==========================================
def render_ai_assistant():
    st.markdown("<div class='editorial-header-title'>AI Selaras</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='editorial-header-sub'>Pendamping dialogis untuk memecah beban tugas kuliah, konsultasi kapasitas waktu, dan rekomendasi strategi belajar.</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class='academic-notice'>
            <strong>Antarmuka Studi Akademik:</strong> Asisten ini berfokus pada manajemen tugas dan perencanaan belajar. 
            Gunakan tombol pertanyaan cepat di bawah atau tulis pertanyaan spesifik seputar tugas perkuliahanmu.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Prompt Chips
    st.markdown("**Konsultasi Cepat:**")
    q1, q2 = st.columns(2)
    with q1:
        btn_q1 = st.button("Strategi pengerjaan tugas Makalah untuk Visual", use_container_width=True)
        btn_q2 = st.button("Solusi jika waktu sebelum deadline tidak cukup", use_container_width=True)
    with q2:
        btn_q3 = st.button("Cara memecah tugas besar ke dalam blok 60 menit", use_container_width=True)
        btn_q4 = st.button("Ringkasan beban tugas aktif minggu ini", use_container_width=True)

    prompt_selected = None
    if btn_q1:
        prompt_selected = "Strategi pengerjaan tugas Makalah untuk preferensi Visual"
    elif btn_q2:
        prompt_selected = "Solusi jika waktu sebelum deadline tidak cukup"
    elif btn_q3:
        prompt_selected = "Cara memecah tugas besar ke dalam blok 60 menit"
    elif btn_q4:
        prompt_selected = "Ringkasan beban tugas aktif minggu ini"

    # Riwayat Percakapan
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_query = st.chat_input("Tanyakan rencana tugas atau strategi belajarmu di sini...")
    effective_query = user_query or prompt_selected

    if effective_query:
        st.session_state.chat_history.append({"role": "user", "content": effective_query})
        with st.chat_message("user"):
            st.markdown(effective_query)

        user = st.session_state.user
        dom = user.get("dominant_preference", "Visual")
        active_tasks = [t for t in st.session_state.tasks if t.get("status") != "Selesai"]
        query_low = effective_query.lower()

        if "makalah" in query_low:
            resp = (
                f"Untuk tugas berjenis **Makalah**, menit dasar komputasinya adalah **{MENIT_DASAR.get('makalah', 240)} menit** dasar. "
                f"Berdasarkan preferensi **{dom}** Anda:\n\n"
                f"- **V01 (Mind Mapping):** Susun kerangka bab dan subbab dalam bentuk peta bercabang terlebih dahulu.\n"
                f"- **V05 (Color Coding):** Gunakan penanda warna berbeda untuk membedakan kutipan teori, analisis data, dan kesimpulan.\n\n"
                f"Sangat disarankan membagi pengerjaan makalah menjadi beberapa sesi berdurasi maksimal **{user.get('max_block_minutes', 60)} menit** "
                f"melalui menu **Rencana** agar penulisan tetap fokus dan tidak jenuh."
            )
        elif "kurang" in query_low or "deadline" in query_low or "waktu" in query_low and "solusi" in query_low:
            resp = (
                "Ketika kapasitas waktu sebelum tenggat tidak mencukupi (`WAKTU_TIDAK_CUKUP`), berikut langkah penyesuaian yang dapat dilakukan:\n\n"
                "1. **Buka Jendela Waktu Tambahan:** Tambahkan slot luang baru pada menu **Rencana** pada hari menjelang tenggat.\n"
                "2. **Pengerjaan Parsial Prioritas:** Kerjakan blok-blok sesi yang telah berhasil dialokasikan semampunya untuk menuntaskan bagian substansi pokok.\n"
                "3. **Tinjau Bobot Tugas:** Periksa apakah lingkup bahasan tugas dapat disederhanakan tanpa mengurangi esensi tugas."
            )
        elif "memecah" in query_low or "blok" in query_low:
            resp = (
                f"Memecah tugas ke dalam blok berdurasi **{user.get('max_block_minutes', 60)} menit** merupakan prinsip kerja modul `schedule_blocks` di backend kami:\n\n"
                "- **Sesi 1 (Menit 0-60):** Penentuan topik, pengumpulan literatur, dan penyusunan kerangka.\n"
                "- **Sesi 2 (Menit 60-120):** Penulisan konten utama atau pengolahan data praktikum.\n"
                "- **Sesi 3 (Menit 120-dst):** Penulisan kesimpulan, formatting, dan verifikasi akhir.\n\n"
                "Di antara setiap blok, sisipkan jeda istirahat 5-10 menit untuk menjaga ketajaman konsentrasi."
            )
        elif "beban" in query_low or "ringkasan" in query_low:
            tot_mnt = sum(t.get("estimasi_menit", 0) for t in active_tasks)
            t_lines = "\n".join([f"- **{t['nama']}** ({t['matkul']}): {format_duration(t['estimasi_menit'])}" for t in active_tasks])
            resp = (
                f"Saat ini kamu memiliki **{len(active_tasks)} tugas aktif** dengan total estimasi durasi **{format_duration(tot_mnt)}**:\n\n"
                f"{t_lines}\n\n"
                f"Tugas terdekat dapat langsung kamu jadwalkan secara otomatis melalui halaman **Rencana**."
            )
        else:
            resp = (
                f"Saya siap mendampingi pengelolaan tugas kuliahmu. "
                f"Berdasarkan preferensi **{dom}** dan {len(active_tasks)} tugas aktifmu saat ini, "
                f"kamu dapat berkonsultasi mengenai strategi tugas tertentu, memeriksa estimasi menit, atau menyusun jadwal sesi belajar di halaman **Rencana**."
            )

        st.session_state.chat_history.append({"role": "assistant", "content": resp})
        with st.chat_message("assistant"):
            st.markdown(resp)


# ==========================================
# 9. PROFIL MAHASISWA & PENGATURAN
# ==========================================
def render_profile():
    st.markdown("<div class='editorial-header-title'>Profil & Konfigurasi Akademik</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='editorial-header-sub'>Informasi identitas mahasiswa, riwayat preferensi belajar, dan konfigurasi penjadwalan.</div>",
        unsafe_allow_html=True,
    )

    user = st.session_state.user
    tasks = st.session_state.tasks

    col_p1, col_p2 = st.columns([1.2, 1.0])

    with col_p1:
        st.markdown(
            """
            <div class='editorial-card'>
                <h4 style='color: #181D20; margin-top: 0;'>Data Identitas Mahasiswa</h4>
            """,
            unsafe_allow_html=True,
        )
        with st.form("form_edit_profil"):
            p_nama = st.text_input("Nama Lengkap", value=user.get("name", "Mahasiswa"))
            p_prodi = st.text_input("Program Studi", value=user.get("study_program", "Teknik Informatika"))
            p_sem = st.number_input("Semester Aktif", min_value=1, max_value=14, value=user.get("semester", 5))

            st.markdown("<hr style='border: none; border-top: 1px solid #EAE7DF; margin: 1rem 0;'>", unsafe_allow_html=True)
            st.markdown("**Konfigurasi Default Penjadwalan**")
            p_blok = st.slider(
                "Default Durasi Maksimal per Blok Belajar (Menit)",
                min_value=15,
                max_value=120,
                value=user.get("max_block_minutes", 60),
                step=15,
            )

            submit_p = st.form_submit_button("Simpan Perubahan Profil", type="primary")
            if submit_p:
                user["name"] = p_nama
                user["study_program"] = p_prodi
                user["semester"] = int(p_sem)
                user["max_block_minutes"] = int(p_blok)
                st.success("Profil dan pengaturan berhasil diperbarui.")
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with col_p2:
        dom = user.get("dominant_preference", "Visual")
        scores = user.get("vark_scores", {"Visual": 0, "Aural": 0, "Read/Write": 0, "Kinesthetic": 0})
        st.markdown(
            f"""
            <div class='editorial-card editorial-card-highlight'>
                <div style='font-size: 0.75rem; text-transform: uppercase; font-weight: 700; color: #18524B; letter-spacing: 0.06em;'>
                    Status Preferensi Belajar (VARK)
                </div>
                <div style='font-size: 1.45rem; font-weight: 700; color: #181D20; margin: 0.25rem 0;'>
                    {dom}
                </div>
                <div style='font-size: 0.85rem; color: #58626E; margin-bottom: 0.85rem;'>
                    Visual: {scores.get('Visual', 0)} &bull; 
                    Aural: {scores.get('Aural', 0)} &bull; 
                    Read/Write: {scores.get('Read/Write', 0)} &bull; 
                    Kinestetik: {scores.get('Kinesthetic', 0)}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("Ulangi Tes Preferensi Belajar", use_container_width=True):
            st.session_state.current_page = "Tes Preferensi"
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class='editorial-card'>
                <h4 style='color: #181D20; margin-top: 0; margin-bottom: 0.5rem;'>Statistik Akademik</h4>
                <div style='font-size: 0.875rem; color: #58626E; line-height: 1.6;'>
                    &bull; Total tugas tercatat: <strong>{len(tasks)} tugas</strong><br>
                    &bull; Tugas selesai: <strong>{len([t for t in tasks if t.get('status') == 'Selesai'])} tugas</strong><br>
                    &bull; Tugas aktif: <strong>{len([t for t in tasks if t.get('status') != 'Selesai'])} tugas</strong>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ==========================================
# 10. REFLEKSI MINGGUAN
# ==========================================
def render_reflection():
    st.markdown("<div class='editorial-header-title'>Refleksi Belajar Mingguan</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='editorial-header-sub'>Evaluasi ritme belajar mandiri, efektivitas strategi studi, dan rencana penyesuaian pekan berikutnya.</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class='academic-notice'>
            <strong>Proses Metakognitif:</strong> Refleksi berkala membantu mahasiswa membangun kesadaran ritme belajar mandiri 
            dan memvalidasi apakah estimasi waktu serta strategi yang dicoba benar-benar membantu tugas perkuliahan.
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_form, col_hist = st.columns([1.2, 1.0])

    with col_form:
        st.markdown("<div style='font-size: 1.1rem; font-weight: 700; color: #181D20; margin-bottom: 0.5rem;'>Catat Jurnal Refleksi Baru</div>", unsafe_allow_html=True)
        cards = load_strategy_cards()
        strategy_options = [f"{c['id']} - {c['strategy_name']}" for c in cards]

        with st.form("form_refleksi_editorial"):
            r_strat = st.selectbox("1. Strategi apa yang paling membantu minggu ini?", options=strategy_options)
            r_kendala = st.text_area(
                "2. Apa yang paling sulit atau menjadi hambatan belajar?",
                placeholder="Contoh: Kesulitan mengatur konsentrasi di sesi sore hari, atau literatur yang sulit dipahami...",
            )
            r_perbaikan = st.text_area(
                "3. Apa yang ingin diperbaiki atau disesuaikan minggu depan?",
                placeholder="Contoh: Membagi tugas makalah menjadi blok 45 menit dan mulai mencicil 3 hari lebih awal...",
            )
            r_skor = st.slider("Tingkat Kepuasan Ritme Belajar Pekan Ini (1 = Sangat Burnout, 5 = Sangat Seimbang)", 1, 5, 4)

            submit_r = st.form_submit_button("Simpan Refleksi Mingguan", type="primary")
            if submit_r:
                if not r_kendala.strip() or not r_perbaikan.strip():
                    st.error("Mohon lengkapi catatan kendala dan rencana perbaikan.")
                else:
                    new_ref = {
                        "tanggal": format_date_id(datetime.now()),
                        "strategi_terbantu": r_strat,
                        "hambatan": r_kendala.strip(),
                        "perbaikan": r_perbaikan.strip(),
                        "skor_kepuasan": r_skor,
                    }
                    st.session_state.reflections.insert(0, new_ref)
                    st.success("Refleksi mingguan berhasil disimpan!")
                    st.rerun()

    with col_hist:
        st.markdown("<div style='font-size: 1.1rem; font-weight: 700; color: #181D20; margin-bottom: 0.5rem;'>Riwayat Jurnal Refleksi</div>", unsafe_allow_html=True)
        reflections = st.session_state.reflections
        if not reflections:
            st.info("Belum ada catatan refleksi tersimpan.")
        else:
            for r in reflections:
                st.markdown(
                    f"""
                    <div class='editorial-card'>
                        <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem;'>
                            <strong style='color: #181D20; font-size: 0.95rem;'>{r.get('tanggal', 'Catatan')}</strong>
                            <span class='academic-pill pill-selesai'>Skor: {r.get('skor_kepuasan', 4)}/5</span>
                        </div>
                        <div style='font-size: 0.85rem; color: #18524B; font-weight: 600; margin-bottom: 0.35rem;'>
                            Strategi: {r.get('strategi_terbantu', '-')}
                        </div>
                        <div style='font-size: 0.825rem; color: #58626E; line-height: 1.5;'>
                            <strong>Kendala:</strong> {r.get('hambatan', '-')}<br>
                            <strong>Rencana:</strong> {r.get('perbaikan', '-')}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
