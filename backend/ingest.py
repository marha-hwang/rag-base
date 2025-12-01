"""Load html from files, clean up, split, ingest into Weaviate."""

import logging
import os
import re
from typing import Optional

import weaviate
from bs4 import BeautifulSoup, SoupStrainer
from langchain.document_loaders import SitemapLoader
from langchain_core.indexing.api import index
from langchain.indexes import SQLRecordManager
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_weaviate import WeaviateVectorStore
from langchain_core.documents import Document
import requests

from backend.constants import WEAVIATE_GENERAL_GUIDES_AND_TUTORIALS_INDEX_NAME
from backend.embeddings import get_embeddings_model
from backend.parser import langchain_docs_extractor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# override : True 면 기존 시스템 환경변수 덮어쓰고 .env 파일의 값으로 설정
from dotenv import load_dotenv
load_dotenv(override=True)


WEAVIATE_URL = os.environ["WEAVIATE_URL"]
WEAVIATE_API_KEY = os.environ["WEAVIATE_API_KEY"]
RECORD_MANAGER_DB_URL = os.environ["RECORD_MANAGER_DB_URL"]


def metadata_extractor(
    meta: dict, soup: BeautifulSoup, title_suffix: Optional[str] = None
) -> dict:
    title_element = soup.find("title")
    description_element = soup.find("meta", attrs={"name": "description"})
    html_element = soup.find("html")
    title = title_element.get_text() if title_element else ""
    if title_suffix is not None:
        title += title_suffix

    return {
        "source": meta["loc"],
        "title": title,
        "description": description_element.get("content", "")
        if description_element
        else "",
        "language": html_element.get("lang", "") if html_element else "",
        **meta,
    }


def simple_extractor(html: str | BeautifulSoup) -> str:
    if isinstance(html, str):
        soup = BeautifulSoup(html, "lxml")
    elif isinstance(html, BeautifulSoup):
        soup = html
    else:
        raise ValueError(
            "Input should be either BeautifulSoup object or an HTML string"
        )
    return re.sub(r"\n\n+", "\n\n", soup.text).strip()


#########################
# General Guides and Tutorials
#########################


# NOTE: To be deprecated once LangChain docs are migrated to new site.
def load_langchain_python_docs():
    return SitemapLoader(
        "https://python.langchain.com/sitemap.xml",
        filter_urls=["https://python.langchain.com/"],
        parsing_function=langchain_docs_extractor,
        default_parser="lxml",
        bs_kwargs={
            "parse_only": SoupStrainer(
                name=("article", "title", "html", "lang", "content")
            ),
        },
        meta_function=metadata_extractor,
    ).load()


# NOTE: To be deprecated once LangChain docs are migrated to new site.
def load_langchain_js_docs():
    return SitemapLoader(
        "https://js.langchain.com/sitemap.xml",
        parsing_function=simple_extractor,
        default_parser="lxml",
        bs_kwargs={
            "parse_only": SoupStrainer(
                name=("article", "title", "html", "lang", "content")
            )
        },
        meta_function=metadata_extractor,
        filter_urls=["https://js.langchain.com/docs/"],
    ).load()


def load_aggregated_docs_site():
    return SitemapLoader(
        "https://docs.langchain.com/sitemap.xml",
        parsing_function=simple_extractor,
        default_parser="lxml",
        bs_kwargs={
            "parse_only": SoupStrainer(
                name=("article", "title", "html", "lang", "content")
            )
        },
        meta_function=metadata_extractor,
    ).load()


def ingest_general_guides_and_tutorials():
    langchain_python_docs = load_langchain_python_docs()
    langchain_js_docs = load_langchain_js_docs()
    aggregated_site_docs = load_aggregated_docs_site()
    return langchain_python_docs + langchain_js_docs + aggregated_site_docs

