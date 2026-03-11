import streamlit as st
import random
from streamlit_autorefresh import st_autorefresh

# 1. 페이지 설정 및 자동 새로고침
st.set_page_config(page_title="Revo Holdem Club", layout="centered")
st_autorefresh(interval=2000, key="poker_refresh")

# CSS: 테이블 통합 디자인 강화
st.markdown("""
    <style>
    .stApp { background-color: #0b0d10; color: #ffffff; }
    
    .table-container {
        position: relative;
        background: radial-gradient(circle, #1a472a 0%, #0d2616 100%);
        border: 12px solid #3d2b1f; border-radius: 200px;
        height: 480px; margin: 40px auto;
        box-shadow: inset 0 0 50px #000;
        display: flex; flex-direction: column; align-items: center; justify-content: center;
    }

    .card {
        background-color: #fff !important; color: #000 !important;
        width: 55px; height: 80px; border-radius: 6px;
        line-height: 80px; font-size: 1.4em; font-weight: bold;
        text-align: center; border: 1px solid #555;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.5); display: inline-block; margin: 0 2px;
    }
    .red { color: #e74c3c !important; }

    /* 플레이어 오버레이 디자인 */
    .player-box {
        position: absolute; width: 150px; text-align: center;
        background: rgba(0,0,0,0.7); padding: 12px; border-radius: 15px;
        border: 1px solid #444;
    }
    .pos-top { top: -35px; }
    .pos-bottom { bottom: -35px; }
    
    /* 포지션 배지 (BTN, BB) */
    .badge {
        display: inline-block; padding: 2px 6px; border-radius: 4px;
        font-size: 0.7em; font-weight: bold; margin-left: 5px;
        color: #000; vertical-align: middle;
    }
    .badge-btn { background-color: #ffeb3b; } /* 버튼/SB는 노란색 */
    .badge-bb { background-color: #ffffff; }  /* BB는 흰색 */

    .pot-info {
        background: rgba(0,0,0,0.5); color: #ffeb3b;
        padding: 8px 20px; border-radius: 25px; font-weight: bold; 
        font-size: 1.4em; border: 2px solid #ffeb3b; margin-top: 15px;
    }

    div.stButton > button {
        background-color: #2d2d2d !important; color: white !important;
        border: 1px solid #555 !important; font-weight: bold !important;
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_resource
def get_game_server():
    return {
        "players": {}, 
        "board": [], "pot": 0.0, "btn_idx": 0, "current_turn_idx": 0,
        "game_status": "WAITING", "deck": [], "current_bet": 0.0, "last_action": ""
    }

server = get_game_server()

def render_card(c):
    is_red = any(s in c for s in ['♥', '♦'])
    return f"<div class='card {'red' if is_red else ''}'>{c}</div>"

def get_pos_html(name):
    p_names = list(server["players"].keys())
    if len(p_names) < 2 or server["game_status"] == "WAITING": return ""
    idx = p_names.index(name)
    if idx == server["btn_idx"]:
        return "<span class='badge badge-btn'>BTN/SB</span>"
    else:
        return "<span class='badge badge-bb'>BB</span>"

def award_pot(winner_name):
    server["players"][winner_name]["stack"] += server["pot"] + sum(p["bet"] for p in server["players"].values())
    for p in server["players"].values(): p["bet"] = 0.0; p["acted"] = False; p["hand"] = []
    server.update({"pot": 0.0, "board": [], "game_status": "WAITING", "last_action": f"{winner_name} Win!"})
    for name, info in server["players"].items():
        if info["stack"] <= 0: server["game_status"] = "GAME_OVER"

def proceed_stage():
    for p in server["players"].values(): server["pot"] += p["bet"]; p["bet"] = 0.0; p["acted"] = False
    server["current_bet"] = 0.0
    if not server["board"]: server["board"].extend([server["deck"].pop() for _ in range(3)])
    elif len(server["board"]) < 5: server["board"].append(server["deck"].pop())
    else: server["game_status"] = "SHOWDOWN"
    server["current_turn_idx"] = 1 - server["btn_idx"]

# --- 메인 로직 ---
if "my_name" not in st.session_state:
    st.title("♠️ REVO HOLDEM")
    name = st.text_input("닉네임 입력").strip()
    if st.button("입장") and name:
        if len(server["players"]) < 2:
            server["players"][name] = {"hand": [], "stack": 100.0, "bet": 0.0, "acted": False}
            st.session_state.my_name = name; st.rerun()
else:
    my_name = st.session_state.my_name
    p_names = list(server["players"].keys())
    if my_name not in server["players"]: st.session_state.clear(); st.rerun()
    
    opp_name = [n for n in p_names if n != my_name][0] if len(p_names) > 1 else None
    my_info = server["players"][my_name]
    is_host = p_names[0] == my_name

    # 1. 통합 테이블 UI 렌더링
    st.markdown("<div class='table-container'>", unsafe_allow_html=True)
    
    # 상대 정보 (상단)
    if opp_name:
        opp_info = server["players"][opp_name]
        st.markdown(f"<div class='player-box pos-top'><b>{opp_name}</b>{get_pos_html(opp_name)}<br>{opp_info['stack']:.1f} BB<br><small>Bet: {opp_info['bet']:.1f}</small></div>", unsafe_allow_html=True)
    
    # 보드 영역
    board_html = "".join([render_card(c) for c in server["board"]]) if server["board"] else "<h3 style='color:#2a633d;'>REVO HOLDEM</h3>"
    st.markdown(f"<div style='display:flex; gap:5px;'>{board_html}</div>", unsafe_allow_html=True)
    
    # 팟 정보
    total_pot = server["pot"] + sum(p["bet"] for p in server["players"].values())
    st.markdown(f"<div class='pot-info'>POT: {total_pot:.1f} BB</div>", unsafe_allow_html=True)
    
    # 내 정보 (하단)
    st.markdown(f"<div class='player-box pos-bottom'><b>{my_name}</b>{get_pos_html(my_name)}<br>{my_info['stack']:.1f} BB<br><small>Bet: {my_info['bet']:.1f}</small></div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

    # 2. 액션 컨트롤
    if server["game_status"] == "PLAYING":
        st.write("### 🎴 MY HAND")
        st.markdown(f"<div style='display:flex; justify-content:center;'>{''.join([render_card(c) for c in my_info['hand']])}</div>", unsafe_allow_html=True)

        if p_names[server["current_turn_idx"]] == my_name:
            st.success("Your Turn!")
            call_amt = server["current_bet"] - my_info["bet"]
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                if st.button("Call/Check"):
                    my_info["stack"] -= call_amt; my_info["bet"] += call_amt; my_info["acted"] = True
                    p1, p2 = server["players"][p_names[0]], server["players"][p_names[1]]
                    if p1["bet"] == p2["bet"] and p1["acted"] and p2["acted"]: proceed_stage()
                    else: server["current_turn_idx"] = 1 - server["current_turn_idx"]
                    st.rerun()
            with c2:
                r_val = st.number_input("Raise", server["current_bet"]+1, float(my_info["stack"]), server["current_bet"]+2, label_visibility="collapsed")
                if st.button("Raise"):
                    diff = r_val - my_info["bet"]
                    my_info["stack"] -= diff; my_info["bet"] = r_val; my_info["acted"] = True; server["current_bet"] = r_val
                    server["players"][opp_name]["acted"] = False; server["current_turn_idx"] = 1 - server["current_turn_idx"]; st.rerun()
            with c3:
                if st.button("Fold"): award_pot(opp_name); st.rerun()
            with c4:
                if st.button("All-in"):
                    total = my_info["stack"] + my_info["bet"]
                    my_info["stack"] = 0; my_info["bet"] = total; my_info["acted"] = True
                    server["current_bet"] = max(server["current_bet"], total)
                    server["players"][opp_name]["acted"] = False; server["current_turn_idx"] = 1 - server["current_turn_idx"]; st.rerun()
        else:
            st.warning("Waiting for opponent...")

    elif server["game_status"] in ["SHOWDOWN", "WAITING"]:
        if is_host:
            st.write("---")
            if server["game_status"] == "SHOWDOWN":
                st.write("### 🏆 Winner Selection")
                sc1, sc2 = st.columns(2)
                if sc1.button(f"{p_names[0]} Win"): award_pot(p_names[0]); st.rerun()
                if sc2.button(f"{p_names[1]} Win"): award_pot(p_names[1]); st.rerun()
            elif len(p_names) == 2:
                if st.button("🚀 Deal Next Hand"):
                    deck = [r+s for s in ['♠','♥','♦','♣'] for r in ['2','3','4','5','6','7','8','9','10','J','Q','K','A']]; random.shuffle(deck)
                    btn = server["btn_idx"]; bb = 1 - btn
                    server["players"][p_names[btn]].update({"hand": [deck.pop(), deck.pop()], "bet": 0.5, "stack": server["players"][p_names[btn]]["stack"]-0.5, "acted": False})
                    server["players"][p_names[bb]].update({"hand": [deck.pop(), deck.pop()], "bet": 1.0, "stack": server["players"][p_names[bb]]["stack"]-1.0, "acted": False})
                    server.update({"deck": deck, "board": [], "game_status": "PLAYING", "pot": 0.0, "current_bet": 1.0, "current_turn_idx": btn, "btn_idx": 1-btn})
                    st.rerun()

    if server["game_status"] == "GAME_OVER":
        st.error(server.get("last_action", "Game Over"))
        if st.button("New Game"): server["players"] = {}; server["game_status"] = "WAITING"; st.rerun()
