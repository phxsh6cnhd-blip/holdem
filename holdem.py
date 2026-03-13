import streamlit as st

# 세션 상태에 액션 관련 데이터 추가
if 'current_turn' not in st.session_state:
    st.session_state.current_turn = 0  # 0: Hero, 1: 상대1, 2: 상대2
if 'my_bet_amount' not in st.session_state:
    st.session_state.my_bet_amount = 0

# --- 게임 함수 ---
def handle_action(action_type):
    hero = st.session_state.players[0]
    
    if action_type == "FOLD":
        st.warning("폴드하셨습니다. 이번 핸드 종료.")
        # 다음 핸드 준비 로직
        
    elif action_type == "CHECK/CALL":
        # 현재 콜해야 할 금액 계산 로직 필요 (여기선 단순화)
        st.success("Check/Call 완료")
        
    elif action_type == "ALL-IN":
        all_in_amount = hero['stack']
        st.session_state.pot += all_in_amount
        hero['stack'] = 0
        st.error(f"🔥 ALL-IN! {all_in_amount}BB를 넣었습니다.")
        
    # 액션 후 다음 사람에게 턴 넘기기
    st.session_state.current_turn = (st.session_state.current_turn + 1) % 3

# --- UI 레이아웃 ---
st.title("♠️ GG-Style Poker Room")

# (테이블 렌더링 부분 생략 - 이전 코드 유지)

# --- 하단 액션 컨트롤러 (내 차례일 때만 활성화) ---
st.divider()

if st.session_state.current_turn == 0: # 내 차례(Hero)인 경우
    st.subheader("Your Action")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("❌ FOLD", use_container_width=True):
            handle_action("FOLD")
            
    with col2:
        # 상황에 따라 Check 또는 Call로 텍스트 변경 가능
        if st.button("✅ CHECK / CALL", use_container_width=True):
            handle_action("CHECK/CALL")
            
    with col3:
        # Raise 버튼 클릭 시 올인!
        if st.button("⬆️ RAISE (ALL-IN)", type="primary", use_container_width=True):
            handle_action("ALL-IN")
            
    # 0BB가 되었는지 체크하여 게임 종료 판단
    if st.session_state.players[0]['stack'] <= 0:
        if st.session_state.pot > 0: # 팟이 아직 분배 전이라면
             st.info("올인 상태입니다. 결과를 확인하세요.")
else:
    st.info(f"⌛ {st.session_state.players[st.session_state.current_turn]['nickname']}의 차례를 기다리는 중...")
