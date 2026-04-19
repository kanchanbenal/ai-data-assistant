

import pandas as pd
import sqlite3
from langchain_community.utilities import SQLDatabase
from langchain_experimental.sql import SQLDatabaseChain
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
# Clean SQL output like [(121398,)] → 121398
import re
print("Step 1: Start")

# Load data
oct_df = pd.read_csv("data/2019-Oct.csv", nrows=100000)
nov_df = pd.read_csv("data/2019-Nov.csv", nrows=100000)

df = pd.concat([oct_df, nov_df])
print("Step 2: Data loaded", df.shape)

# Clean data
df.dropna(inplace=True)
df.drop_duplicates(inplace=True)
print("Step 3: Cleaned", df.shape)

# Save sample
df.to_csv("data/sample.csv", index=False)
print("Step 4: CSV saved")

# Create DB
print("Step 5: Creating DB")
conn = sqlite3.connect("ecommerce.db")

df.to_sql("events", conn, if_exists="replace", index=False)
print("Step 6: DB written")

result = conn.execute("SELECT COUNT(*) FROM events").fetchall()
print("Step 7: Rows:", result)

conn.close()
print("Step 8: Done")

# Connect LangChain
print("Step 9: Connecting to database with LangChain")
db = SQLDatabase.from_uri("sqlite:///ecommerce.db")
print("Connected to DB")

# Load LLM
print("Step 10: Loading LLM...")
llm = OllamaLLM(model="llama3")
print("LLM loaded ")

# Strong prompt
custom_prompt = PromptTemplate(
    input_variables=["input", "table_info", "top_k"],
    template="""
You are an expert SQLite assistant.

STRICT RULES:
- Output ONLY a valid SQL query
- DO NOT include explanations
- DO NOT include words like 'Result' or 'Answer'
- DO NOT include multiple statements
- Return ONLY ONE SQL query

Table name: events

Question: {input}
"""
)

# Create chatbot
print("Step 11: Creating chatbot...")
db_chain = SQLDatabaseChain.from_llm(
    llm,
    db,
    verbose=True,
    prompt=custom_prompt,
    return_direct=True   
)

print("Chatbot ready ")

import re

# Chat loop
while True:
    query = input("\nAsk your question (type 'exit' to quit): ")

    if query.lower() == "exit":
        break

    try:
        response = db_chain.invoke(query)

        # handle both string and dict
        if isinstance(response, str):
            result = response
        else:
            result = response.get("result", response)

        # extract number from [(121398,)]
        match = re.search(r"\[\((\d+),?\)\]", str(result))
        if match:
            result = match.group(1)

        print("\nAnswer:", result)

    except Exception as e:
        print("Error:", e)