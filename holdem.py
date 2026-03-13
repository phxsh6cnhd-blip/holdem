import streamlit as st
from streamlit_autorefresh import st_autorefresh
import time

# 1. 페이지 설정
st.set_page_config(page_title="holdem", layout="centered")

# 2. 공유 데이터 매니저 (서버 메모리에 저장)
@st.cache_resource
def get_game_manager():
    return {
        "pot": 0,
        "current_turn": 0,
        "players": [
            {"id": 0, "nickname": "Player 1", "stack": 100, "cards": ["🂡", "🂱"], "pos": "SB"},
            {"id": 1, "nickname": "Player 2", "stack": 100, "cards": ["🃁", "🃑"], "pos": "BB"}
        ],
        "game_status": "PLAYING"
    }

game = get_game_manager()
st_autorefresh(interval=1000, key="global_refresh")

if "my_role" not in st.session_state:
    st.session_state.my_role = None

# 3. GGpoker 스타일 CSS
st.markdown("""
    <style>
    /* 전체 배경 */
    .stApp { background-color: #0e1117; }
    
    /* 테이블 컨테이너 (부모) */
    .poker-table-container {
        position: relative;
        width: 100%;
        height: 500px; /* 테이블 높이 */
        background: radial-gradient(circle, #2a623d 0%, #1a3c26 100%);
        border: 15px solid #3d2b1f;
        border-radius: 250px; /* 타원형 */
        margin: 0 auto;
        box-shadow: inset 0 0 100px #000;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    
    /* 중앙 팟 표시 */
    .pot-info {
        font-size: 32px;
        font-weight: bold;
        color: #ffd700;
        text-shadow: 2px 2px 4px #000;
    }

    /* 플레이어 영역 (공통) */
    .player-area {
        position: absolute;
        width: 150px;
        background: rgba(0,0,0,0.85);
        border: 2px solid #555;
        border-radius: 15px;
        padding: 10px;
        text-align: center;
        color: white;
        transition: all 0.3s;
    }

    /* Player 1 위치 (상단) */
    .p0 { top: -25px; left: 50%; transform: translateX(-50%); }
    
    /* Player 2 위치 (하단) */
    .p1 { bottom: -25px; left: 50%; transform: translateX(-50%); }

    /* 현재 차례 강조 */
    .active-turn {
        border-color: #00ff00;
        box-shadow: 0 0 20px #00ff00;
    }

    /* 카드 스타일 */
    .card-style {
        font-size: 45px;
        line-height: 1.2;
        margin: 5px 0;
    }
    </style>
    """, unsafe_allow_html=True)

# 4. 역할 선택 화면
if st.session_state.my_role is None:
    st.title("Hold'em 역할 선택")
    col1, col2 = st.columns(2)
    if col1.button("Player 1 (SB)"): st.session_state.my_role = 0; st.rerun()
    if col2.button("Player 2 (BB)"): st.session_state.my_role = 1; st.rerun()
    st.stop()

# 5. 메인 게임 화면
st.title("♠️ holdem")

# HTML 테이블 렌더링
active_p0 = "active-turn" if game['current_turn'] == 0 else ""
active_p1 = "active-turn" if game['current_turn'] == 1 else ""

# 본인 역할에 따른 카드 공개/비공개 로직
p0_cards = "🂡 🂱" if st.session_state.my_role == 0 else "🂠 🂠"
p1_cards = "🃁 🃑" if st.session_state.my_role == 1 else "🂠 🂠"

table_html = f"""
<div style="padding: 50px 0;"> <div class="poker-table-container">
        <div class="pot-info">💰 {game['pot']} BB</div>
        
        <div class="player-area p0 {active_p0}">
            <div style="font-size:14px; opacity:0.8;">Player 1 (SB)</div>
            <div class="card-style">{p0_cards}</div>
            <div style="color:#ffd700; font-weight:bold;">{game['players'][0]['stack']} BB</div>
        </div>
        
        <div class="player-area p1 {active_p1}">
            <div style="font-size:14px; opacity:0.8;">Player 2 (BB)</div>
            <div class="card-style">{p1_cards}</div>
            <div style="color:#ffd700; font-weight:bold;">{game['players'][1]['stack']} BB</div>
        </div>
    </div>
</div>
"""
st.markdown(table_html, unsafe_allow_html=True)

# 6. 액션 컨트롤 (내 차례일 때만)
if game['game_status'] == "PLAYING":
    if game['current_turn'] == st.session_state.my_role:
        st.success("당신의 차례입니다!")
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
        st.info("상대방의 액션을 기다리는 중...")
