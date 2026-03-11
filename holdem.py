import streamlit as st
import random
import pandas as pd
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="우리만의 홀덤 룸", layout="centered")

# CSS: 모바일 가독성 및 카드 박스 디자인
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 12px; height: 3.5em; font-weight: bold; }
    .card-box { 
        background-color: #f8f9fa; 
        padding: 20px; 
        border-radius: 15px; 
        text-align: center; 
        border: 2px solid #27ae60; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .host-badge { color: #f1c40f; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 2. 전역 공유 서버 설정 (모든 접속자가 이 데이터를 공유함)
@st.cache_resource
def get_game_server():
    return {
        "players": {}, # {닉네임: {"hand": [], "chips": 10000, "is_host": False}}
        "board": [],
        "bb": 100,
        "deck": [],
        "game_status": "WAITING"
    }

server = get_game_server()

# 3. 로그인/입장 로직
if "my_name" not in st.session_state:
    st.title("♠️ 프라이빗 홀덤 룸")
    st.write("친구들과 같은 링크로 접속해 게임을 즐기세요!")
    
    with st.form("entry_form"):
        name = st.text_input("사용할 닉네임 입력").strip()
        submit = st.form_submit_button("게임방 입장하기")
        if submit and name:
            if name not in server["players"]:
                # 첫 접속자를 방장으로 설정
                is_host = len(server["players"]) == 0
                server["players"][name] = {"hand": [], "chips": 10000, "is_host": is_host}
                st.session_state.my_name = name
                st.rerun()
            else:
                st.error("이미 방에 있는 이름이야! 다른 이름을 써줘.")
else:
    my_name = st.session_state.my_name
    
    # 서버 리셋 등으로 내 정보가 사라진 경우 대응
    if my_name not in server["players"]:
        st.session_state.clear()
        st.rerun()
        
    my_info = server["players"][my_name]

    # --- 사이드바: 플레이어 현황 ---
    st.sidebar.title("👥 참여자 목록")
    for p_name, p_data in server["players"].items():
        role_icon = "👑" if p_data["is_host"] else "👤"
        st.sidebar.write(f"{role_icon} **{p_name}** ({p_data['chips']:,} 칩)")

    # 방장 전용 관리 도구
    if my_info["is_host"]:
        with st.sidebar.expander("⚙️ 방장 전용 설정"):
            if st.button("♻️ 게임 서버 초기화 (전체 리셋)"):
                server["players"] = {}
                server["game_status"] = "WAITING"
                server["board"] = []
                st.rerun()
            
            if server["game_status"] == "WAITING":
                bb_val = st.number_input("스타트 BB", value=100, step=100)
                if st.button("🚀 게임 시작 (카드 셔플)"):
                    # 덱 생성 및 셔플
                    suits = ['♠', '♥', '♦', '♣']
                    ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
                    deck = [f"{r}{s}" for s in suits for r in ranks]
                    random.shuffle(deck)
                    
                    # 모든 플레이어에게 2장씩 배분
                    for p in server["players"]:
                        server["players"][p]["hand"] = [deck.pop(), deck.pop()]
                    
                    server["deck"] = deck
                    server["bb"] = bb_val
                    server["game_status"] = "PLAYING"
                    server["board"] = []
                    st.rerun()

    # --- 메인 게임 화면 ---
    st.title("🃏 홀덤 테이블")

    if server["game_status"] == "PLAYING":
        st.info(f"💰 **현재 BB: {server['bb']:,}**")
        
        # 1. 내 핸드 확인 (체크박스로 가리기 기능)
        st.write("### 🎴 내 카드")
        show_card = st.checkbox("내 카드 몰래 보기")
        if show_card:
            h = my_info["hand"]
            st.markdown(f"<div class='card-box'><h2>{h[0]} {h[1]}</h2></div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='card-box'><h2>🂠 🂠</h2></div>", unsafe_allow_html=True)

        st.divider()

        # 2. 커뮤니티 카드 (공용 보드)
        st.write("### 🏟 커뮤니티 카드")
        if server["board"]:
            st.markdown(f"## {' | '.join(server['board'])}")
        else:
            st.write("아직 깔린 카드가 없습니다.")

        # 3. 방장용 보드 컨트롤
        if my_info["is_host"] and len(server["board"]) < 5:
            st.write("")
            btn_label = "Flop 오픈 (3장)" if len(server["board"]) == 0 else "다음 카드 오픈"
            if st.button(f"➡️ {btn_label}"):
                if len(server["board"]) == 0:
                    server["board"].extend([server["deck"].pop() for _ in range(3)])
                else:
                    server["board"].append(server["deck"].pop())
                st.rerun()
                
    else:
        st.warning("⏳ 게임 대기 중입니다. 방장이 시작하기를 기다려주세요.")
        st.write(f"현재 접속: **{len(server['players'])}명**")

    # 수동 동기화 버튼
    st.write("---")
    if st.button("🔄 화면 새로고침"):
        st.rerun()
