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

from app.rag.constants import WEAVIATE_GENERAL_GUIDES_AND_TUTORIALS_INDEX_NAME
from app.rag.embeddings import get_embeddings_model
from app.rag.parser import langchain_docs_extractor
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
 
WEAVIATE_HOST = settings.WEAVIATE_HOST
WEAVIATE_PORT = settings.WEAVIATE_PORT
WEAVIATE_GRPC_PORT = settings.WEAVIATE_GRPC_PORT
RECORD_MANAGER_DB_URL = settings.RECORD_MANAGER_DB_URL


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
    print(page_content)

    if not page_content:
        logger.warning(f"No content extracted from URL: {url}")
        return []

    doc = Document(page_content=page_content, metadata=metadata)
    return [doc]

def load_notion_docs(path:str):
    from langchain_community.document_loaders import NotionDirectoryLoader

    loader = NotionDirectoryLoader(path)
    documents = loader.load()
    for document in documents:
        source = document.metadata["source"]
        document.metadata["title"] = source
    return documents

def ingest_docs():
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=4000, chunk_overlap=200)
    embedding = get_embeddings_model()

    with weaviate.connect_to_local(
        host = WEAVIATE_HOST,
        port = WEAVIATE_PORT,
        grpc_port = WEAVIATE_GRPC_PORT,
        skip_init_checks=True
    ) as weaviate_client:
        # General Guides and Tutorials
        general_guides_and_tutorials_vectorstore = WeaviateVectorStore(
            client=weaviate_client,
            index_name=WEAVIATE_GENERAL_GUIDES_AND_TUTORIALS_INDEX_NAME,
            text_key="text",
            embedding=embedding,
            # Weaviate에 쿼리 시 반환할 메타데이터 속성 지정, 따라서 Ducument 저장시에 해당 속성이 반드시 포함되어야 함
            attributes=["source", "title"],
        )

        # 어떤 문서가 이미 벡터 저장소에 저장되었는지 기록하는 역활을 함 (중복 인덱싱 방지)
        record_manager = SQLRecordManager(
            namespace=f"weaviate/{WEAVIATE_GENERAL_GUIDES_AND_TUTORIALS_INDEX_NAME}",
            db_url=RECORD_MANAGER_DB_URL,
        )
        record_manager.create_schema()
        
        # general_guides_and_tutorials_docs = ingest_general_guides_and_tutorials()
        general_guides_and_tutorials_docs = load_single_url("https://m.sports.naver.com/kbaseball/article/022/0004086120")
        # general_guides_and_tutorials_docs = load_notion_docs("/Users/haram/Desktop/카카오부캠/코드/rag-base/test/sample_data/test")

        # 문서 분할
        docs_transformed = text_splitter.split_documents(
            general_guides_and_tutorials_docs
        )
        # 필터링: 너무 짧은 문서는 제외
        docs_transformed = [
            doc for doc in docs_transformed if len(doc.page_content) > 10
        ]

        # weaviate에서 검색을 할 때 metadata의 source, title 필드를 포함하여 반환하도록 설정했으므로 문서에도 해당 필드가 반드시 포함되어야 함
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
            # 벡터db의 metadata에 포함된 source 필드를 고유 식별자로 사용, record_manager에서는 group_id컬럼에 식별자를 저장하여 중복 인덱싱 방지
            # 만약 source_id_key를 사용하지 않는다면 page_content의 해시값이 고유 식별자로 사용됨
            # 문서가 조금만 바껴도 해시값이 달라지기 때문에 동일 문서임에도 불구하고 중복 인덱싱될 수 있음, 따라서 source와 같은 고유 식별자를 사용하는 것이 좋음
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

