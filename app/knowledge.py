from pathlib import Path
from .config import FAQ_PATH, CHROMA_PATH

_faq_store = None

def _build_store():
    global _faq_store
    try:
        from langchain_community.document_loaders import TextLoader
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        from langchain_groq import ChatGroq
        from langchain_community.embeddings import FakeEmbeddings
        from langchain_chroma import Chroma
        # FakeEmbeddings keeps the demo key-free for embeddings, but is not suitable for production retrieval.
        docs = TextLoader(str(FAQ_PATH), encoding="utf-8").load()
        chunks = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=80).split_documents(docs)
        _faq_store = Chroma.from_documents(
            documents=chunks,
            embedding=FakeEmbeddings(size=384),
            persist_directory=str(CHROMA_PATH),
            collection_name="support_faqs"
        )
        return _faq_store
    except Exception:
        return None

def search_faqs(query: str) -> str:
    global _faq_store
    if _faq_store is None:
        _faq_store = _build_store()
    if _faq_store is not None:
        try:
            docs = _faq_store.similarity_search(query, k=3)
            if docs:
                return "\n\n".join(d.page_content for d in docs)
        except Exception:
            pass
    # Robust lightweight fallback: keyword matching against FAQ sections.
    text = FAQ_PATH.read_text(encoding="utf-8")
    terms = [t.lower().strip(".,?!") for t in query.split() if len(t) > 3]
    sections = [s.strip() for s in text.split("\n## ") if s.strip()]
    scored = sorted(
        ((sum(term in section.lower() for term in terms), section) for section in sections),
        key=lambda item: item[0], reverse=True
    )
    relevant = [section for score, section in scored[:3] if score > 0]
    return "\n\n".join(relevant) if relevant else "No closely matching FAQ was found. Escalate if the customer needs a definitive answer."
