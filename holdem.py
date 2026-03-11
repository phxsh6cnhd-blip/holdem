import streamlit as st
import random
import pandas as pd
import time

# 1. 페이지 설정 및 디자인
st.set_page_config(page_title="우리만의 홀덤 룸", layout="centered")

# 2. 모든 사용자가 공유하는 데이터 (서버 역할)
if "game_server" not in st.session_state:
    st.session_state.game_server = {
        "players": {}, # {닉네임: {"hand": [], "chips": 0}}
        "board": [],
        "bb": 100,
        "deck": [],
        "game_status": "WAITING", # WAITING, PLAYING, END
        "turn": None
    }

server = st.session_state.game_server

# --- UI 섹션 ---
st.title("♠️ 커스텀 홀덤 룸")

# 1단계: 닉네임 입력 및 입장
if "my_name" not in st.session_state:
    with st.form("entry_form"):
        name = st.text_input("사용할 닉네임을 입력하세요")
        submit = st.form_submit_button("입장하기")
        if submit and name:
            st.session_state.my_name = name
            server["players"][name] = {"hand": [], "chips": 10000} # 기본 칩 1만
            st.rerun()
else:
    my_name = st.session_state.my_name
    st.sidebar.write(f"✅ 접속 중: **{my_name}**")
    
    # 방장(첫 번째 접속자) 전용 설정
    is_host = list(server["players"].keys())[0] == my_name
    if is_host and server["game_status"] == "WAITING":
        with st.expander("⚙️ 방장 설정 (BB 설정)"):
            bb_val = st.number_input("스타트 BB 설정", value=100, step=100)
            if st.button("게임 시작 (카드 셔플)"):
                # 카드 섞고 분배 로직
                suits = ['♠', '♥', '♦', '♣']
                ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
                deck = [f"{r}{s}" for s in suits for r in ranks]
                random.shuffle(deck)
                
                # 플레이어별 카드 분배
                for p in server["players"]:
                    server["players"][p]["hand"] = [deck.pop(), deck.pop()]
                
                server["deck"] = deck
                server["bb"] = bb_val
                server["game_status"] = "PLAYING"
                server["board"] = []
                st.rerun()

    # --- 테이블 화면 ---
    if server["game_status"] == "PLAYING":
        st.write(f"💰 **BB: {server['bb']}**")
        
        # 1. 내 패 확인 (나만 보여야 함)
        st.subheader("🎴 내 핸드")
        my_hand = server["players"][my_name]["hand"]
        if st.checkbox("내 카드 보기 (보안 주의)"):
            st.write(f"## {my_hand[0]} {my_hand[1]}")
        else:
            st.write("## 🂠 🂠")

        st.divider()

        # 2. 공통 보드
        st.subheader("🏟️ 테이블 보드")
        if server["board"]:
            st.write(f"### {' | '.join(server['board'])}")
        else:
            st.write("카드를 기다리는 중...")

        # 3. 상대방 상태 (핸드는 비밀)
        st.write("👥 접속 플레이어")
        for p in server["players"]:
            if p != my_name:
                st.write(f"- {p}: 🂠 🂠 (칩: {server['players'][p]['chips']})")

        # 방장이 보드 오픈 제어
        if is_host:
            if st.button("다음 카드 오픈 (Flop/Turn/River)"):
                if len(server["board"]) == 0: # 플랍
                    server["board"].extend([server["deck"].pop() for _ in range(3)])
                elif len(server["board"]) < 5: # 턴/리버
                    server["board"].append(server["deck"].pop())
                st.rerun()

    else:
        st.info("다른 플레이어를 기다리거나 방장이 시작하기를 기다려주세요.")
        st.write(f"현재 대기 중: {', '.join(server['players'].keys())}")

    # 리프레시 버튼 (멀티플레이 싱크를 위해)
    if st.button("🔄 새로고침"):
        st.rerun()