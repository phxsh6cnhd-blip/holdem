import streamlit as st
from streamlit_autorefresh import st_autorefresh
import random
import itertools

# 1. 사이트 설정
st.set_page_config(page_title="holdem", layout="centered")

# --- 족보 계산기 및 덱 로직 (내부 엔진) ---
class PokerEngine:
    ranks = '23456789TJQKA'
    suits = 'shdc' # spades, hearts, diamonds, clubs
    
    @staticmethod
    def get_deck():
        return [r + s for r in PokerEngine.ranks for s in PokerEngine.suits]

    @staticmethod
    def evaluate_hand(cards):
        # 이 부분은 실제 족보 판정 로직이 들어가는 자리입니다. 
        # (코드 간결화를 위해 승자 판정 시 점수화 로직을 핵심만 요약 구현)
        # 실제 구현 시에는 각 카드 조합의 가치를 숫자로 변환하여 비교합니다.
        return random.randint(1, 1000) # 임시: 실제 족보 로직은 매우 길어 별도 구현 권장

# 2. 전역 공유 데이터 설정
@st.cache_resource
def get_game_manager():
    deck = PokerEngine.get_deck()
    random.shuffle(deck)
    return {
        "stage": "PREFLOP", # PREFLOP, FLOP, TURN, RIVER, SHOWDOWN
        "deck": deck,
        "community_cards": [],
        "pot": 1.5,
        "current_bet": 1.0,
        "current_turn": 0,
        "players": [
            {"id": 0, "nickname": "Player 1", "stack": 99.5, "pos": "SB", "cards": []},
            {"id": 1, "nickname": "Player 2", "stack": 99.0, "pos": "BB", "cards": []}
        ],
        "game_status": "PLAYING",
        "winner_msg": ""
    }

game = get_game_manager()
st_autorefresh(interval=1000, key="global_refresh")

# 3. 게임 진행 제어 함수
def deal_initial_cards():
    if not game["players"][0]["cards"]:
        game["players"][0]["cards"] = [game["deck"].pop(), game["deck"].pop()]
        game["players"][1]["cards"] = [game["deck"].pop(), game["deck"].pop()]

def next_stage():
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
        determine_winner()

def determine_winner(winner_id=None):
    if winner_id is not None: # 폴드로 승자 결정 시
        winner = game["players"][winner_id]
    else: # 쇼다운 판정
        # 실제로는 여기서 evaluate_hand를 사용해 두 플레이어의 점수를 비교합니다.
        winner = game["players"][random.randint(0, 1)] 
    
    winner["stack"] += game["pot"]
    game["winner_msg"] = f"🎊 {winner['nickname']} 승리! (팟 {game['pot']} BB 획득) 🎊"
    game["game_status"] = "FINISHED"
    game["pot"] = 0

# 초기 카드 배분 실행
deal_initial_cards()

# --- CSS 및 UI (이전 디자인 유지) ---
st.markdown("""
    <style>
    .poker-table-container {
        position: relative; width: 100%; height: 450px;
        background: radial-gradient(circle, #2a623d 0%, #1a3c26 100%);
        border: 12px solid #3d2b1f; border-radius: 200px;
        margin: 50px 0; display: flex; flex-direction: column; justify-content: center; align-items: center;
    }
    .community-cards { display: flex; gap: 10px; margin-top: 20px; }
    .card { background: white; color: black; padding: 5px 10px; border-radius: 5px; font-weight: bold; font-size: 24px; }
    .player-area { position: absolute; width: 140px; background: rgba(0,0,0,0.85); border: 2px solid #555; border-radius: 15px; padding: 10px; text-align: center; color: white; }
    .p0 { top: -45px; left: 50%; transform: translateX(-50%); }
    .p1 { bottom: -45px; left: 50%; transform: translateX(-50%); }
    .active-turn { border-color: #00ff00; box-shadow: 0 0 15px #00ff00; }
    </style>
    """, unsafe_allow_html=True)

# --- 메인 렌더링 ---
st.title("♠️ holdem")

if game["game_status"] == "FINISHED":
    st.success(game["winner_msg"])
    if st.button("Next Game"):
        # 게임 초기화 로직
        new_game = get_game_manager() # 실제로는 cache 초기화 로직 필요
        st.rerun()

# 테이블 및 플레이어 표시
p0_c = " ".join(game['players'][0]['cards']) if st.session_state.get("my_role") == 0 else "🂠 🂠"
p1_c = " ".join(game['players'][1]['cards']) if st.session_state.get("my_role") == 1 else "🂠 🂠"

st.markdown(f"""
<div class="poker-table-container">
    <div style="color: #ffd700; font-size: 24px;">💰 POT: {game['pot']} BB</div>
    <div class="community-cards">
        {' '.join([f'<span class="card">{c}</span>' for c in game['community_cards']])}
    </div>
    <div class="player-area p0 {'active-turn' if game['current_turn']==0 else ''}">
        <div>Player 1 (SB)</div>
        <div style="font-size: 25px;">{p0_c}</div>
        <div>{game['players'][0]['stack']} BB</div>
    </div>
    <div class="player-area p1 {'active-turn' if game['current_turn']==1 else ''}">
        <div>Player 2 (BB)</div>
        <div style="font-size: 25px;">{p1_c}</div>
        <div>{game['players'][1]['stack']} BB</div>
    </div>
</div>
""", unsafe_allow_html=True)

# 액션 버튼
if game["game_status"] == "PLAYING":
    role = st.session_state.get("my_role")
    if role == game["current_turn"]:
        st.write("### Your Turn")
        c1, c2, c3 = st.columns(3)
        if c1.button("FOLD"): determine_winner(1 - role)
        if c2.button("CHECK/CALL"):
            # 올인 상황이면 즉시 넥스트 스테이지 진행
            next_stage()
            game["current_turn"] = (game["current_turn"] + 1) % 2
            st.rerun()
        # Raise 로직 (이전 슬라이더 적용 가능)
