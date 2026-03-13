import streamlit as st
from streamlit_autorefresh import st_autorefresh
import random
import time

# 1. 페이지 및 초기 설정
st.set_page_config(page_title="holdem", layout="centered")

# 2. 게임 엔진 데이터 (공유 저장소)
@st.cache_resource
def get_game_manager():
    return {
        "stage": "PREFLOP", # PREFLOP, FLOP, TURN, RIVER, SHOWDOWN
        "pot": 1.5,
        "current_bet": 1.0,
        "current_turn": 0, # SB(Player 1)가 먼저 액션
        "community_cards": [],
        "deck": [],
        "players": [
            {"id": 0, "nickname": "Player 1", "stack": 99.5, "pos": "SB", "cards": [], "last_action": ""},
            {"id": 1, "nickname": "Player 2", "stack": 99.0, "pos": "BB", "cards": [], "last_action": ""}
        ],
        "game_status": "PLAYING",
        "log": "게임이 시작되었습니다."
    }

game = get_game_manager()
st_autorefresh(interval=1000, key="global_refresh")

# 3. 핵심 게임 함수
def shuffle_and_deal():
    ranks = '23456789TJQKA'
    suits = '♠♥♦♣'
    deck = [r + s for r in ranks for s in suits]
    random.shuffle(deck)
    game["deck"] = deck
    game["players"][0]["cards"] = [game["deck"].pop(), game["deck"].pop()]
    game["players"][1]["cards"] = [game["deck"].pop(), game["deck"].pop()]

def process_next_stage():
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
        auto_determine_winner()
    
    game["current_bet"] = 0 # 스테이지 변경 시 베팅 초기화
    game["current_turn"] = 1 # 헤즈업은 포스트플랍에서 BB가 먼저 액션 (또는 룰에 따라 설정)

def auto_determine_winner(fold_winner_id=None):
    if fold_winner_id is not None:
        winner = game["players"][fold_winner_id]
        game["log"] = f"상대방 폴드! {winner['nickname']} 승리"
    else:
        # 족보 계산 로직이 들어갈 자리 (현재는 단순 랜덤 승자 판정)
        winner = random.choice(game["players"])
        game["log"] = f"쇼다운! {winner['nickname']} 족보 승리"
    
    winner["stack"] += game["pot"]
    game["game_status"] = "FINISHED"

# 초기 카드 배분
if not game["players"][0]["cards"]:
    shuffle_and_deal()

# 4. CSS (디자인)
st.markdown("""
    <style>
    .poker-table {
        position: relative; width: 100%; height: 420px;
        background: radial-gradient(circle, #2a623d 0%, #1a3c26 100%);
        border: 10px solid #3d2b1f; border-radius: 200px;
        margin: 40px 0; display: flex; flex-direction: column; align-items: center; justify-content: center;
    }
    .player-box {
        position: absolute; width: 130px; background: rgba(0,0,0,0.85);
        border: 2px solid #555; border-radius: 12px; padding: 8px; text-align: center; color: white;
    }
    .p0 { top: -35px; left: 50%; transform: translateX(-50%); }
    .p1 { bottom: -35px; left: 50%; transform: translateX(-50%); }
    .active { border-color: #00ff00; box-shadow: 0 0 15px #00ff00; }
    .community { display: flex; gap: 8px; margin-top: 20px; }
    .card { background: white; color: black; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 20px; }
    </style>
    """, unsafe_allow_html=True)

# 5. UI 렌더링
st.title("♠️ holdem heads-up")

if "my_role" not in st.session_state:
    st.subheader("플레이어를 선택하세요")
    c1, c2 = st.columns(2)
    if c1.button("Player 1 (SB)"): st.session_state.my_role = 0; st.rerun()
    if c2.button("Player 2 (BB)"): st.session_state.my_role = 1; st.rerun()
    st.stop()

# 게임 상태 표시
p0_c = " ".join(game['players'][0]['cards']) if st.session_state.my_role == 0 or game["stage"] == "SHOWDOWN" else "🂠 🂠"
p1_c = " ".join(game['players'][1]['cards']) if st.session_state.my_role == 1 or game["stage"] == "SHOWDOWN" else "🂠 🂠"

table_html = f"""
<div class="poker-table">
    <div style="color: #ffd700; font-size: 22px; font-weight: bold;">💰 POT: {game['pot']} BB</div>
    <div class="community">
        {' '.join([f'<div class="card">{c}</div>' for c in game['community_cards']])}
    </div>
    <div class="player-box p0 {'active' if game['current_turn']==0 else ''}">
        <div style="font-size: 11px;">Player 1 (SB)</div>
        <div style="font-size: 24px; margin: 5px 0;">{p0_c}</div>
        <div style="color: gold;">{game['players'][0]['stack']} BB</div>
    </div>
    <div class="player-box p1 {'active' if game['current_turn']==1 else ''}">
        <div style="font-size: 11px;">Player 2 (BB)</div>
        <div style="font-size: 24px; margin: 5px 0;">{p1_c}</div>
        <div style="color: gold;">{game['players'][1]['stack']} BB</div>
    </div>
</div>
"""
st.markdown(table_html, unsafe_allow_html=True)

# 6. 액션 및 스테이지 제어
if game["game_status"] == "PLAYING":
    if st.session_state.my_role == game["current_turn"]:
        st.success("당신의 차례입니다!")
        me = game["players"][st.session_state.my_role]
        
        c1, c2, c3 = st.columns(3)
        if c1.button("❌ FOLD"):
            auto_determine_winner(1 - st.session_state.my_role)
            st.rerun()
        
        if c2.button(f"✅ CALL/CHECK ({game['current_bet']}BB)"):
            game["pot"] += game["current_bet"]
            me["stack"] -= game["current_bet"]
            # 헤즈업은 둘 다 액션을 마쳤을 때 다음 단계로 이동
            process_next_stage()
            st.rerun()

        st.divider()
        if me["stack"] > 0:
            min_r = min(game["current_bet"] * 2, me["stack"])
            raise_val = st.slider("Raise", float(min_r), float(me["stack"]), float(min_r), step=0.5)
            if st.button(f"⬆️ RAISE to {raise_val}"):
                game["pot"] += raise_val
                me["stack"] -= raise_val
                game["current_bet"] = raise_val
                game["current_turn"] = (game["current_turn"] + 1) % 2
                st.rerun()
    else:
        st.info("상대방의 선택을 기다리고 있습니다...")

else:
    st.warning(game["log"])
    if st.button("Next Game (Reset)"):
        # 초기화 (cache_resource이므로 수동 초기화)
        game.update(get_game_manager())
        shuffle_and_deal()
        st.rerun()
