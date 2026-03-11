import streamlit as st
import random
from streamlit_autorefresh import st_autorefresh

# 1. 페이지 설정
st.set_page_config(page_title="Revo 홀덤 클럽", layout="centered")
st_autorefresh(interval=2000, key="poker_refresh")

# CSS: 사진 같은 테이블 UI & 버튼 시인성 강화
st.markdown("""
    <style>
    .stApp { background-color: #0b0d10; color: #ffffff; }
    
    /* 홀덤 테이블 스타일 (입체감 부여) */
    .poker-table {
        background: radial-gradient(circle, #1a472a 0%, #0d2616 100%);
        border: 10px solid #3d2b1f; border-radius: 150px;
        padding: 60px 20px; text-align: center; position: relative;
        box-shadow: inset 0 0 50px #000, 0 10px 20px rgba(0,0,0,0.5);
        margin-bottom: 30px;
    }

    /* 카드 디자인 (흰색 바탕 + 테두리) */
    .card {
        background-color: #ffffff !important; 
        color: #000000 !important;
        width: 65px; height: 90px; 
        display: inline-block;
        border-radius: 8px; 
        margin: 5px; 
        line-height: 90px;
        font-size: 1.8em; 
        font-weight: bold; 
        border: 2px solid #555;
        box-shadow: 2px 2px 8px rgba(0,0,0,0.8);
        text-align: center;
    }
    .card-back {
        background: linear-gradient(135deg, #2c3e50 25%, #34495e 25%, #34495e 50%, #2c3e50 50%, #2c3e50 75%, #34495e 75%, #34495e 100%);
        background-size: 10px 10px;
        width: 65px; height: 90px; 
        display: inline-block;
        border-radius: 8px; 
        margin: 5px; 
        border: 2px solid #fff;
        box-shadow: 2px 2px 8px rgba(0,0,0,0.8);
    }
    .red { color: #e74c3c !important; } /* 하트, 다이아는 빨간색 */
    
    /* 버튼 스타일 (아이폰에서도 글자 잘 보이게) */
    div.stButton > button {
        background-color: #2d2d2d !important;
        color: #ffffff !important;
        border: 2px solid #444 !important;
        border-radius: 10px !important;
        height: 3.5em !important;
        font-size: 1.1em !important;
        font-weight: 800 !important;
        box-shadow: 0 4px #1a1a1a !important;
    }
    div.stButton > button:active {
        box-shadow: 0 0 #1a1a1a !important;
        transform: translateY(4px);
    }
    div.stButton > button:disabled {
        background-color: #111 !important;
        color: #333 !important;
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_resource
def get_game_server():
    return {
        "players": {}, # {닉네임: {"hand": [], "bb": 100.0}}
        "board": [], "pot": 0.0, "btn_idx": 0, "current_turn_idx": 0,
        "is_allin": False, "last_action": "입장해 주세요", "game_status": "WAITING", "deck": []
    }

server = get_game_server()

def render_card(card_str):
    if not card_str: return ""
    is_red = any(s in card_str for s in ['♥', '♦'])
    color_class = "red" if is_red else ""
    return f"<div class='card {color_class}'>{card_str}</div>"

# --- 메인 로직 ---
if "my_name" not in st.session_state:
    st.title("♣️ REVO HOLDEM")
    with st.form("join"):
        name = st.text_input("닉네임 입력").strip()
        if st.form_submit_button("테이블 앉기"):
            if name and name not in server["players"]:
                server["players"][name] = {"hand": [], "bb": 100.0}
                st.session_state.my_name = name; st.rerun()
else:
    my_name = st.session_state.my_name
    p_names = list(server["players"].keys())
    if my_name not in server["players"]: st.session_state.clear(); st.rerun()
    
    my_info = server["players"][my_name]
    is_host = p_names[0] == my_name

    # --- 테이블 UI 상단 ---
    st.markdown("<div class='poker-table'>", unsafe_allow_html=True)
    if server["game_status"] == "PLAYING":
        # 보드 카드 출력
        board_html = "".join([render_card(c) for c in server["board"]]) if server["board"] else "<h3 style='opacity:0.5;'>PRE-FLOP</h3>"
        st.markdown(board_html, unsafe_allow_html=True)
        st.markdown(f"<div style='margin-top:20px;'><span style='color:#ffeb3b; font-size:2em; font-weight:bold;'>{server['pot']:.1f} BB</span></div>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:#aaa; font-size:0.9em;'>{server['last_action']
