
from app.rag.retrieval_graph.graph import graph as retrieval_graph
from langchain_core.messages import HumanMessage
import asyncio
import nest_asyncio
nest_asyncio.apply()


ios_JD = """

부서 소개

KREAM iOS 팀은 KREAM iOS 앱의 새로운 서비스 개발과 유지 보수 및 성능 개선에 주력합니다.
최적의 서비스 제공과 안정성 유지, 빠른 반응성을 추구하며, Apple의 HIG(Human Interface Guidelines)를 준수하여
사용자에게 편리하고 직관적인 앱을 제공하고, 새로운 iOS 생태계의 변화와 Apple의 새로운 기술을 적극적으로 수용하여
사용자들에게 새로운 경험을 제공하는 것을 목표로 합니다.

KREAM Tech는 한정판 거래 플랫폼을 넘어 글로벌 AI 커머스 서비스로 나아가는 KREAM의 비전을 기술적으로 실현하며,
안정성과 속도를 모두 고려한 개발 문화를 지향합니다.
담당 업무

- KREAM iOS 앱 전반에 관련된 개발 업무 담당
- 서비스 신규 기능 개발
- 거래 프로세스 개발 및 유지 및 보수
- 기존 기능(홈/스타일/샵/마이 등) 개선 및 유지 및 보수
필요 역량

- 3년 이상 iOS 앱 개발 및 출시 경험이 있으신 분
- Swift 개발에 능숙하신 분
- iOS 최신 트렌드를 이용한 개발 경험이 있으신 분
- 적극적으로 문제를 진단하고 창의적으로 해결할 수 있는 능력을 보유하신 분
우대 사항

- iOS 및 Apple의 디자인 철학(HIG)에 대한 이해도가 높으신 분
- SwiftUI 개발 경험이 있으신 분
- 유닛 테스트 및 UI 테스트 작성 경험이 있으신 분
- 스타트업 및 애자일 조직 경험이 있으신 분
- 팀 프로젝트 및 코드 리뷰에 적극적인 성향이신 분
- 적극적이고 논리적인 커뮤니케이션이 가능하신 분
- 최고의 서비스를 만들기 위한 자발적인 목표와 전략을 설정하시는 분
- 커머스 서비스 개발 경험이 있는 분
- 스니커즈 또는 패션 리셀 시장과 문화에 대한 관심이 높으신 분
"""

async def main():

    from dotenv import load_dotenv
    load_dotenv() # .env 파일 로드
    from langfuse.langchain import CallbackHandler
    langfuse_handler = CallbackHandler()

    config = {"callbacks": [langfuse_handler]}

    print("▶️ 그래프 실행을 시작합니다...")
    
    inputs = {
        "messages": [
            HumanMessage(content=ios_JD)
        ]
    }

    final_state = await retrieval_graph.ainvoke(inputs, config=config)

    print("\n✅ 그래프 실행 완료!")
    
    print("\n[최종 답변]")
    print(final_state.get('answer', '답변을 생성하지 못했습니다.'))

    await asyncio.sleep(0)

if __name__ == "__main__":
    asyncio.run(main())