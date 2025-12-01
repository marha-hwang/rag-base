# from langchain.llms import OpenAI  <-- (X) 구버전
from langchain_openai import ChatOpenAI # <-- (O) 최신 버전 (ChatOpenAI 사용)
from langchain_community.callbacks.streamlit import StreamlitCallbackHandler
from dotenv import load_dotenv
import streamlit as st

# .env 파일에서 환경 변수 로드
load_dotenv()

st.title("💬 My GPT-like Chat")

# 
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 수정된 부분 ---
# 1. ChatOpenAI를 사용해야 'gpt-3.5-turbo'나 'gpt-4' 같은 대화형 모델이 호출됩니다.
# 2. streaming=True로 설정해야 글자가 써지는 효과를 볼 수 있습니다.
llm = ChatOpenAI(
    model="gpt-4o",  # 또는 "gpt-3.5-turbo"
    temperature=0, 
    streaming=True
)
# ------------------

if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        st_callback = StreamlitCallbackHandler(st.container())
        
        # invoke에 문자열(prompt)을 바로 넣어도 알아서 HumanMessage로 변환해 줍니다.
        response = llm.invoke(prompt, config={"callbacks": [st_callback]})
        
        # response는 객체(AIMessage)이므로 .content를 뽑아서 저장해야 깔끔합니다.
        st.session_state.messages.append({"role": "assistant", "content": response.content})
        st.markdown(response.content) # StreamlitCallbackHandler가 있어도 최종 결과는 한번 더 찍어주는 게 안전함