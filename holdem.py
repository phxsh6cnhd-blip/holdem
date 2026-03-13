import streamlit as st
from streamlit_autorefresh import st_autorefresh
import time

# 1. 페이지 설정 (사이트 이름: holdem)
st.set_page_config(page_title="holdem", layout="centered")

# 2. 공유 데이터 매니저 (모든 유저가 이 데이터를 공유함)
@st.cache_resource
def get_game_manager():
    return {
        "pot": 0,
        "current_turn": 0,
        "players": [
            {"id": 0, "nickname": "Player 1", "stack": 100, "pos": "SB"},
            {"id": 1, "nickname": "Player 2", "stack": 100, "pos": "BB"}
        ],
        "game_status": "PLAYING"
    }

game = get_game_manager()
st_autorefresh(interval=1000, key="global_refresh")

if "my_role" not in st.session_state:
    st.session_state.my_role = None

# 3. CSS (여기에 디자인 코드를 다 몰아넣었습니다)
st.markdown("""
    <style>
    .poker-table-container {
        position: relative;
        width: 100%;
        height: 400px;
        background: radial-gradient(circle, #2a623d 0%, #1a3c26 100%);
        border: 12px solid #3d2b1f;
        border-radius: 200px;
        margin: 50px 0;
        display: flex;
        justify-content: center;
        align-items: center;
        box-shadow: inset 0 0 50px #000;
    }
    .pot-info { font-size: 28px; font-weight: bold; color: #ffd700; text-shadow: 2px 2px 4px #000; }
    .player-area {
        position: absolute;
        width: 140px;
        background: rgba(0,0,0,0.85);
        border: 2px solid #555;
        border-radius: 15px;
        padding: 10px;
        text-align: center;
        color: white;
    }
    .p0 { top: -40px; left: 50%; transform: translateX(-50%); } /* Player 1 위 */
    .p1 { bottom: -40px; left: 50%; transform: translateX(-50%); } /* Player 2 아래 */
    .active-turn { border-color: #00ff00; box-shadow: 0 0 15px #00ff00; }
    .card-style { font-size: 40px; line-height: 1; margin: 5px 0; }
    </style>
    """, unsafe_allow_html=True)

# 4. 역할 선택
if st.session_state.my_role is None:
    st.title("♠️ holdem - 접속")
    c1, c2 = st.columns(2)
    if c1.button("Player 1 (SB) 접속"): st.session_state.my_role = 0; st.rerun()
    if c2.button("Player 2 (BB) 접속"): st.session_state.my_role = 1; st.rerun()
    st.stop()

# 5. 게임 화면 출력 (여기가 HTML을 그리는 부분입니다)
st.title("♠️ holdem")

active_p0 = "active-turn" if game['current_turn'] == 0 else ""
active_p1 = "active-turn" if game['current_turn'] == 1 else ""

# 본인 역할에 따른 카드 공개 여부
p0_cards = "🂡 🂱" if st.session_state.my_role == 0 else "🂠 🂠"
p1_cards = "🃁 🃑" if st.session_state.my_role == 1 else "🂠 🂠"

# f-string을 사용해 HTML 구성
table_html = f"""
<div class="poker-table-container">
    <div class="pot-info">💰 {game['pot']} BB</div>
    
    <div class="player-area p0 {active_p0}">
        <div style="font-size:12px; opacity:0.8;">Player 1 (SB)</div>
        <div class="card-style">{p0_cards}</div>
        <div style="color:#ffd700; font-weight:bold;">{game['players'][0]['stack']} BB</div>
    </div>
    
    <div class="player-area p1 {active_p1}">
        <div style="font-size:12px; opacity:0.8;">Player 2 (BB)</div>
        <div class="card-style">{p1_cards}</div>
        <div style="color:#ffd700; font-weight:bold;">{game['players'][1]['stack']} BB</div>
    </div>
</div>
"""
# 중요: unsafe_allow_html=True가 있어야 텍스트가 아닌 디자인으로 보입니다.
st.markdown(table_html, unsafe_allow_html=True)

# 6. 액션 컨트롤 버튼
if game['game_status'] == "PLAYING":
    if game['current_turn'] == st.session_state.my_role:
        st.success("✨ 당신의 차례입니다!")
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("❌ FOLD", use_container_width=True):
                game['current_turn'] = (game['current_turn'] + 1) % 2
                st.rerun()
        with c2:
            if st.button("✅ CHECK/CALL", use_container_width=True):
                game['current_turn'] = (game['current_turn'] + 1) % 2
                st.rerun()
        with c3:
            if st.button("🔥 RAISE (ALL-IN)", type="primary", use_container_width=True):
                me = game['players'][st.session_state.my_role]
                game['pot'] += me['stack']
                me['stack'] = 0
                game['current_turn'] = (game['current_turn'] + 1) % 2
                st.rerun()
    else:
        st.info("⌛ 상대방의 액션을 기다리는 중...")
