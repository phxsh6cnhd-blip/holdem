import streamlit as st
import random
import time
from streamlit_autorefresh import st_autorefresh

# 1. 페이지 설정 및 자동 새로고침
st.set_page_config(page_title="GG Revo Holdem", layout="centered")
st_autorefresh(interval=2000, key="poker_refresh")

st.markdown("""
    <style>
    .stApp { background-color: #0b0d10; color: #ffffff; }
    .table-container {
        position: relative;
        background: radial-gradient(circle, #2c2520 0%, #000000 100%);
        border: 10px solid #222; border-radius: 200px;
        height: 520px; margin: 50px auto;
        box-shadow: 0 20px 50px rgba(0,0,0,0.8);
        display: flex; flex-direction: column; align-items: center; justify-content: center;
    }
    .card {
        background-color: #fff !important; color: #000 !important;
        width: 55px; height: 80px; border-radius: 6px;
        line-height: 80px; font-size: 1.4em; font-weight: bold;
        text-align: center; border: 1px solid #555;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.5); display: inline-block; margin: 0 3px;
    }
    .card-back {
        background: linear-gradient(135deg, #444 25%, #222 25%, #222 50%, #444 50%, #444 75%, #222 75%, #222 100%);
        background-size: 10px 10px; width: 55px; height: 80px; border-radius: 6px; border: 1px solid #777;
    }
    .red { color: #e74c3c !important; }
    .player-seat {
        position: absolute; width: 140px; text-align: center;
        background: rgba(20,20,20,0.9); padding: 10px; border-radius: 12px;
        border: 1px solid #444;
    }
    .pos-top { top: 20px; }
    .pos-bottom { bottom: 20px; border: 2px solid #3498db; }
    .dealer-btn {
        position: absolute; background: #f1c40f; color: black;
        width: 28px; height: 28px; border-radius: 50%;
        line-height: 28px; font-weight: bold; font-size: 0.8em;
        border: 2px solid #000; text-align: center;
    }
    .db-top { top: 110px; right: 170px; }
    .db-bottom { bottom: 110px; left: 170px; }
    .pot-box {
        background: rgba(0,0,0,0.7); color: #ffeb3b;
        padding: 5px 20px; border-radius: 20px; font-size: 1.3em;
        border: 1px solid #ffeb3b; margin-top: 15px; font-weight: bold;
    }
    .action-container { background: #1a1a1a; padding: 20px; border-radius: 15px; margin-top: 20px; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_resource
def get_game_server():
    return {
        "players": {}, 
        "board": [], "pot": 0.0, "btn_idx": 0, "current_turn_idx": 0,
        "game_status": "WAITING", "deck": [], "current_bet": 0.0,
        "is_allin_state": False, "last_action": ""
    }

server = get_game_server()

def render_card(c):
    if not c: return ""
    is_red = any(s in c for s in ['♥', '♦'])
    return f"<div class='card {'red' if is_red else ''}'>{c}</div>"

# --- 올인 자동 런아웃 ---
def run_auto_board():
    while len(server["board"]) < 5:
        time.sleep(1.5)
        if not server["board"]:
            server["board"].extend([server["deck"].pop() for _ in range(3)])
        else:
            server["board"].append(server["deck"].pop()) # 괄호 방식 수정 완료
        st.rerun()
    server["game_status"] = "SHOWDOWN"
    server["is_allin_state"] = False
    st.rerun()

def award_pot(winner_name):
    opp_name = [n for n in server["players"].keys() if n != winner_name][0]
    server["players"][winner_name]["stack"] += server["pot"] + server["players"][winner_name]["bet"] + server["players"][opp_name]["bet"]
    for p in server["players"].values(): p["bet"] = 0.0; p["acted"] = False; p["hand"] = []
    server.update({"pot": 0.0, "board": [], "game_status": "WAITING", "is_allin_state": False, "current_bet": 0.0})
    if server["players"][opp_name]["stack"] <= 0: server["game_status"] = "GAME_OVER"

# --- 메인 렌더링 시작 ---
if "my_name" not in st.session_state:
    st.title("💰 GG REVO HOLDEM")
    name = st.text_input("닉네임 입력").strip()
    if st.button("입장") and name:
        if len(server["players"]) < 2:
            server["players"][name] = {"hand": [], "stack": 10000.0, "bet": 0.0, "acted": False}
            st.session_state.my_name = name; st.rerun()
else:
    my_name = st.session_state.my_name
    p_names = list(server["players"].keys())
    
    # [핵심] KeyError 방지 로직: 내 이름이 명단에 없으면 세션 초기화 후 재입장 유도
    if my_name not in server["players"]:
        st.session_state.clear()
        st.rerun()

    opp_name = [n for n in p_names if n != my_name][0] if len(p_names) > 1 else None
    my_info = server["players"][my_name] # 이제 여기서 에러 안 남!
    is_host = p_names[0] == my_name

    st.markdown("<div class='table-container'>", unsafe_allow_html=True)
    
    # 1. 상대방 영역
    if opp_name:
        opp_info = server["players"][opp_name]
        opp_hand_html = ""
        if server["game_status"] == "SHOWDOWN":
            opp_hand_html = f"<div style='margin-top:5px;'>{''.join([render_card(c) for c in opp_info['hand']])}</div>"
        else:
            opp_hand_html = "<div style='margin-top:5px;'><div class='card-back'></div><div class='card-back'></div></div>"
        
        st.markdown(f"<div class='player-seat pos-top'><b>{opp_name}</b><br><span style='color:#5bc0de;'>{opp_info['stack']:,.0f}</span>{opp_hand_html}</div>", unsafe_allow_html=True)
        if server["btn_idx"] != p_names.index(my_name):
            st.markdown("<div class='dealer-btn db-top'>D</div>", unsafe_allow_html=True)

    # 2. 보드 & 팟
    board_html = "".join([render_card(c) for c in server["board"]])
    st.markdown(f"<div>{board_html}</div>", unsafe_allow_html=True)
    total_pot = server["pot"] + sum(p["bet"] for p in server["players"].values())
    st.markdown(f"<div class='pot-box'>Total Pot : {total_pot:,.0f}</div>", unsafe_allow_html=True)

    # 3. 내 영역
    my_cards_html = "".join([render_card(c) for c in my_info["hand"]]) if server["game_status"] != "WAITING" else ""
    st.markdown(f"<div class='player-seat pos-bottom'><b>{my_name}</b><br><span style='color:#5bc0de;'>{my_info['stack']:,.0f}</span><div style='margin-top:5px;'>{my_cards_html}</div></div>", unsafe_allow_html=True)
    if server["btn_idx"] == p_names.index(my_name):
        st.markdown("<div class='dealer-btn db-bottom'>D</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

    # 4. 액션 버튼
    if server["game_status"] == "PLAYING" and not server["is_allin_state"]:
        cur_p = p_names[server["current_turn_idx"]]
        if cur_p == my_name:
            st.markdown("<div class='action-container'>", unsafe_allow_html=True)
            call_amt = server["current_bet"] - my_info["bet"]
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                if st.button(f"Check/Call {call_amt:,.0f}" if call_amt > 0 else "Check"):
                    my_info["stack"] -= call_amt; my_info["bet"] += call_amt; my_info["acted"] = True
                    p1, p2 = server["players"][p_names[0]], server["players"][p_names[1]]
                    if p1["bet"] == p2["bet"] and p1["acted"] and p2["acted"]:
                        if p1["stack"] == 0 or p2["stack"] == 0:
                            server["is_allin_state"] = True; st.rerun()
                        else:
                            for p in server["players"].values(): server["pot"] += p["bet"]; p["bet"] = 0.0; p["acted"] = False
                            server["current_bet"] = 0.0
                            if not server["board"]: server["board"].extend([server["deck"].pop() for _ in range(3)])
                            elif len(server["board"]) < 5: server["board"].append(server["deck"].pop())
                            else: server["game_status"] = "SHOWDOWN"
                            server["current_turn_idx"] = 1 - server["btn_idx"]; st.rerun()
                    else: server["current_turn_idx"] = 1 - server["current_turn_idx"]; st.rerun()
            with c2:
                r_val = st.number_input("Raise To", server["current_bet"] + 100, float(my_info["stack"] + my_info["bet"]), step=100.0)
                if st.button("RAISE"):
                    diff = r_val - my_info["bet"]; my_info["stack"] -= diff; my_info["bet"] = r_val; my_info["acted"] = True
                    server["current_bet"] = r_val; server["players"][opp_name]["acted"] = False
                    server["current_turn_idx"] = 1 - server["current_turn_idx"]; st.rerun()
            with c3:
                if st.button("ALL-IN"):
                    total = my_info["stack"] + my_info["bet"]; my_info["stack"] = 0; my_info["bet"] = total; my_info["acted"] = True
                    server["current_bet"] = max(server["current_bet"], total); server["players"][opp_name]["acted"] = False
                    server["current_turn_idx"] = 1 - server["current_turn_idx"]; st.rerun()
            with c4:
                if st.button("FOLD"): award_pot(opp_name); st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    if server["is_allin_state"]:
        run_auto_board()

    # 5. 쇼다운 승자 선택 (호스트)
    if is_host and server["game_status"] == "SHOWDOWN":
        st.write("### 🏆 WINNER SELECTION")
        sc1, sc2 = st.columns(2)
        if sc1.button(f"{p_names[0]} WIN"): award_pot(p_names[0]); st.rerun()
        if sc2.button(f"{p_names[1]} WIN"): award_pot(p_names[1]); st.rerun()
    elif is_host and server["game_status"] == "WAITING" and len(p_names) == 2:
        if st.button("🚀 DEAL NEXT HAND"):
            deck = [r+s for s in ['♠','♥','♦','♣'] for r in ['2','3','4','5','6','7','8','9','10','J','Q','K','A']]; random.shuffle(deck)
            btn = server["btn_idx"]; bb = 1 - btn
            server["players"][p_names[btn]].update({"hand": [deck.pop(), deck.pop()], "bet": 50, "stack": server["players"][p_names[btn]]["stack"]-50, "acted": False})
            server["players"][p_names[bb]].update({"hand": [deck.pop(), deck.pop()], "bet": 100, "stack": server["players"][p_names[bb]]["stack"]-100, "acted": False})
            server.update({"deck": deck, "board": [], "game_status": "PLAYING", "pot": 0.0, "current_bet": 100, "current_turn_idx": btn, "btn_idx": 1-btn})
            st.rerun()
