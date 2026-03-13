import streamlit as st
from streamlit_autorefresh import st_autorefresh
import time

st.set_page_config(page_title="holdem", layout="centered")

# 1. 공유 데이터 매니저
@st.cache_resource
def get_game_manager():
    return {
        "pot": 1.5, # SB(0.5) + BB(1.0) 시작
        "current_bet": 1.0, 
        "current_turn": 0, # SB부터 액션 시작 (프리플랍 기준)
        "players": [
            {"id": 0, "nickname": "Player 1", "stack": 99.5, "pos": "SB", "cards": "🂡 🂱"},
            {"id": 1, "nickname": "Player 2", "stack": 99.0, "pos": "BB", "cards": "🃁 🃑"}
        ],
        "game_status": "PLAYING"
    }

game = get_game_manager()
st_autorefresh(interval=1000, key="global_refresh")

if "my_role" not in st.session_state:
    st.session_state.my_role = None

# 2. GGpoker 스타일 CSS
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; }
    .poker-table-container {
        position: relative;
        width: 100%;
        height: 400px;
        background: radial-gradient(circle, #2a623d 0%, #1a3c26 100%);
        border: 12px solid #3d2b1f;
        border-radius: 200px;
        margin: 50px 0;
        display: flex; justify-content: center; align-items: center;
        box-shadow: inset 0 0 50px #000;
    }
    .pot-info { font-size: 28px; font-weight: bold; color: #ffd700; text-shadow: 2px 2px 4px #000; }
    .player-area {
        position: absolute; width: 140px; background: rgba(0,0,0,0.85);
        border: 2px solid #555; border-radius: 15px; padding: 10px; text-align: center; color: white;
    }
    .p0 { top: -40px; left: 50%; transform: translateX(-50%); }
    .p1 { bottom: -40px; left: 50%; transform: translateX(-50%); }
    .active-turn { border-color: #00ff00; box-shadow: 0 0 15px #00ff00; }
    .card-style { font-size: 45px; line-height: 1; margin: 5px 0; font-family: "Segoe UI Emoji"; }
    </style>
    """, unsafe_allow_html=True)

# 3. 역할 선택
if st.session_state.my_role is None:
    st.title("♠️ holdem - 접속")
    c1, c2 = st.columns(2)
    if c1.button("Player 1 (SB) 접속"): st.session_state.my_role = 0; st.rerun()
    if c2.button("Player 2 (BB) 접속"): st.session_state.my_role = 1; st.rerun()
    st.stop()

# 4. 게임 화면 렌더링
st.title("♠️ holdem")

active_p0 = "active-turn" if game['current_turn'] == 0 else ""
active_p1 = "active-turn" if game['current_turn'] == 1 else ""

# 카드 렌더링 로직 (수정됨)
p0_display = game['players'][0]['cards'] if st.session_state.my_role == 0 else "🂠 🂠"
p1_display = game['players'][1]['cards'] if st.session_state.my_role == 1 else "🂠 🂠"

table_html = f"""
<div class="poker-table-container">
    <div class="pot-info">💰 {game['pot']} BB</div>
    <div class="player-area p0 {active_p0}">
        <div style="font-size:12px; opacity:0.8;">Player 1 (SB)</div>
        <div class="card-style">{p0_display}</div>
        <div style="color:#ffd700; font-weight:bold;">{game['players'][0]['stack']} BB</div>
    </div>
    <div class="player-area p1 {active_p1}">
        <div style="font-size:12px; opacity:0.8;">Player 2 (BB)</div>
        <div class="card-style">{p1_display}</div>
        <div style="color:#ffd700; font-weight:bold;">{game['players'][1]['stack']} BB</div>
    </div>
</div>
"""
st.markdown(table_html, unsafe_allow_html=True)

# 5. 액션 버튼
if game['game_status'] == "PLAYING":
    if game['current_turn'] == st.session_state.my_role:
        st.success("✨ 당신의 차례입니다!")
        me = game['players'][st.session_state.my_role]
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("❌ FOLD", use_container_width=True):
                game['current_turn'] = (game['current_turn'] + 1) % 2
                st.rerun()
        with c2:
            # 콜 금액 계산: 현재 베팅 기준에 맞춰 부족한 만큼만 차감
            call_amount = game['current_bet'] 
            if st.button(f"✅ CALL ({call_amount}BB)", use_container_width=True):
                game['pot'] += call_amount
                me['stack'] -= call_amount
                game['current_turn'] = (game['current_turn'] + 1) % 2
                st.rerun()

        st.divider()
        # 최소 레이즈는 현재 판 베팅의 2배
        min_raise = min(game['current_bet'] * 2, me['stack'])
        max_raise = me['stack']

        if me['stack'] > 0:
            raise_val = st.slider("Raise Amount", float(min_raise), float(max_raise), float(min_raise), step=0.5)
            btn_label = "🔥 ALL-IN" if raise_val == max_raise else f"⬆️ RAISE to {raise_val} BB"
            if st.button(btn_label, type="primary", use_container_width=True):
                game['pot'] += raise_val
                me['stack'] -= raise_val
                game['current_bet'] = raise_val
                game['current_turn'] = (game['current_turn'] + 1) % 2
                st.rerun()
    else:
        st.info("⌛ 상대방의 액션을 기다리고 있습니다...")

# 6. 종료 처리
if any(p['stack'] <= 0 for p in game['players']):
    game['game_status'] = "FINISHED"
    st.error("게임 종료! 0BB 플레이어가 발생했습니다.")
    if st.button("Regame"):
        game['pot'] = 1.5
        game['current_turn'] = 0
        game['game_status'] = "PLAYING"
        game['current_bet'] = 1.0
        game['players'][0]['stack'] = 99.5
        game['players'][1]['stack'] = 99.0
        st.rerun()
