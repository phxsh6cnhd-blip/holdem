import streamlit as st
from streamlit_autorefresh import st_autorefresh
import random
import time

# 1. 페이지 설정
st.set_page_config(page_title="holdem", layout="centered")

# 2. 게임 엔진 데이터 (공유 저장소)
@st.cache_resource
def get_game_manager():
    # 초기 덱 생성 및 셔플
    ranks = '23456789TJQKA'
    suits = '♠♥♦♣'
    deck = [r + s for r in ranks for s in suits]
    random.shuffle(deck)
    
    p1_cards = [deck.pop(), deck.pop()]
    p2_cards = [deck.pop(), deck.pop()]
    
    return {
        "stage": "PREFLOP",
        "pot": 1.5,
        "current_bet": 1.0,
        "current_turn": 0, # 0: SB(P1), 1: BB(P2)
        "community_cards": [],
        "deck": deck,
        "players": [
            {"id": 0, "nickname": "Player 1", "stack": 99.5, "pos": "SB", "cards": p1_cards},
            {"id": 1, "nickname": "Player 2", "stack": 99.0, "pos": "BB", "cards": p2_cards}
        ],
        "game_status": "PLAYING",
        "winner_log": ""
    }

# 데이터 불러오기 및 새로고침 설정
game = get_game_manager()
st_autorefresh(interval=1000, key="global_refresh")

# 역할 선택 세션 초기화
if "my_role" not in st.session_state:
    st.session_state.my_role = None

# 3. 주요 게임 로직 함수
def process_next_stage():
    """다음 스트리트로 이동하거나 쇼다운을 진행합니다."""
    if game["stage"] == "PREFLOP":
        game["stage"] = "FLOP"
        game["community_cards"] = [game["deck"].pop() for _ in range(3)]
    elif game["stage"] == "FLOP":
        game["stage"] = "TURN"
        game["community_cards"].append(game["deck"].pop())
    elif game["stage"] == "TURN":
        game["stage"] = "RIVER"
        game["community_cards"].append(game["deck"].pop())
    elif game["stage"] == "RIVER":
        game["stage"] = "SHOWDOWN"
        determine_winner()
    
    game["current_bet"] = 0
    # 포스트플랍에서는 BB(Player 2, index 1)가 먼저 액션하는 것이 일반적 룰
    game["current_turn"] = 1 

def determine_winner(fold_winner_id=None):
    """승자를 판정하고 팟을 지급합니다."""
    if fold_winner_id is not None:
        winner = game["players"][fold_winner_id]
        game["winner_log"] = f"상대방 폴드! {winner['nickname']} 승리"
    else:
        # 자동 족보 계산 로직 (임시 랜덤)
        winner = random.choice(game["players"])
        game["winner_log"] = f"쇼다운 결과 {winner['nickname']} 승리!"
    
    winner["stack"] += game["pot"]
    game["game_status"] = "FINISHED"

# 4. CSS (디자인 오류 수정본)
# 텍스트 노출 방지를 위해 스타일 시트를 확실하게 선언
st.markdown("""
<style>
    .poker-table {
        position: relative; width: 100%; height: 400px;
        background: radial-gradient(circle, #2a623d 0%, #1a3c26 100%);
        border: 10px solid #3d2b1f; border-radius: 200px;
        margin: 40px 0; display: flex; flex-direction: column; align-items: center; justify-content: center;
        z-index: 1;
    }
    .player-box {
        position: absolute; width: 140px; background: rgba(0,0,0,0.9);
        border: 2px solid #555; border-radius: 15px; padding: 10px; text-align: center; color: white;
    }
    .p0 { top: -30px; left: 50%; transform: translateX(-50%); }
    .p1 { bottom: -30px; left: 50%; transform: translateX(-50%); }
    .active-glow { border-color: #00ff00; box-shadow: 0 0 15px #00ff00; }
    .community-area { display: flex; gap: 8px; margin-top: 15px; }
    .poker-card { background: white; color: black; padding: 5px 8px; border-radius: 5px; font-weight: bold; font-size: 22px; min-width: 40px; text-align: center; }
</style>
""", unsafe_allow_html=True)

