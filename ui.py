
import streamlit as st
import re
from langchain_community.utilities import SQLDatabase
from langchain_experimental.sql import SQLDatabaseChain
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate

st.set_page_config(page_title="AI Data Assistant", layout="centered")

st.title("🤖 AI Data Assistant")
st.caption("Ask questions about your e-commerce dataset using natural language")

@st.cache_resource
def load_chain():
    db = SQLDatabase.from_uri("sqlite:///ecommerce.db")
    llm = OllamaLLM(model="llama3")

    prompt = PromptTemplate(
        input_variables=["input", "table_info", "top_k"],
        template="""
You are an expert SQLite assistant.

STRICT RULES:
- Output ONLY a valid SQL query
- No explanation

Table: events

Question: {input}
"""
    )

    return SQLDatabaseChain.from_llm(
        llm,
        db,
        verbose=False,
        prompt=prompt,
        return_direct=True
    )

db_chain = load_chain()

query = st.text_input("💬 Ask your question")

if query:
    with st.spinner("Thinking..."):
        try:
            response = db_chain.invoke(query)

            if isinstance(response, str):
                result = response
            else:
                result = response.get("result", response)

            match = re.search(r"\[\((\d+),?\)\]", str(result))
            if match:
                result = match.group(1)

            st.success(f"✅ Answer: {result}")

        except Exception as e:
            st.error(f"❌ Error: {e}")