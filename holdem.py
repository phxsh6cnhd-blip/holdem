import streamlit as st
import random
from streamlit_autorefresh import st_autorefresh

# 1. 페이지 설정 및 다크 모드 스타일 UI
st.set_page_config(page_title="헤즈업 챔피언십", layout="centered")

# 2초마다 자동 새로고침 (상대방의 액션을 실시간으로 확인)
st_autorefresh(interval=2000, key="poker_refresh")

st.markdown("""
    <style>
    /* 전체 배경을 어둡게 (눈 보호) */
    .stApp { background-color: #0e1117; color: #ffffff; }
    .stButton>button { width: 100%; border-radius: 10px; font-weight: bold; }
    
    /* 홀덤 테이블 느낌의 UI */
    .poker-table {
        background-color: #1a472a; border: 5px solid #3d2b1f;
        border-radius: 100px; padding: 40px; text-align: center;
        margin-bottom: 20px; border-style: double;
    }
    /* 카드 박스 (다크톤) */
    .card-box {
        background-color: #2d2d2d; color: #ff4b4b;
        padding: 15px; border-radius: 10px;
        border: 2px solid #555; display: inline-block;
        width: 100px; margin: 5px; font-size: 1.5em;
        font-weight: bold;
    }
    .info-text { font-size: 1.1em; color: #aaa; }
    .pot-text { font-size: 1.8em; color: #ffeb3b; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 2. 공유 서버 설정
@st.cache_resource
def get_game_server():
    return {
        "players": {}, # {닉네임: {"hand": [], "bb_left": 100.0, "status": "LIVE"}}
        "board": [], 
        "pot": 0.0, 
        "bb_amount": 2.0, 
        "btn_idx": 0, 
        "current_turn_idx": 0,
        "last_action": "게임을 대기 중입니다.", 
        "game_status": "WAITING", 
        "deck": []
    }

server = get_game_server()

# 3. 로직 함수
def next_turn():
    server["current_turn_idx"] = 1 - server["current_turn_idx"]

# --- 입장 및 세션 체크 ---
if "my_name" not in st.session_state:
    st.title("♠️ 리얼 홀덤 테이블")
    with st.form("entry"):
        name = st.text_input("닉네임").strip()
        if st.form_submit_button("입장"):
            if name and name not in server["players"]:
                server["players"][name] = {"hand": [], "bb_left": 100.0, "status": "LIVE"}
                st.session_state.my_name = name
                st.rerun()
            else:
                st.error("이름을 입력하거나 중복을 확인해줘!")
else:
    my_name = st.session_state.my_name
    p_names = list(server["players"].keys())
    
    if my_name not in server["players"]:
        st.session_state.clear()
        st.rerun()
    
    is_host = p_names[0] == my_name
    my_info = server["players"][my_name]

    # --- 사이드바: 플레이어 정보 ---
    st.sidebar.title("📊 플레이어 정보")
    for p in p_names:
        info = server["players"][p]
        st.sidebar.write(f"**{p}**: {info['bb_left']:.1f} BB")

    if is_host:
        with st.sidebar.expander("🛠 방장 설정"):
            if st.button("♻️ 전체 리셋"):
                server["players"].clear()
                server["game_status"] = "WAITING"
                st.rerun()
            
            if server["game_status"] == "WAITING" and len(p_names) == 2:
                if st.button("🚀 NEXT HAND (Deal)"):
                    suits = ['♠','♥','♦','♣']
                    ranks = ['2','3','4','5','6','7','8','9','10','J','Q','K','A']
                    deck = [r+s for s in suits for r in ranks]
                    random.shuffle(deck)
                    
                    # 프리플랍 세팅 (버튼 교대)
                    server["btn_idx"] = 1 - server["btn_idx"]
                    server["current_turn_idx"] = server["btn_idx"] # 헤즈업: BTN이 먼저
                    
                    for p in server["players"]:
                        server["players"][p].update({"hand": [deck.pop(), deck.pop()], "status": "LIVE"})
                    
                    server.update({"deck": deck, "board": [], "game_status": "PLAYING", "pot": 0.0, "last_action": "새로운 핸드가 시작되었습니다."})
                    st.rerun()

    # --- 메인 게임 UI ---
    if server["game_status"] == "PLAYING":
        # 1. 테이블 UI
        st.markdown(f"""<div class="poker-table">
            <p class="info-text">COMMUNITY BOARD</p>
            <h2 style="color:white;">{' | '.join(server['board']) if server['board'] else "PRE-FLOP"}</h2>
            <hr style="border: 0.5px solid #2a633d;">
            <p class="info-text">TOTAL POT</p>
            <p class="pot-text">{server['pot']:.1f} BB</p>
            <p style="color:#ffeb3b; font-size:0.9em;">최근 액션: {server['last_action']}</p>
        </div>""", unsafe_allow_html=True)

        # 2. 내 핸드 표시
        st.write("### 🎴 내 카드")
        h = my_info["hand"]
        st.markdown(f"<div><div class='card-box'>{h[0]}</div><div class='card-box'>{h[1]}</div></div>", unsafe_allow_html=True)
        st.write(f"나의 잔고: **{my_info['bb_left']:.1f} BB**")

        st.divider()

        # 3. 베팅 액션 (내 차례일 때만)
        cur_p = p_names[server["current_turn_idx"]]
        if cur_p == my_name:
            st.success("🔥 당신의 차례입니다!")
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                if st.button("Check/Call"):
                    server["last_action"] = f"{my_name}이(가) Check/Call 했습니다."
                    next_turn()
                    st.rerun()
            with c2:
                # 레이즈 입력
                r_amt = st.number_input("Raise (BB)", min_value=1.0, max_value=float(my_info["bb_left"]), value=2.0, step=1.0)
                if st.button(f"{r_amt}BB Raise"):
                    my_info["bb_left"] -= r_amt
                    server["pot"] += r_amt
                    server["last_action"] = f"{my_name}이(가) {r_amt}BB Raise 했습니다."
                    next_turn()
                    st.rerun()
            with c3:
                if st.button("ALL-IN"):
                    allin = my_info["bb_left"]
                    my_info["bb_left"] = 0
                    server["pot"] += allin
                    server["last_action"] = f"{my_name}이(가) ALL-IN! ({allin:.1f}BB)"
                    next_turn()
                    st.rerun()
            with c4:
                if st.button("Fold"):
                    server["last_action"] = f"{my_name}이(가) Fold 했습니다."
                    server["game_status"] = "WAITING" # 판 종료
                    st.rerun()
        else:
            st.warning(f"⏳ {cur_p}의 차례를 기다리는 중...")

        # 4. 방장 전용 보드 제어
        if is_host and len(server["board"]) < 5:
            st.write("")
            if st.button("➡️ 다음 카드 오픈"):
                if not server["board"]:
                    server["board"].extend([server["deck"].pop() for _ in range(3)])
                else:
                    server["board"].append(server["deck"].pop())
                # 플랍 이후는 BB부터 액션
                server["current_turn_idx"] = 1 - server["btn_idx"]
                st.rerun()
    else:
        st.info("방장이 'NEXT HAND'를 누르면 게임이 시작됩니다.")

    # 수동 새로고침 (비상용)
    st.sidebar.write("---")
    if st.sidebar.button("🔄 수동 새로고침"):
        st.rerun()
