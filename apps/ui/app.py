import sys
from pathlib import Path
import streamlit as st

# Root proyek SelarasBelajar
BASE_DIR = Path(__file__).resolve().parents[2]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from apps.ui.data import init_session_state
from apps.ui.components import (
    inject_custom_css,
    render_landing,
    render_test_vark,
    render_result_vark,
    render_dashboard,
    render_tasks,
    render_planner,
    render_strategies,
    render_ai_assistant,
    render_profile,
    render_reflection,
)


def main():
    st.set_page_config(
        page_title="SelarasBelajar.Lab",
        page_icon="🎓",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Inisialisasi session state & stylesheet CSS editorial
    init_session_state()
    inject_custom_css()

    user = st.session_state.user
    curr_page = st.session_state.current_page

    # ==========================================
    # SIDEBAR BESPOKE & NAVIGASI
    # ==========================================
    with st.sidebar:
        # 1. Brand Header
        st.markdown(
            """
            <div style='margin-bottom: 1.25rem; display: flex; align-items: center; gap: 10px;'>
                <div style='width: 38px; height: 38px; border-radius: 9px; background-color: #18524B; display: flex; align-items: center; justify-content: center; color: #FFFFFF; font-weight: 800; font-size: 1.15rem; box-shadow: 0 2px 5px rgba(24, 82, 75, 0.25);'>
                    ✦
                </div>
                <div>
                    <div style='font-size: 1.2rem; font-weight: 800; color: #181D20; letter-spacing: -0.02em; line-height: 1.2;'>
                        SelarasBelajar<span style='color: #18524B;'>.Lab</span>
                    </div>
                    <div style='font-size: 0.725rem; color: #7A8490; font-weight: 500;'>
                        Academic Productivity
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # 2. Student Profile Card
        initials = "".join([part[0] for part in user.get("name", "M").split()[:2]]).upper()
        dom_pref = user.get("dominant_preference", "Visual")

        st.markdown(
            f"""
            <div style='background: #FFFFFF; border: 1px solid #E6E3DB; border-radius: 10px; padding: 0.85rem 1rem; margin-bottom: 1.25rem; box-shadow: 0 1px 3px rgba(0,0,0,0.02);'>
                <div style='display: flex; align-items: center; gap: 10px; margin-bottom: 0.5rem;'>
                    <div style='width: 32px; height: 32px; border-radius: 50%; background: #EDF5F4; border: 1px solid #D0E5E3; color: #18524B; font-weight: 700; font-size: 0.8rem; display: flex; align-items: center; justify-content: center;'>
                        {initials}
                    </div>
                    <div>
                        <div style='font-size: 0.875rem; font-weight: 700; color: #181D20; line-height: 1.2;'>
                            {user.get('name', 'Mahasiswa')}
                        </div>
                        <div style='font-size: 0.75rem; color: #7A8490;'>
                            {user.get('study_program', 'Informatika')} &bull; Sem {user.get('semester', 5)}
                        </div>
                    </div>
                </div>
                <div style='display: flex; align-items: center; justify-content: space-between; border-top: 1px solid #F1EFEA; padding-top: 0.45rem;'>
                    <span style='font-size: 0.725rem; color: #8B95A0; font-weight: 600; text-transform: uppercase;'>Preferensi</span>
                    <span class='academic-pill pill-tag'>● {dom_pref}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # 3. Navigasi Kustom (Tanpa Radio Bullets)
        def nav_button(label: str, target: str, icon: str):
            is_active = (curr_page == target)
            btn_label = f"{icon}  {label}"
            if st.button(
                btn_label,
                key=f"nav_{target}",
                type="primary" if is_active else "secondary",
                use_container_width=True,
            ):
                if st.session_state.current_page != target:
                    st.session_state.current_page = target
                    st.rerun()

        st.markdown("<div class='sidebar-section-title'>Ruang Kerja</div>", unsafe_allow_html=True)
        nav_button("Dashboard", "Dashboard", "📊")
        nav_button("Tugas Kuliah", "Tugas", "📋")
        nav_button("Rancang Jadwal", "Rencana", "🗓️")

        st.markdown("<div class='sidebar-section-title'>Sistem Studi</div>", unsafe_allow_html=True)
        nav_button("Katalog Strategi", "Strategi", "💡")
        nav_button("AI Selaras", "AI Selaras", "💬")

        st.markdown("<div class='sidebar-section-title'>Evaluasi & Akun</div>", unsafe_allow_html=True)
        nav_button("Refleksi Mingguan", "Refleksi", "📖")
        nav_button("Profil & Pengaturan", "Profil", "👤")
        nav_button("Tes Preferensi", "Tes Preferensi", "🧭")

        st.markdown("<div class='sidebar-section-title'>Informasi</div>", unsafe_allow_html=True)
        nav_button("Beranda", "Landing", "🏠")

        # 4. Footer Sidebar
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        st.markdown(
            """
            <div style='font-size: 0.725rem; color: #9AA3AF; line-height: 1.45; border-top: 1px solid #E6E3DB; padding-top: 0.85rem;'>
                <strong>SelarasBelajar.Lab</strong> &bull; v1.2 Editorial<br>
                Core: <code>planner</code> &bull; <code>scheduler</code> &bull; <code>verifier (RB-05)</code>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ==========================================
    # ROUTING HALAMAN
    # ==========================================
    page = st.session_state.current_page

    if page == "Landing":
        render_landing()
    elif page == "Tes Preferensi":
        render_test_vark()
    elif page == "Hasil Preferensi":
        render_result_vark()
    elif page == "Dashboard":
        render_dashboard()
    elif page == "Tugas":
        render_tasks()
    elif page == "Rencana":
        render_planner()
    elif page == "Strategi":
        render_strategies()
    elif page == "AI Selaras":
        render_ai_assistant()
    elif page == "Profil":
        render_profile()
    elif page == "Refleksi":
        render_reflection()
    else:
        render_dashboard()


if __name__ == "__main__":
    main()
