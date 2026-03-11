import streamlit as st
import random
import time
from streamlit_autorefresh import st_autorefresh

# 1. 페이지 설정 및 자동 새로고침
st.set_page_config(page_title="GG REVO POKER", layout="centered")
st_autorefresh(interval=2000, key="poker_refresh")

st.markdown("""
    <style>
    .stApp { background-color: #050505; color: #ffffff; }
    .poker-arena { display: flex; flex-direction: column; align-items: center; width: 100%; min-height: 550px; }
    .table-main {
        position: relative; background: radial-gradient(circle, #2d241e 0%, #000 100%);
        border: 10px solid #222; border-radius: 200px; width: 100%; max-width: 550px; height: 380px; 
        box-shadow: inset 0 0 80px #000; display: flex; align-items: center; justify-content: center;
    }
    .card {
        background-color: #fff !important; color: #000 !important; width: 45px; height: 65px; 
        border-radius: 4px; line-height: 65px; font-size: 1.1em; font-weight: bold;
        text-align: center; border: 1px solid #999; box-shadow: 2px 2px 5px rgba(0,0,0,0.5); margin: 0 2px;
    }
    .red { color: #e74c3c !important; }
    .card-back { background: #7d1a1a; width: 45px; height: 65px; border-radius: 4px; border: 1px solid #fff; }
    .p-seat { position: absolute; width: 125px; text-align: center; background: rgba(15,15,15,0.9); border-radius: 10px; border: 1px solid #444; padding: 5px; z-index: 10; }
    .opp-seat { top: 20px; }
    .me-seat { bottom: 20px; border: 2px solid #f1c40f; }
    .pot-display { position: absolute; top: 42%; color: #f1c40f; font-weight: bold; font-size: 1.1em; background: rgba(0,0,0,0.6); padding: 4px 15px; border-radius: 20px; }
    .dealer-btn { position: absolute; width: 22px; height: 22px; border-radius: 50%; background: #f1c40f; color: #000; font-weight: bold; font-size: 0.7em; line-height: 22px; text-align: center; border: 1px solid #000; }
    .db-opp { top: 90px; right: 135px; }
    .db-me { bottom: 90px; left: 135px; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_resource
def get_game_server():
    return {
        "players": {}, "board": [], "pot": 0.0, "btn_idx": 0, "current_turn_idx": 0,
        "game_status": "WAITING", "deck": [], "current_bet": 0.0, "is_allin_state": False
    }

server = get_game_server()

def draw_card(c):
    if not c: return ""
    is_red = any(s in c for s in ['♥', '♦'])
    return f"<div class='card {'red' if is_red else ''}'>{c}</div>"

# --- [추가] 강제 초기화 기능 (참여 안 될 때 사용) ---
if st.sidebar.button("⚠️ 서버 강제 초기화"):
    server["players"] = {}
    server["game_status"] = "WAITING"
    st.rerun()

# 3. 입장 및 메인 화면
if "my_name" not in st.session_state:
    st.title("💰 GG REVO POKER")
    name = st.text_input("닉네임 입력").strip()
    
    # 입장 가능 여부 표시
    slots_left = 2 - len(server["players"])
    st.write(f"현재 참여 가능 인원: **{slots_left}명**")
    
    if st.button("게임 참여하기"):
        if not name:
            st.error("닉네임을 입력해줘!")
        elif name in server["players"]:
            st.error("이미 사용 중인 이름이야!")
        elif len(server["players"]) >= 2:
            st.error("방이 꽉 찼어! 사이드바에서 초기화를 눌러줘.")
        else:
            server["players"][name] = {"hand": [], "stack": 10000.0, "bet": 0.0, "acted": False}
            st.session_state.my_name = name
            st.success(f"{name}님 환영해! 잠시만 기다려...")
            time.sleep(1)
            st.rerun()
else:
    # --- 이하 게임 화면 (동일) ---
    my_name = st.session_state.my_name
    p_names = list(server["players"].keys())
    
    if my_name not in server["players"]:
        st.session_state.clear()
        st.rerun()

    opp_name = [n for n in p_names if n != my_name][0] if len(p_names) > 1 else None
    my_info = server["players"][my_name]
    is_host = p_names[0] == my_name

    st.markdown("<div class='poker-arena'><div class='table-main'>", unsafe_allow_html=True)
    
    # 상대방
    if opp_name:
        opp_info = server["players"][opp_name]
        opp_cards = "".join([draw_card(c) for c in opp_info["hand"]]) if server["game_status"] == "SHOWDOWN" else "<div style='display:flex;justify-content:center;'><div class='card-back'></div><div class='card-back'></div></div>"
        st.markdown(f"<div class='p-seat opp-seat'><div style='font-size:0.8em; color:#aaa;'>{opp_name}</div><div style='color:#5bc0de; font-weight:bold;'>{opp_info['stack']:,.0f}</div><div style='display:flex; justify-content:center; gap:2px; margin-top:3px;'>{opp_cards}</div></div>", unsafe_allow_html=True)
        if server["btn_idx"] != p_names.index(my_name): st.markdown("<div class='dealer-btn db-opp'>D</div>", unsafe_allow_html=True)

    # 보드
    board_html = "".join([draw_card(c) for c in server["board"]])
    st.markdown(f"<div style='display:flex; justify-content:center; z-index:5;'>{board_html}</div>", unsafe_allow_html=True)
    total_pot = float(server["pot"] + sum(p["bet"] for p in server["players"].values()))
    st.markdown(f"<div class='pot-display'>Total Pot: {total_pot:,.0f}</div>", unsafe_allow_html=True)

    # 나
    my_cards = "".join([draw_card(c) for c in my_info["hand"]]) if server["game_status"] != "WAITING" else ""
    st.markdown(f"<div class='p-seat me-seat'><div style='font-size:0.8em; color:#aaa;'>{my_name}</div><div style='color:#5bc0de; font-weight:bold;'>{my_info['stack']:,.0f}</div><div style='display:flex; justify-content:center; gap:2px; margin-top:3px;'>{my_cards}</div></div>", unsafe_allow_html=True)
    if server["btn_idx"] == p_names.index(my_name): st.markdown("<div class='dealer-btn db-me'>D</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True) 

    # [액션 버튼 바] - 여기에 추가 (테이블 밖)
    if server["game_status"] == "PLAYING" and not server["is_allin_state"]:
        cur_p = p_names[server["current_turn_idx"]]
        if cur_p == my_name:
            st.write("---")
            call_amt = float(server["current_bet"] - my_info["bet"])
            c1, c2, c3, c4 = st.columns(4)
            # (이하 베팅 버튼 로직 동일...)
            with c1:
                if st.button(f"CALL {call_amt:,.0f}" if call_amt > 0 else "CHECK"):
                    my_info["stack"] -= call_amt; my_info["bet"] += call_amt; my_info["acted"] = True
                    p1, p2 = server["players"][p_names[0]], server["players"][p_names[1]]
                    if p1["bet"] == p2["bet"] and p1["acted"] and p2["acted"]:
                        if p1["stack"] <= 0 or p2["stack"] <= 0: server["is_allin_state"] = True
                        else:
                            for p in server["players"].values(): server["pot"] += p["bet"]; p["bet"] = 0.0; p["acted"] = False
                            server["current_bet"] = 0.0
                            if not server["board"]: server["board"].extend([server["deck"].pop() for _ in range(3)])
                            elif len(server["board"]) < 5: server["board"].append(server["deck"].pop())
                            else: server["game_status"] = "SHOWDOWN"
                            server["current_turn_idx"] = 1 - server["btn_idx"]
                    else: server["current_turn_idx"] = 1 - server["current_turn_idx"]
                    st.rerun()
            with c2:
                r_val = st.number_input("Raise", float(server["current_bet"] + 100), float(my_info["stack"] + my_info["bet"]), step=100.0, label_visibility="collapsed")
                if st.button("RAISE"):
                    diff = r_val - my_info["bet"]; my_info["stack"] -= diff; my_info["bet"] = r_val; my_info["acted"] = True
                    server["current_bet"] = r_val; server["players"][opp_name]["acted"] = False
                    server["current_turn_idx"] = 1 - server["current_turn_idx"]; st.rerun()
            with c3:
                if st.button("ALL-IN"):
                    total = float(my_info["stack"] + my_info["bet"]); my_info["stack"] = 0.0; my_info["bet"] = total; my_info["acted"] = True
                    server["current_bet"] = max(server["current_bet"], total); server["players"][opp_name]["acted"] = False
                    server["current_turn_idx"] = 1 - server["current_turn_idx"]; st.rerun()
            with c4:
                if st.button("FOLD"):
                    opp = [n for n in server["players"].keys() if n != my_name][0]
                    server["players"][opp]["stack"] += server["pot"] + sum(p["bet"] for p in server["players"].values())
                    for p in server["players"].values(): p["bet"] = 0.0; p["hand"] = []
                    server.update({"pot": 0.0, "board": [], "game_status": "WAITING"}); st.rerun()

    st.markdown("</div>", unsafe_allow_html=True) # arena 끝

    # 올인 런아웃 로직
    if server["is_allin_state"]:
        while len(server["board"]) < 5:
            time.sleep(1.5)
            if not server["board"]: server["board"].extend([server["deck"].pop() for _ in range(3)])
            elif len(server["board"]) < 5: server["board"].append(server["deck"].pop())
            st.rerun()
        server["game_status"] = "SHOWDOWN"; server["is_allin_state"] = False; st.rerun()

    # 쇼다운 승자 선택 (호스트)
    if is_host and server["game_status"] == "SHOWDOWN":
        st.write("### 🏆 승자 선택")
        sc1, sc2 = st.columns(2)
        def award(winner):
            opp = [n for n in server["players"].keys() if n != winner][0]
            server["players"][winner]["stack"] += server["pot"] + server["players"][winner]["bet"] + server["players"][opp]["bet"]
            for p in server["players"].values(): p["bet"] = 0.0; p["hand"] = []
            server.update({"pot": 0.0, "board": [], "game_status": "WAITING", "current_bet": 0.0})
            st.rerun()
        if sc1.button(f"{p_names[0]} 승리"): award(p_names[0])
        if sc2.button(f"{p_names[1]} 승리"): award(p_names[1])
    elif is_host and server["game_status"] == "WAITING" and len(p_names) == 2:
        if st.button("🚀 NEXT HAND"):
            deck = [r+s for s in ['♠','♥','♦','♣'] for r in ['2','3','4','5','6','7','8','9','10','J','Q','K','A']]; random.shuffle(deck)
            btn, bb = server["btn_idx"], 1 - server["btn_idx"]
            server["players"][p_names[btn]].update({"hand": [deck.pop(), deck.pop()], "bet": 50.0, "stack": server["players"][p_names[btn]]["stack"]-50.0, "acted": False})
            server["players"][p_names[bb]].update({"hand": [deck.pop(), deck.pop()], "bet": 100.0, "stack": server["players"][p_names[bb]]["stack"]-100.0, "acted": False})
            server.update({"deck": deck, "board": [], "game_status": "PLAYING", "pot": 0.0, "current_bet": 100.0, "current_turn_idx": btn, "btn_idx": 1-btn})
            st.rerun()
