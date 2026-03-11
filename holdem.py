import streamlit as st
import random

# 1. 페이지 설정
st.set_page_config(page_title="헤즈업 홀덤 Pro", layout="centered")

# CSS: 액션 차례 강조 디자인
st.markdown("""
    <style>
    .action-turn { 
        background-color: #ff4b4b; color: white; padding: 10px; 
        border-radius: 10px; text-align: center; font-weight: bold;
        margin-bottom: 10px;
    }
    .my-hand-box { 
        background-color: #e8f5e9; padding: 20px; border-radius: 15px; 
        text-align: center; border: 3px solid #27ae60; 
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_resource
def get_game_server():
    return {
        "players": {}, # {닉네임: {"hand": [], "chips": 10000}}
        "board": [],
        "btn_idx": 0,
        "current_turn_idx": 0, # 현재 누구 차례인지
        "game_status": "WAITING",
        "pot": 0
    }

server = get_game_server()

if "my_name" not in st.session_state:
    st.title("♠️ 헤즈업 멀티플레이")
    with st.form("entry"):
        name = st.text_input("닉네임 입력").strip()
        if st.form_submit_button("입장"):
            if name and name not in server["players"]:
                server["players"][name] = {"hand": [], "chips": 10000}
                st.session_state.my_name = name
                st.rerun()
else:
    my_name = st.session_state.my_name
    player_names = list(server["players"].keys())
    
    if my_name not in server["players"]:
        st.session_state.clear()
        st.rerun()

    # --- 사이드바 및 포지션 계산 ---
    is_host = player_names[0] == my_name
    st.sidebar.title("👥 플레이어")
    
    for i, p_name in enumerate(player_names):
        pos = ""
        if len(player_names) == 2 and server["game_status"] == "PLAYING":
            # 헤즈업 룰: BTN이 SB를 겸함
            pos = " (BTN/SB)" if i == server["btn_idx"] else " (BB)"
        st.sidebar.write(f"{p_name}{pos} {'(나)' if p_name == my_name else ''}")

    # --- 게임 로직 컨트롤 ---
    if is_host:
        with st.sidebar.expander("⚙️ 방장 메뉴"):
            if st.button("♻️ 전체 리셋"):
                server["players"], server["game_status"] = {}, "WAITING"
                st.rerun()
            if server["game_status"] == "WAITING" and len(player_names) == 2:
                if st.button("🚀 게임 시작"):
                    deck = [r+s for s in ['♠','♥','♦','♣'] for r in ['2','3','4','5','6','7','8','9','10','J','Q','K','A']]
                    random.shuffle(deck)
                    for p in server["players"]:
                        server["players"][p]["hand"] = [deck.pop(), deck.pop()]
                    server.update({"deck": deck, "board": [], "game_status": "PLAYING", "pot": 0})
                    # 프리플랍은 BTN/SB가 먼저 액션
                    server["current_turn_idx"] = server["btn_idx"]
                    st.rerun()

    # --- 메인 화면 ---
    st.title("🃏 홀덤 테이블")
    
    if server["game_status"] == "PLAYING":
        # 현재 누구 차례인지 표시
        current_player = player_names[server["current_turn_idx"]]
        if current_player == my_name:
            st.markdown("<div class='action-turn'>🔥 당신의 차례입니다!</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='action-turn' style='background-color:#555;'>⏳ {current_player}의 차례를 기다리는 중...</div>", unsafe_allow_html=True)

        # 1. 내 카드
        st.write("### 🎴 내 핸드")
        h = server["players"][my_name]["hand"]
        st.markdown(f"<div class='my-hand-box'><h1>{h[0]} {h[1]}</h1></div>", unsafe_allow_html=True)
        
        # 2. 베팅 버튼 (내 차례일 때만 활성화)
        st.write("")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Check / Call", disabled=(current_player != my_name)):
                server["current_turn_idx"] = (server["current_turn_idx"] + 1) % 2
                st.rerun()
        with col2:
            if st.button("Raise", disabled=(current_player != my_name)):
                server["current_turn_idx"] = (server["current_turn_idx"] + 1) % 2
                st.rerun()
        with col3:
            if st.button("Fold", disabled=(current_player != my_name)):
                server["game_status"] = "WAITING"
                st.rerun()

        st.divider()

        # 3. 보드 및 방장 컨트롤
        st.write("### 🏟 보드")
        if server["board"]:
            st.markdown(f"## {' | '.join(server['board'])}")
        
        if is_host and len(server["board"]) < 5:
            if st.button("➡️ 다음 카드 오픈"):
                if not server["board"]: server["board"].extend([server["deck"].pop() for _ in range(3)])
                else: server.board.append(server["deck"].pop())
                # 플랍 이후는 BB부터 액션 (BTN_idx가 아닌 쪽)
                server["current_turn_idx"] = 1 - server["btn_idx"]
                st.rerun()
    else:
        st.info("두 명이 접속하면 방장이 게임을 시작할 수 있습니다.")

    st.write("---")
    if st.button("🔄 새로고침"): st.rerun()
