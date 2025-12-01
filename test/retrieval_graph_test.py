import os
import sys
# 현재 파일의 상위 디렉토리(프로젝트 루트)를 Python 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from backend.retrieval_graph.graph import graph as retrieval_graph
from langchain_core.messages import HumanMessage
import asyncio
import nest_asyncio
nest_asyncio.apply()

from dotenv import load_dotenv
load_dotenv(override=True)

async def main():
    """
    컴파일된 LangGraph 그래프를 실행하는 메인 함수
    """
    # 1. 그래프에 전달할 입력값 정의
    # InputState 스키마에 따라 'messages' 키에 대화 내용을 리스트로 담습니다.
    inputs = {
        "messages": [
            HumanMessage(content="최신 kbo계약을 알려줘.")
        ]
    }

    #     results = await graph.ainvoke(
    #     {
    #         "messages": [("human", inputs["question"])],
    #     }
    # )

    # 2. (선택 사항) 실행 시점에 특정 설정을 전달할 수 있습니다.
    # AgentConfiguration에 정의된 필드들을 변경할 수 있습니다.
    # 예를 들어, 응답 생성 모델을 claude-3-5-sonnet으로 변경
    # config = {
    #     "configurable": {
    #         "response_model": "anthropic/claude-3-5-sonnet-20240620"
    #     }
    # }

    print("▶️ 그래프 실행을 시작합니다...")
    
    # 3. ainvoke를 사용하여 그래프를 비동기적으로 실행합니다.
    # 첫 번째 인자로 입력값(inputs)을, config 인자로 설정값을 전달합니다.
    final_state = await retrieval_graph.ainvoke(inputs)

    print("\n✅ 그래프 실행 완료!")
    
    # 4. 최종 결과 확인
    # invoke는 그래프의 최종 상태(AgentState)를 반환합니다.
    # 'answer' 필드에 최종 생성된 답변이 들어있습니다.
    print("\n[최종 답변]")
    print(final_state.get('answer', '답변을 생성하지 못했습니다.'))

    # 최종 상태의 다른 정보들도 확인할 수 있습니다.
    # print("\n[수행된 리서치 단계]")
    # print(final_state.get('steps')) # 이 시점에는 비어있을 것입니다.
    # print("\n[검색된 문서 개수]")
    # print(len(final_state.get('documents', [])))

    # 리소스가 정상적으로 닫힐 수 있도록 짧은 대기 시간을 줍니다.
    await asyncio.sleep(0)

if __name__ == "__main__":
    asyncio.run(main())