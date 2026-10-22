if st.session_state.lang == "CZ":
            st.page_link("Dashboard.py", label="🏠 Hlavní Dashboard")
            st.page_link("pages/1_Insider_4F.py", label="🧛 Insider Tracker (4F)")
            st.page_link("pages/2_SEC_13F_Radar.py", label="🏛️ SEC 13F Radar")
            st.page_link("pages/3_Terminal.py", label="📊 Terminal")
            st.page_link("pages/4_Opcni_Radar.py", label="🎲 Opční Radar")
            st.page_link("pages/5_COT_Reporty.py", label="🏛️ COT Reporty")
            st.page_link("pages/6_Makro.py", label="🌍 Makro & Rizika")
            
            # Pokud ještě máš Aktualizace, musí mít jiné číslo, např. 7:
            # st.page_link("pages/7_Aktualizace.py", label="🗄️ Aktualizace Dat")
        else:
            st.page_link("Dashboard.py", label="🏠 Main Dashboard")
            st.page_link("pages/1_Insider_4F.py", label="🧛 Insider Tracker (4F)")
            st.page_link("pages/2_SEC_13F_Radar.py", label="🏛️ SEC 13F Radar")
            st.page_link("pages/3_Terminal.py", label="📊 Terminal")
            st.page_link("pages/4_Opcni_Radar.py", label="🎲 Options Radar")
            st.page_link("pages/5_COT_Reporty.py", label="🏛️ COT Reports")
            st.page_link("pages/6_Makro.py", label="🌍 Macro & Risks")
            
            # st.page_link("pages/7_Aktualizace.py", label="🗄️ Data Update")