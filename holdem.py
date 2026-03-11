import streamlit as st
import random
import time
from streamlit_autorefresh import st_autorefresh

# 1. 페이지 설정 및 자동 새로고침
st.set_page_config(page_title="GG REVO POKER", layout="centered")
st_autorefresh(interval=2000, key="poker_refresh")

# CSS: 테이블 위젯 통합 배치 (중구난방 해결)
st.markdown("""
    <style>
    .stApp { background-color: #050505; color: #ffffff; }
    
    /* 실제 게임판 (GGPoker 느낌) */
    .table-main {
        position: relative;
        background: radial-gradient(circle, #2d241e 0%, #000 100%);
        border: 8px solid #222; border-radius: 220px;
        width: 100%; height: 550px; margin: 0 auto;
        box-shadow: inset 0 0 80px #000, 0 20px 40px rgba(0,0,0,0.8);
        overflow: visible; display: flex; align-items: center; justify-content: center;
    }

    /* 보드 카드 중앙 정렬 */
    .board-container { display: flex; gap: 8px; justify-content: center; z-index: 5; }

    /* 카드 디자인 개선 (직사각형 비율) */
    .card {
        background-color: #fff !important; color: #000 !important;
        width: 60px; height: 85px; border-radius: 6px;
        line-height: 85px; font-size: 1.5em; font-weight: bold;
        text-align: center; border: 1px solid #999;
        box-shadow: 2px 4px 10px rgba(0,0,0,0.5);
    }
    .red { color: #e74c3c !important; }
    .card-back {
        background: linear-gradient(135deg, #7d1a1a 25%, #5a1212 25%, #5a1212 50%, #7d1a1a 50%, #7d1a1a 75%, #5a1212 75%, #5a1212 100%);
        background-size: 8px 8px; width: 60px; height: 85px; border-radius: 6px; border: 1px solid #fff;
    }

    /* 플레이어 박스 (상대: 상단, 나: 하단) */
    .p-box {
        position: absolute; width: 150px; text-align: center; z-index: 10;
        background: rgba(15,15,15,0.9); border-radius: 12px; border: 1px solid #444; padding: 10px;
    }
    .opp-seat { top: -30px; }
    .me-seat { bottom: -30px; border: 2px solid #f1c40f; } /* 내 자리는 금색 강조 */

    /* 팟(Pot) 위치 */
    .pot-display {
        position: absolute; top: 35%; color: #f1c40f; font-size: 1.3em;
        font-weight: bold; background: rgba(0,0,0,0.5); padding: 5px 20px; border-radius: 20px;
    }

    /* 딜러 버튼 (D) */
    .d-btn {
        position: absolute; width: 30px; height: 30px; border-radius: 50%;
        background: #f1c40f; color: #000; font-weight: bold; font-size: 0.9em;
        line-height: 30px; text-align: center; border: 2px solid #000;
    }
    .db-opp { top: 80px; right: 100px; }
    .db-me { bottom: 80px; left: 100px; }

    /* 액션 버튼 (테이블 밖 하단) */
    .action-bar {
        background: #111; padding: 25px; border-radius: 20px; margin-top: 40px;
        display: flex; gap: 10px; border: 1px solid #333;
    }
    div.stButton > button {
        background-color: #2c3e50 !important; color: #fff !important;
        border-radius: 12px !important; height: 3.5em !important; font-weight: bold !important;
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_resource
def get_game_server():
    return {
        "players": {}, 
        "board": [], "pot": 0.0, "btn_idx": 0, "current_turn_idx": 0,
        "game_status": "WAITING", "deck": [], "current_bet": 0.0,
        "is_allin_state": False
    }

server = get_game_server()

def draw_card(c):
    if not c: return ""
    is_red = any(s in c for s in ['♥', '♦'])
    return f"<div class='card {'red' if is_red else ''}'>{c}</div>"

# --- 메인 렌더링 ---
if "my_name" not in st.session_state:
    st.title("💰 GG REVO POKER")
    name = st.text_input("NICKNAME").strip()
    if st.button("SIT DOWN") and name:
        if len(server["players"]) < 2:
            server["players"][name] = {"hand": [], "stack": 10000.0, "bet": 0.0, "acted": False}
            st.session_state.my_name = name; st.rerun()
else:
    my_name = st.session_state.my_name
    p_names = list(server["players"].keys())
    
    # 팅김 방지
    if my_name not in server["players"]:
        st.session_state.clear(); st.rerun()

    opp_name = [n for n in p_names if n != my_name][0] if len(p_names) > 1 else None
    my_info = server["players"][my_name]
    is_host = p_names[0] == my_name

    # 1. 통합 테이블 UI
    st.markdown("<div class='table-main'>", unsafe_allow_html=True)
    
    # [상대방 영역]
    if opp_name:
        opp_info = server["players"][opp_name]
        opp_card_html = ""
        if server["game_status"] == "SHOWDOWN":
            opp_card_html = "".join([draw_card(c) for c in opp_info["hand"]])
        else:
            opp_card_html = "<div class='card-back'></div><div class='card-back'></div>"
        
        st.markdown(f"""
            <div class='p-box opp-seat'>
                <div style='font-weight:bold; color:#ccc;'>{opp_name}</div>
                <div style='color:#5bc0de;'>{opp_info['stack']:,.0f}</div>
                <div style='display:flex; gap:4px; justify-content:center; margin-top:5px;'>{opp_card_html}</div>
            </div>
        """, unsafe_allow_html=True)
        if server["btn_idx"] != p_names.index(my_name):
            st.markdown("<div class='d-btn db-opp'>D</div>", unsafe_allow_html=True)

    # [보드 영역]
    board_html = "".join([draw_card(c) for c in server["board"]])
    st.markdown(f"<div class='board-container'>{board_html}</div>", unsafe_allow_html=True)
    
    # [팟 정보]
    total_pot = float(server["pot"] + sum(p["bet"] for p in server["players"].values()))
    st.markdown(f"<div class='pot-display'>Total Pot: {total_pot:,.0f}</div>", unsafe_allow_html=True)

    # [내 영역]
    my_card_html = "".join([draw_card(c) for c in my_info["hand"]]) if server["game_status"] != "WAITING" else ""
    st.markdown(f"""
        <div class='p-box me-seat'>
            <div style='font-weight:bold; color:#fff;'>{my_name}</div>
            <div style='color:#5bc0de;'>{my_info['stack']:,.0f}</div>
            <div style='display:flex; gap:4px; justify-content:center; margin-top:5px;'>{my_card_html}</div>
        </div>
    """, unsafe_allow_html=True)
    if server["btn_idx"] == p_names.index(my_name):
        st.markdown("<div class='d-btn db-me'>D</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

    # 2. 액션 바 (테이블 밖)
    if server["game_status"] == "PLAYING" and not server["is_allin_state"]:
        cur_p = p_names[server["current_turn_idx"]]
        if cur_p == my_name:
            st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)
            col_act = st.container()
            with col_act:
                call_amt = float(server["current_bet"] - my_info["bet"])
                c1, c2, c3, c4 = st.columns(4)
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
                    m_r = float(server["current_bet"] + 100)
                    mx_r = float(my_info["stack"] + my_info["bet"])
                    if m_r > mx_r: m_r = mx_r
                    r_val = st.number_input("RAISE", m_r, mx_r, m_r, 100.0, label_visibility="collapsed")
                    if st.button(f"RAISE {r_val:,.0f}"):
                        diff = r_val - my_info["bet"]; my_info["stack"] -= diff; my_info["bet"] = r_val; my_info["acted"] = True
                        server["current_bet"] = r_val; server["players"][opp_name]["acted"] = False
                        server["current_turn_idx"] = 1 - server["current_turn_idx"]; st.rerun()
                with c3:
                    if st.button("ALL-IN"):
                        total = float(my_info["stack"] + my_info["bet"]); my_info["stack"] = 0.0; my_info["bet"] = total; my_info["acted"] = True
                        server["current_bet"] = max(server["current_bet"], total); server["players"][opp_name]["acted"] = False
                        server["current_turn_idx"] = 1 - server["current_turn_idx"]; st.rerun()
                with c4:
                    if st.button("FOLD"): award_pot(opp_name); st.rerun()

    # 올인 자동 런아웃 연출
    if server["is_allin_state"]:
        while len(server["board"]) < 5:
            time.sleep(1.5)
            if not server["board"]: server["board"].extend([server["deck"].pop() for _ in range(3)])
            else: server["board"].append(server["deck"].pop())
            st.rerun()
        server["game_status"] = "SHOWDOWN"; server["is_allin_state"] = False; st.rerun()

    # 호스트 관리
    if is_host:
        with st.sidebar:
            st.title("HOST MENU")
            if st.button("RESET SERVER"): server["players"] = {}; server["game_status"] = "WAITING"; st.rerun()
            if server["game_status"] == "SHOWDOWN":
                st.write("### WINNER SELECTION")
                if st.button(f"{p_names[0]} WIN"): award_pot(p_names[0]); st.rerun()
                if st.button(f"{p_names[1]} WIN"): award_pot(p_names[1]); st.rerun()
            elif len(p_names) == 2 and server["game_status"] == "WAITING":
                if st.button("DEAL NEXT HAND"):
                    deck = [r+s for s in ['♠','♥','♦','♣'] for r in ['2','3','4','5','6','7','8','9','10','J','Q','K','A']]; random.shuffle(deck)
                    btn = server["btn_idx"]; bb = 1 - btn
                    server["players"][p_names[btn]].update({"hand": [deck.pop(), deck.pop()], "bet": 50.0, "stack": server["players"][p_names[btn]]["stack"]-50.0, "acted": False})
                    server["players"][p_names[bb]].update({"hand": [deck.pop(), deck.pop()], "bet": 100.0, "stack": server["players"][p_names[bb]]["stack"]-100.0, "acted": False})
                    server.update({"deck": deck, "board": [], "game_status": "PLAYING", "pot": 0.0, "current_bet": 100.0, "current_turn_idx": btn, "btn_idx": 1-btn})
                    st.rerun()
