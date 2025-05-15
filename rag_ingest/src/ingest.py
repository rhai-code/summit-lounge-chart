#!/usr/bin/env python3
import requests
import urllib.parse

from bs4 import BeautifulSoup
from argparse import ArgumentParser
from langchain.text_splitter import MarkdownTextSplitter
from langchain_core.documents import Document
from langchain_milvus import Milvus
from langchain_openai import OpenAIEmbeddings


parser = ArgumentParser(prog="ingest.py", description="Tool to ingest a remote listing markdown files into a RAG database")

parser.add_argument("markdown", help="The file reference to ingest")
parser.add_argument("database", help="The database ingest it to")
parser.add_argument("embeddings", help="The URL of the OpenAI compatible embeddings endpoint")

args = parser.parse_args()

listing = requests.get(args.markdown)
soup = BeautifulSoup(listing.text, 'html.parser')

splitter = MarkdownTextSplitter(chunk_size=2000, chunk_overlap=200)
mds = []
for link in soup.find_all('a'):
    url = urllib.parse.urljoin(args.markdown, link.get('href'))
    mds.append(requests.get(url).text)

documents = splitter.create_documents(mds)

from pprint import pprint

embeddings = OpenAIEmbeddings(
    api_key="fake",
    openai_api_base=args.embeddings,
    model="intfloat/multilingual-e5-large",
)
vectorstore = Milvus.from_documents(
    documents=documents,
    embedding=embeddings,
    connection_args={
        "uri": args.database,
    },
    drop_old=True
)
from pprint import pprint
pprint(vectorstore.__dict__)
