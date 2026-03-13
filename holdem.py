import streamlit as st
from streamlit_autorefresh import st_autorefresh
import time

# 1. 사이트 기본 설정
st.set_page_config(page_title="holdem", layout="centered")

# 2. 전역 공유 데이터 설정 (모든 유저가 이 데이터를 공유함)
@st.cache_resource
def get_game_manager():
    return {
        "pot": 0,
        "current_turn": 0, # 0: Player 1, 1: Player 2
        "players": [
            {"id": 0, "nickname": "Player 1", "stack": 100, "cards": ["🂡", "🂱"], "pos": "SB"},
            {"id": 1, "nickname": "Player 2", "stack": 100, "cards": ["🃁", "🃑"], "pos": "BB"}
        ],
        "game_status": "PLAYING",
        "last_update": time.time()
    }

game = get_game_manager()

# 3. 개별 세션 설정 (접속자 본인이 누구인지 저장)
if "my_role" not in st.session_state:
    st.session_state.my_role = None # 아직 역할 선택 전

# 자동 새로고침 (실시간 동기화를 위해 필수)
st_autorefresh(interval=1000, key="global_refresh")

# --- UI 스타일 ---
st.markdown("""
    <style>
    .poker-table { background-color: #1a4a1a; border: 8px solid #3d2b1f; border-radius: 150px; 
                   padding: 40px; text-align: center; color: white; margin-bottom: 20px; }
    .player-card { background: rgba(0,0,0,0.7); padding: 10px; border-radius: 10px; border: 1px solid gold; }
    .my-turn { border: 3px solid #00ff00 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 메인 로직 ---
st.title("♠️ Hold'em Online")

# A. 역할 선택 (로그인)
if st.session_state.my_role is None:
    st.subheader("플레이어를 선택하세요")
    col1, col2 = st.columns(2)
    if col1.button("Player 1으로 참여"):
        st.session_state.my_role = 0
        st.rerun()
    if col2.button("Player 2으로 참여"):
        st.session_state.my_role = 1
        st.rerun()
    st.stop()

# B. 게임 종료 체크
if any(p['stack'] <= 0 for p in game['players']):
    game['game_status'] = "FINISHED"

if game['game_status'] == "FINISHED":
    winner = max(game['players'], key=lambda x: x['stack'])
    st.balloons()
    st.error(f"🏆 최종 승자: {winner['nickname']} 🏆")
    if st.button("Regame (모두 초기화)"):
        game['pot'] = 0
        game['current_turn'] = 0
        game['game_status'] = "PLAYING"
        for p in game['players']: p['stack'] = 100
        st.rerun()

else:
    # C. 테이블 레이아웃
    st.markdown('<div class="poker-table">', unsafe_allow_html=True)
    st.write(f"### 💰 TOTAL POT: {game['pot']} BB")
    
    c1, c2 = st.columns(2)
    for i, p in enumerate(game['players']):
        with [c1, c2][i]:
            # 내 순서일 때 강조 표시
            is_turn = "my-turn" if game['current_turn'] == i else ""
            st.markdown(f"<div class='player-card {is_turn}'>", unsafe_allow_html=True)
            st.write(f"**{p['nickname']}** ({p['pos']})")
            
            # 본인 카드만 공개, 상대 카드는 뒷면 (GGpoker 방식)
            if st.session_state.my_role == i:
                st.write(f"🂡 🂱") # 실제로는 p['cards'] 연동
                st.write(" (내 카드) ")
            else:
                st.write("🂠 🂠")
                st.write(" (상대 카드) ")
                
            st.write(f"스택: {p['stack']} BB")
            st.markdown("</div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # D. 액션 버튼 (내 차례일 때만 활성화)
    if game['current_turn'] == st.session_state.my_role:
        st.success("✨ 당신의 차례입니다!")
        col_f, col_c, col_r = st.columns(3)
        
        if col_f.button("❌ FOLD"):
            game['current_turn'] = (game['current_turn'] + 1) % 2
            st.rerun()
            
        if col_c.button("✅ CHECK/CALL"):
            game['current_turn'] = (game['current_turn'] + 1) % 2
            st.rerun()
            
        if col_r.button("🔥 ALL-IN", type="primary"):
            me = game['players'][st.session_state.my_role]
            game['pot'] += me['stack']
            me['stack'] = 0
            game['current_turn'] = (game['current_turn'] + 1) % 2
            st.rerun()
    else:
        st.info(f"⌛ 상대방({game['players'][game['current_turn']]['nickname']})의 결정을 기다리고 있습니다...")

# 사이드바 정보
with st.sidebar:
    st.write(f"당신은 **Player {st.session_state.my_role + 1}** 입니다.")
    if st.button("역할 초기화"):
        st.session_state.my_role = None
        st.rerun()