def load_single_url(url: str) -> list[Document]:
    """Load a single URL and extract content using custom functions."""
    try:
        response = requests.get(url)
        response.raise_for_status()  # HTTP 에러가 발생하면 예외를 발생시킴
    except requests.RequestException as e:
        logger.error(f"Failed to fetch URL {url}: {e}")
        return []

    # html 내용 출력 (디버깅 용도)
    #print(response.text)

    # 필요한 태그만 파싱
    strainer = SoupStrainer(name=("article", "title", "lang"))
    #strainer = SoupStrainer(name=("article", "title", "html", "lang", "content"))
    # 페이지 파싱
    soup = BeautifulSoup(response.text, "lxml", parse_only=strainer)

    # 기존 메타데이터 및 파싱 함수 재사용
    meta = {"loc": url}
    metadata = metadata_extractor(meta, soup)
    print(metadata)

    page_content = langchain_docs_extractor(soup)
    print(  page_content)

    if not page_content:
        logger.warning(f"No content extracted from URL: {url}")
        return []

    doc = Document(page_content=page_content, metadata=metadata)
    return [doc]

def ingest_docs():
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=4000, chunk_overlap=200)
    embedding = get_embeddings_model()

    with weaviate.connect_to_weaviate_cloud(
        cluster_url=WEAVIATE_URL,
        auth_credentials=weaviate.classes.init.Auth.api_key(WEAVIATE_API_KEY),
        skip_init_checks=True,
    ) as weaviate_client:
        # General Guides and Tutorials
        general_guides_and_tutorials_vectorstore = WeaviateVectorStore(
            client=weaviate_client,
            index_name=WEAVIATE_GENERAL_GUIDES_AND_TUTORIALS_INDEX_NAME,
            text_key="text",
            embedding=embedding,
            attributes=["source", "title"],
        )

        # 중복되는 레코드 관리를 위한 Record Manager 생성
        # SQLRecordManager 는 Weaviate 와 같은 벡터 스토어와 함께 사용하여 인덱싱된 벡터의 메타데이터 및 상태를 관리합니다.
        # 이를 통해 중복 인덱싱을 방지하고, 업데이트된 문서만 재인덱싱할 수 있습니다.
        # 예: 어떤 문서가 이미 인덱싱되었는지 추적
        # Record Manager 는 벡터 스토어와 별도의 데이터베이스에 문서의 고유 식별자, 인덱싱 상태, 타임스탬프 등의 정보를 관리합니다.
        # 예: PostgreSQL, SQLite 등
        # 매번 모든 문서를 임베딩 하는 시간/돈을 절약할 수 있습니다.
        record_manager = SQLRecordManager(
            namespace=f"weaviate/{WEAVIATE_GENERAL_GUIDES_AND_TUTORIALS_INDEX_NAME}",
            db_url=RECORD_MANAGER_DB_URL,
        )
        record_manager.create_schema()
        
        # general_guides_and_tutorials_docs = ingest_general_guides_and_tutorials()
        general_guides_and_tutorials_docs = load_single_url("https://m.sports.naver.com/kbaseball/article/022/0004086120")

        # 문서 분할
        docs_transformed = text_splitter.split_documents(
            general_guides_and_tutorials_docs
        )
        # 필터링: 너무 짧은 문서는 제외
        docs_transformed = [
            doc for doc in docs_transformed if len(doc.page_content) > 10
        ]

        # We try to return 'source' and 'title' metadata when querying vector store and
        # Weaviate will error at query time if one of the attributes is missing from a
        # retrieved document.
        for doc in docs_transformed:
            if "source" not in doc.metadata:
                doc.metadata["source"] = ""
            if "title" not in doc.metadata:
                doc.metadata["title"] = ""
        indexing_stats = index(
            docs_transformed,
            record_manager,
            general_guides_and_tutorials_vectorstore,
            cleanup="full",
            source_id_key="source",
            force_update=(os.environ.get("FORCE_UPDATE") or "false").lower() == "true",
        )
        logger.info(f"Indexing stats: {indexing_stats}")
        num_vecs = (
            weaviate_client.collections.get(
                WEAVIATE_GENERAL_GUIDES_AND_TUTORIALS_INDEX_NAME
            )
            .aggregate.over_all()
            .total_count
        )
        logger.info(
            f"General Guides and Tutorials now has this many vectors: {num_vecs}",
        )


if __name__ == "__main__":
    ingest_docs()
