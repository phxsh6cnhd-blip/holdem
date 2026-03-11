# --- 상대 플레이어 영역 (수정 및 확인용) ---
with col_right: 
    opp_name = [n for n in p_names if n != my_name][0] if len(p_names) > 1 else "..."
    st.markdown(f"👤 **{opp_name}**")
    
    # 쇼다운 상태이거나 올인 런아웃이 끝났을 때만 상대 카드 공개
    if server["game_status"] == "SHOWDOWN":
        opp_hand = server["players"][opp_name]["hand"]
        opp_hand_html = "".join([render_card(c) for c in opp_hand])
        st.markdown(f"<div style='display:flex; justify-content:center;'>{opp_hand_html}</div>", unsafe_allow_html=True)
    else:
        # 평소에는 카드 뒷면 표시
        st.markdown("<div style='display:flex; justify-content:center;'><div class='card-back'></div><div class='card-back'></div></div>", unsafe_allow_html=True)
    
    if len(p_names) > 1:
        st.write(f"<span class='stack-val'>{server['players'][opp_name]['stack']:,.0f}</span>", unsafe_allow_html=True)
