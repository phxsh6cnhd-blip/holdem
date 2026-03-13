import streamlit as st
from streamlit_autorefresh import st_autorefresh
import time

st.set_page_config(page_title="holdem", layout="centered")

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

# --- GGpoker 스타일 커스텀 CSS ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .poker-container {
        position: relative;
        width: 100%;
        height: 450px;
        background: radial-gradient(circle, #2a623d 0%, #1a3c26 100%);
        border: 12px solid #3d2b1f;
        border-radius: 200px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        box-shadow: inset 0 0 50px #000;
    }
    .pot-display {
        font-size: 24px;
        font-weight: bold;
        color: #ffd700;
        margin-bottom: 20px;
    }
    .player-area {
        position: absolute;
        width: 140px;
        text-align: center;
        background: rgba(0,0,0,0.8);
        padding: 10px;
        border-radius: 15px;
        border: 2px solid #555;
    }
    .p0 { top: 20px; left: 50%; transform: translateX(-50%); } /* Player 1 위쪽 */
    .p1 { bottom: 20px; left: 50%; transform: translateX(-50%); } /* Player 2 아래쪽 */
    .active-turn { border-color: #00ff00; box-shadow: 0 0 15px #00ff00; }
    .card-style { font-size: 40px; margin-top: 5px; }
    </style>
    """, unsafe_allow_html=True)

# 역할 선택 로직 (생략 방지)
if st.session_state.my_role is None:
    st.title("Hold'em 역할 선택")
    c1, c2 = st.columns(2)
    if c1.button("Player 1 (SB)"): st.session_state.my_role = 0; st.rerun()
    if c2.button("Player 2 (BB)"): st.session_state.my_role = 1; st.rerun()
    st.stop()

# --- 메인 게임 화면 ---
st.title("♠️ holdem")

# 테이블 렌더링 (HTML)
table_html = f"""
<div class="poker-container">
    <div class="pot-display">💰 POT: {game['pot']} BB</div>
"""

for i, p in enumerate(game['players']):
    active_class = "active-turn" if game['current_turn'] == i else ""
    # 카드 표시 로직: 본인이면 앞면, 아니면 뒷면
    if st.session_state.my_role == i:
        display_cards = "🂡 🂱" # 나중에 game['players'][i]['cards']로 연동
    else:
        display_cards = "🂠 🂠"
        
    table_html += f"""
    <div class="player-area p{i} {active_class}">
        <div style="color:white; font-size:14px;">{p['nickname']} ({p['pos']})</div>
        <div class="card-style">{display_cards}</div>
        <div style="color:#ffd700; font-weight:bold;">{p['stack']} BB</div>
    </div>
    """
table_html += "</div>"
st.markdown(table_html, unsafe_allow_html=True)

# --- 액션 버튼 (SB, BB 공통 적용) ---
if game['game_status'] == "PLAYING":
    if game['current_turn'] == st.session_state.my_role:
        st.success("당신의 차례입니다!")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("❌ FOLD", use_container_width=True):
                game['current_turn'] = (game['current_turn'] + 1) % 2
                st.rerun()
        with col2:
            if st.button("✅ CHECK/CALL", use_container_width=True):
                game['current_turn'] = (game['current_turn'] + 1) % 2
                st.rerun()
        with col3:
            # SB와 BB 모두에게 Raise(All-in) 버튼이 보이도록 보장
            if st.button("🔥 RAISE (ALL-IN)", type="primary", use_container_width=True):
                me = game['players'][st.session_state.my_role]
                game['pot'] += me['stack']
                me['stack'] = 0
                game['current_turn'] = (game['current_turn'] + 1) % 2
                st.rerun()
    else:
        st.info("상대방의 액션을 기다리고 있습니다...")

# 0BB 종료 체크
if any(p['stack'] <= 0 for p in game['players']):
    game['game_status'] = "FINISHED"
    st.error("게임 종료! 0BB 플레이어 발생.")
    if st.button("Regame"):
        game['pot'] = 0
        game['current_turn'] = 0
        game['game_status'] = "PLAYING"
        for p in game['players']: p['stack'] = 100
        st.rerun()
