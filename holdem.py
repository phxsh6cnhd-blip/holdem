import streamlit as st
import random
from datetime import datetime
from streamlit_autorefresh import st_autorefresh # 자동 새로고침 라이브러리

# 1. 페이지 설정
st.set_page_config(page_title="헤즈업 홀덤 Pro", layout="centered")

# --- 자동 새로고침 설정 (2초마다 실행) ---
# 이 함수가 실행되면 사용자가 버튼을 안 눌러도 2초마다 코드가 재실행됨
count = st_autorefresh(interval=2000, key="fizzbuzzcounter")

st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 12px; height: 3.5em; font-weight: bold; }
    .action-turn { 
        background-color: #ff4b4b; color: white; padding: 10px; 
        border-radius: 10px; text-align: center; font-weight: bold; margin-bottom: 10px;
    }
    .my-hand-box { 
        background-color: #e8f5e9; padding: 20px; border-radius: 15px; 
        text-align: center; border: 3px solid #27ae60; 
    }
    </style>
    """, unsafe_allow_html=True)

# 2. 공유 서버 설정
@st.cache_resource
def get_game_server():
    return {
        "players": {}, 
        "board": [],
        "btn_idx": 0,
        "current_turn_idx": 0,
        "game_status": "WAITING",
        "pot": 0,
        "deck": []
    }

server = get_game_server()

# --- 방장 자동 임명 로직 ---
def get_host_name():
    if not server["players"]: return None
    return list(server["players"].keys())[0]

# 3. 입장 로직
if "my_name" not in st.session_state:
    st.title("♠️ 실시간 홀덤 룸")
    with st.form("entry"):
        name = st.text_input("닉네임 입력").strip()
        if st.form_submit_button("입장"):
            if name and name not in server["players"]:
                server["players"][name] = {"hand": [], "chips": 10000}
                st.session_state.my_name = name
                st.rerun()
            else:
                st.error("이미 사용 중인 이름이거나 빈칸이야!")
else:
    my_name = st.session_state.my_name
    player_names = list(server["players"].keys())
    
    if my_name not in server["players"]:
        st.session_state.clear()
        st.rerun()

    host_name = get_host_name()
    is_host = (my_name == host_name)

    # 사이드바 (자동으로 갱신되어 보임)
    st.sidebar.title("👥 참여자 현황")
    for i, p_name in enumerate(player_names):
        mark = "👑" if p_name == host_name else "👤"
        pos = ""
        if len(player_names) == 2 and server["game_status"] == "PLAYING":
            pos = " (BTN/SB)" if i == server["btn_idx"] else " (BB)"
        st.sidebar.write(f"{mark} {p_name}{pos} {'(나)' if p_name == my_name else ''}")

    # 방장 메뉴
    if is_host:
        with st.sidebar.expander("⚙️ 방장 관리"):
            if st.button("♻️ 서버 전체 초기화"):
                server["players"].clear()
                server["game_status"] = "WAITING"
                st.rerun()
            
            if server["game_status"] == "WAITING" and len(player_names) >= 2:
                if st.button("🚀 게임 시작"):
                    suits, ranks = ['♠','♥','♦','♣'], ['2','3','4','5','6','7','8','9','10','J','Q','K','A']
                    deck = [r+s for s in suits for r in ranks]
                    random.shuffle(deck)
                    for p in server["players"]:
                        server["players"][p]["hand"] = [deck.pop(), deck.pop()]
                    
                    server.update({"deck": deck, "board": [], "game_status": "PLAYING", "pot": 0})
                    server["current_turn_idx"] = server["btn_idx"]
                    st.rerun()

    # --- 메인 게임 화면 ---
    if server["game_status"] == "PLAYING":
        current_player = player_names[server["current_turn_idx"]]
        if current_player == my_name:
            st.markdown("<div class='action-turn'>🔥 당신의 차례입니다!</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='action-turn' style='background-color:#555;'>⏳ {current_player}의 차례...</div>", unsafe_allow_html=True)

        st.write("### 🎴 내 핸드")
        h = server["players"][my_name]["hand"]
        st.markdown(f"<div class='my-hand-box'><h1>{h[0]} {h[1]}</h1></div>", unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("Check/Call", disabled=(current_player != my_name)):
                server["current_turn_idx"] = (server["current_turn_idx"] + 1) % len(player_names)
                st.rerun()
        with c2:
            if st.button("Raise", disabled=(current_player != my_name)):
                server["current_turn_idx"] = (server["current_turn_idx"] + 1) % len(player_names)
                st.rerun()
        with c3:
            if st.button("Fold", disabled=(current_player != my_name)):
                server["game_status"] = "WAITING"
                st.rerun()

        st.divider()
        st.write("### 🏟 커뮤니티 카드")
        if server["board"]:
            st.markdown(f"## {' | '.join(server['board'])}")
        
        if is_host and len(server["board"]) < 5:
            if st.button("➡️ 다음 카드 오픈"):
                if not server["board"]: server["board"].extend([server["deck"].pop() for _ in range(3)])
                else: server["board"].append(server["deck"].pop())
                server["current_turn_idx"] = 1 - server["btn_idx"]
                st.rerun()
    else:
        st.info("두 명 이상 접속하면 방장이 게임을 시작할 수 있습니다.")
