import streamlit as st
from streamlit_autorefresh import st_autorefresh
import time

# 1. 사이트 기본 설정
st.set_page_config(page_title="holdem", layout="centered")

# 2. 전역 공유 데이터 설정 (모든 유저가 동일한 서버 데이터를 공유)
@st.cache_resource
def get_game_manager():
    return {
        "pot": 0,
        "current_bet": 2, # 현재 라운드에서 콜해야 할 금액 (기본 BB)
        "current_turn": 0, # 0: Player 1 (SB), 1: Player 2 (BB)
        "players": [
            {"id": 0, "nickname": "Player 1", "stack": 100, "pos": "SB", "cards": "🂡 🂱"},
            {"id": 1, "nickname": "Player 2", "stack": 100, "pos": "BB", "cards": "🃁 🃑"}
        ],
        "game_status": "PLAYING"
    }

game = get_game_manager()

# 3. 개별 세션 설정 (접속자가 누구인지 저장)
if "my_role" not in st.session_state:
    st.session_state.my_role = None

# 실시간 동기화를 위한 자동 새로고침 (1초)
st_autorefresh(interval=1000, key="global_refresh")

# 4. GGpoker 스타일 CSS
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
    .p0 { top: -40px; left: 50%; transform: translateX(-50%); } /* 위쪽 */
    .p1 { bottom: -40px; left: 50%; transform: translateX(-50%); } /* 아래쪽 */
    .active-turn { border-color: #00ff00; box-shadow: 0 0 15px #00ff00; }
    .card-style { font-size: 40px; line-height: 1; margin: 5px 0; }
    </style>
    """, unsafe_allow_html=True)

# 5. 역할 선택 (로그인)
if st.session_state.my_role is None:
    st.title("♠️ holdem - 접속")
    c1, c2 = st.columns(2)
    if c1.button("Player 1 (SB) 선택"): st.session_state.my_role = 0; st.rerun()
    if c2.button("Player 2 (BB) 선택"): st.session_state.my_role = 1; st.rerun()
    st.stop()

# 6. 메인 게임 화면 렌더링
st.title("♠️ holdem")

# HTML 테이블 그리기
active_p0 = "active-turn" if game['current_turn'] == 0 else ""
active_p1 = "active-turn" if game['current_turn'] == 1 else ""
p0_cards = game['players'][0]['cards'] if st.session_state.my_role == 0 else "🂠 🂠"
p1_cards = game['players'][1]['cards'] if st.session_state.my_role == 1 else "🂠 🂠"

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
st.markdown(table_html, unsafe_allow_html=True)

# 7. 액션 컨트롤 로직
if game['game_status'] == "PLAYING":
    if game['current_turn'] == st.session_state.my_role:
        st.success("✨ 당신의 차례입니다!")
        
        me = game['players'][st.session_state.my_role]
        
        # 기본 액션 버튼
        c1, c2 = st.columns(2)
        with c1:
            if st.button("❌ FOLD", use_container_width=True):
                game['current_turn'] = (game['current_turn'] + 1) % 2
                st.rerun()
        with c2:
            if st.button("✅ CHECK / CALL", use_container_width=True):
                # 콜 로직: 현재 베팅 금액만큼 스택에서 차감 (단순화)
                game['current_turn'] = (game['current_turn'] + 1) % 2
                st.rerun()

        # 레이즈(No-Limit) 섹션
        st.divider()
        min_raise = min(game['current_bet'] * 2, me['stack'])
        max_raise = me['stack']

        if me['stack'] > 0:
            raise_val = st.slider("Raise Amount (BB)", int(min_raise), int(max_raise), int(min_raise))
            
            btn_label = "🔥 ALL-IN" if raise_val == max_raise else f"⬆️ RAISE to {raise_val} BB"
            if st.button(btn_label, type="primary", use_container_width=True):
                game['pot'] += raise_val
                me['stack'] -= raise_val
                game['current_bet'] = raise_val # 현재 판의 베팅 기준 업데이트
                game['current_turn'] = (game['current_turn'] + 1) % 2
                st.rerun()
    else:
        st.info("⌛ 상대방의 액션을 기다리고 있습니다...")

# 8. 게임 종료 체크
if any(p['stack'] <= 0 for p in game['players']):
    game['game_status'] = "FINISHED"
    st.error("게임 종료! 0BB 플레이어가 발생했습니다.")
    if st.button("Regame"):
        game['pot'] = 0
        game['current_turn'] = 0
        game['game_status'] = "PLAYING"
        for p in game['players']: p['stack'] = 100
        st.rerun()

# 사이드바 설정
with st.sidebar:
    st.write(f"접속 중인 역할: **Player {st.session_state.my_role + 1}**")
    if st.button("역할 초기화"):
        st.session_state.my_role = None
        st.rerun()
