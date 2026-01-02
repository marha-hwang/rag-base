from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from dotenv import load_dotenv
load_dotenv() # .env 파일 로드

from langfuse.langchain import CallbackHandler
langfuse_handler = CallbackHandler()
 
llm = ChatOpenAI(model_name="gpt-4o-mini")
prompt = ChatPromptTemplate.from_template("Tell me a joke about {topic}")
chain = prompt | llm
 
response = chain.invoke(
    {"topic": "cats"}, 
    config={"callbacks": [langfuse_handler]}
)