# 5. UI 렌더링
st.title("♠️ holdem heads-up")

if st.session_state.my_role is None:
    st.subheader("본인의 플레이어 번호를 선택하세요")
    c1, c2 = st.columns(2)
    if c1.button("Player 1 (SB)"):
        st.session_state.my_role = 0
        st.rerun()
    if c2.button("Player 2 (BB)"):
        st.session_state.my_role = 1
        st.rerun()
    st.stop()

# 카드 노출 로직 수정
p0_c = " ".join(game['players'][0]['cards']) if st.session_state.my_role == 0 or game["stage"] == "SHOWDOWN" else "🂠 🂠"
p1_c = " ".join(game['players'][1]['cards']) if st.session_state.my_role == 1 or game["stage"] == "SHOWDOWN" else "🂠 🂠"

# 테이블 HTML 렌더링 (구조적 오류 수정)
table_html = f"""
<div class="poker-table">
    <div style="color: #ffd700; font-size: 24px; font-weight: bold; margin-bottom: 10px;">💰 POT: {game['pot']} BB</div>
    <div class="community-area">
        {" ".join([f'<div class="poker-card">{c}</div>' for c in game['community_cards']]) if game['community_cards'] else '<div style="color:white; opacity:0.3;">커뮤니티 카드 대기 중</div>'}
    </div>
    <div class="player-box p0 {"active-glow" if game['current_turn']==0 else ""}">
        <div style="font-size: 12px; opacity:0.7;">Player 1 (SB)</div>
        <div style="font-size: 26px; margin: 5px 0;">{p0_c}</div>
        <div style="color: gold;">{game['players'][0]['stack']} BB</div>
    </div>
    <div class="player-area p1" style="display:none;"></div> <div class="player-box p1 {"active-glow" if game['current_turn']==1 else ""}">
        <div style="font-size: 12px; opacity:0.7;">Player 2 (BB)</div>
        <div style="font-size: 26px; margin: 5px 0;">{p1_c}</div>
        <div style="color: gold;">{game['players'][1]['stack']} BB</div>
    </div>
</div>
"""
st.markdown(table_html, unsafe_allow_html=True)

# 6. 액션 컨트롤 로직 검토
if game["game_status"] == "PLAYING":
    if st.session_state.my_role == game["current_turn"]:
        st.success("✨ 당신의 차례입니다!")
        me = game["players"][st.session_state.my_role]
        
        c1, c2, c3 = st.columns(3)
        if c1.button("❌ FOLD", use_container_width=True):
            determine_winner(fold_winner_id=(1 - st.session_state.my_role))
            st.rerun()
        
        # 콜/체크 버튼: 현재 베팅이 0이면 체크, 있으면 콜
        call_label = "✅ CHECK" if game["current_bet"] == 0 else f"✅ CALL ({game['current_bet']}BB)"
        if c2.button(call_label, use_container_width=True):
            game["pot"] += game["current_bet"]
            me["stack"] -= game["current_bet"]
            process_next_stage()
            st.rerun()

        # 레이즈 섹션
        if me["stack"] > 0:
            st.divider()
            min_r = min(game["current_bet"] * 2 if game["current_bet"] > 0 else 2.0, me["stack"])
            raise_val = st.slider("Raise 금액 설정", float(min_r), float(me["stack"]), float(min_r), step=0.5)
            if st.button(f"⬆️ RAISE to {raise_val} BB", type="primary", use_container_width=True):
                game["pot"] += raise_val
                me["stack"] -= raise_val
                game["current_bet"] = raise_val
                game["current_turn"] = (1 - game["current_turn"])
                st.rerun()
    else:
        st.info("⌛ 상대방의 액션을 기다리고 있습니다...")
else:
    st.warning(game["winner_log"])
    if st.button("다음 게임 시작 (Reset)", use_container_width=True):
        st.cache_resource.clear() # 캐시 초기화로 새 게임 생성
        st.rerun()
