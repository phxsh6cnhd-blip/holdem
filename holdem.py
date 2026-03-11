import streamlit as st
import random
from streamlit_autorefresh import st_autorefresh

# 1. 페이지 설정 및 자동 새로고침
st.set_page_config(page_title="Revo Holdem Engine", layout="centered")
st_autorefresh(interval=2000, key="poker_refresh")

st.markdown("""
    <style>
    .stApp { background-color: #0b0d10; color: #ffffff; }
    .poker-table {
        background: radial-gradient(circle, #1a472a 0%, #0d2616 100%);
        border: 10px solid #3d2b1f; border-radius: 150px;
        padding: 40px 20px; text-align: center; box-shadow: inset 0 0 50px #000; margin-bottom: 20px;
    }
    .card {
        background-color: #fff !important; color: #000 !important;
        width: 60px; height: 85px; display: inline-block;
        border-radius: 8px; margin: 3px; line-height: 85px;
        font-size: 1.5em; font-weight: bold; border: 1px solid #555; text-align: center;
    }
    .red { color: #e74c3c !important; }
    div.stButton > button {
        background-color: #2d2d2d !important; color: white !important;
        height: 3em !important; font-weight: bold !important;
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_resource
def get_game_server():
    return {
        "players": {}, # {name: {"hand": [], "stack": 100.0, "bet": 0.0, "acted": False}}
        "board": [], "pot": 0.0, "btn_idx": 0, "current_turn_idx": 0,
        "game_status": "WAITING", "deck": [], "last_raise": 0.0, "current_bet": 0.0
    }

server = get_game_server()

def render_card(c):
    is_red = any(s in c for s in ['♥', '♦'])
    return f"<div class='card {'red' if is_red else ''}'>{c}</div>"

# --- 핵심 로직: 라운드 종료 판단 ---
def check_round_finished():
    p_names = list(server["players"].keys())
    p1, p2 = server["players"][p_names[0]], server["players"][p_names[1]]
    
    # 두 명의 베팅 금액이 같고, 최소 한 명은 액션을 완료했을 때 (단, 프리플랍 BB 옵션 상황 제외)
    if p1["bet"] == p2["bet"] and (p1["acted"] and p2["acted"]):
        return True
    return False

def move_to_next_stage():
    # 팟 합산 및 플레이어 베팅 초기화
    for p in server["players"].values():
        server["pot"] += p["bet"]
        p["bet"] = 0.0
        p["acted"] = False
    
    server["current_bet"] = 0.0
    server["last_raise"] = 1.0 # 최소 레이즈 단위 초기화
    
    if not server["board"]: # 프리플랍 -> 플랍
        server["board"].extend([server["deck"].pop() for _ in range(3)])
        server["current_turn_idx"] = 1 - server["btn_idx"] # 플랍 이후는 BB 선액션
    elif len(server["board"]) < 5: # 플랍 -> 턴, 턴 -> 리버
        server["board"].append(server["deck"].pop())
        server["current_turn_idx"] = 1 - server["btn_idx"]
    else:
        server["game_status"] = "SHOWDOWN"

# --- 메인 렌더링 ---
if "my_name" not in st.session_state:
    st.title("♣️ REVO ENGINE")
    with st.form("join"):
        name = st.text_input("닉네임").strip()
        if st.form_submit_button("입장"):
            if name and name not in server["players"] and len(server["players"]) < 2:
                server["players"][name] = {"hand": [], "stack": 100.0, "bet": 0.0, "acted": False}
                st.session_state.my_name = name; st.rerun()
else:
    my_name = st.session_state.my_name
    p_names = list(server["players"].keys())
    if my_name not in server["players"]: st.session_state.clear(); st.rerun()
    
    is_host = p_names[0] == my_name
    my_info = server["players"][my_name]
    opp_name = [n for n in p_names if n != my_name][0] if len(p_names) > 1 else None

    # 테이블 UI
    st.markdown("<div class='poker-table'>", unsafe_allow_html=True)
    if server["game_status"] != "WAITING":
        st.markdown("".join([render_card(c) for c in server["board"]]) if server["board"] else "<h3>PRE-FLOP</h3>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:#ffeb3b; font-size:1.5em;'>POT: {server['pot'] + sum(p['bet'] for p in server['players'].values()):.1f} BB</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    if server["game_status"] == "PLAYING" and opp_name:
        opp_info = server["players"][opp_name]
        
        # 레이아웃: 나 vs 상대
        c1, c2 = st.columns(2)
        with c1:
            st.write(f"🙋 **{my_name}** (Stack: {my_info['stack']:.1f})")
            st.markdown("".join([render_card(c) for c in my_info["hand"]]), unsafe_allow_html=True)
            st.info(f"Bet: {my_info['bet']:.1f} BB")
        with c2:
            st.write(f"👤 **{opp_name}** (Stack: {opp_info['stack']:.1f})")
            st.markdown("<div class='card'>?</div><div class='card'>?</div>", unsafe_allow_html=True)
            st.info(f"Bet: {opp_info['bet']:.1f} BB")

        st.divider()

        # 베팅 컨트롤
        cur_idx = server["current_turn_idx"]
        if p_names[cur_idx] == my_name:
            st.success("Your Action")
            call_amount = server["current_bet"] - my_info["bet"]
            min_raise = server["current_bet"] + server["last_raise"]
            
            col1, col2, col3 = st.columns(3)
            with col1: # CALL / CHECK
                label = "Check" if call_amount == 0 else f"Call {call_amount:.1f}"
                if st.button(label):
                    my_info["stack"] -= call_amount
                    my_info["bet"] += call_amount
                    my_info["acted"] = True
                    if check_round_finished(): move_to_next_stage()
                    else: server["current_turn_idx"] = 1 - cur_idx
                    st.rerun()
            
            with col2: # RAISE
                r_val = st.number_input("Raise to", min_raise, float(my_info['stack'] + my_info['bet']), min_raise, 1.0)
                if st.button("Raise"):
                    added_bet = r_val - my_info["bet"]
                    server["last_raise"] = r_val - server["current_bet"]
                    server["current_bet"] = r_val
                    my_info["stack"] -= added_bet
                    my_info["bet"] = r_val
                    my_info["acted"] = True
                    # 레이즈 시 상대방은 다시 액션해야 함
                    server["players"][opp_name]["acted"] = False
                    server["current_turn_idx"] = 1 - cur_idx
                    st.rerun()
            
            with col3: # FOLD
                if st.button("Fold"):
                    server["game_status"] = "WAITING"
                    st.rerun()
        else:
            st.warning("Wait for opponent...")

    # 호스트 관리 (게임 시작)
    if is_host:
        with st.sidebar:
            if st.button("Reset Game"): server["players"] = {}; server["game_status"] = "WAITING"; st.rerun()
            if len(p_names) == 2 and st.button("Deal Next Hand"):
                deck = [r+s for s in ['♠','♥','♦','♣'] for r in ['2','3','4','5','6','7','8','9','10','J','Q','K','A']]
                random.shuffle(deck)
                # 프리플랍 블라인드 포스트
                btn = server["btn_idx"]
                bb = 1 - btn
                p_btn, p_bb = p_names[btn], p_names[bb]
                
                server["players"][p_btn].update({"hand": [deck.pop(), deck.pop()], "bet": 0.5, "stack": server["players"][p_btn]["stack"]-0.5, "acted": False})
                server["players"][p_bb].update({"hand": [deck.pop(), deck.pop()], "bet": 1.0, "stack": server["players"][p_bb]["stack"]-1.0, "acted": False})
                
                server.update({"deck": deck, "board": [], "game_status": "PLAYING", "pot": 0.0, "current_bet": 1.0, "last_raise": 1.0, "current_turn_idx": btn})
                st.rerun()
