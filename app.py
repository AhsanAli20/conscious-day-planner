import os
import sqlite3
from datetime import datetime
import streamlit as st
from dotenv import load_dotenv
from langchain.chat_models import ChatOpenAI


# Load environment variables

load_dotenv()
api_key =  st.secrets["general"]["OPENROUTER_API_KEY"]
if not api_key:
    st.error("❌ OPENROUTER_API_KEY not found in .env file.")
    st.stop()

# Database setup

DB_FILE = "entries.db"
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    journal TEXT,
    intention TEXT,
    dream TEXT,
    priorities TEXT,
    reflection TEXT,
    strategy TEXT
)
""")
conn.commit()

# LangChain LLM setup

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.7,
    openai_api_key=api_key,
    base_url="https://openrouter.ai/api/v1"
)

PROMPT_TEMPLATE = """
You are a daily reflection and planning assistant. Your goal is to:
1. Reflect on the user's journal and dream input
2. Interpret the user's emotional and mental state
3. Understand their intention and 3 priorities
4. Generate a practical, energy-aligned strategy for their day

INPUT:
Morning Journal: {journal}
Intention: {intention}
Dream: {dream}
Top 3 Priorities: {priorities}

OUTPUT:
Reflection:
(Write the Inner Reflection Summary, Dream Interpretation Summary, and Energy/Mindset Insight here)

Strategy:
(Write only the Suggested Day Strategy here in clear bullet points)
"""

# Sidebar Navigation

st.sidebar.title("📌 Menu")
menu = st.sidebar.radio("Go to", ["🆕 New Entry", "📜 View Past Entries"])

# New Entry Page

if menu == "🆕 New Entry":
    st.title("🧠 Conscious Day Planner — New Entry")

    journal = st.text_area("Morning Journal")
    intention = st.text_input("Today's Intention")
    dream = st.text_area("Last Night's Dream")
    priorities = st.text_input("Top 3 Priorities (comma separated)")

    if st.button("Generate Plan"):
        if not (journal and intention and dream and priorities):
            st.error("Please fill all fields before generating.")
        else:
            with st.spinner("Thinking..."):
                prompt = PROMPT_TEMPLATE.format(
                    journal=journal,
                    intention=intention,
                    dream=dream,
                    priorities=priorities
                )
                response = llm.invoke(prompt).content

                # Split output
                reflection_text = ""
                strategy_text = ""
                if "Strategy:" in response:
                    parts = response.split("Strategy:")
                    reflection_text = parts[0].replace("Reflection:", "").strip()
                    strategy_text = parts[1].strip()
                else:
                    reflection_text = response.strip()

                # Save to database
                date_str = datetime.now().strftime("%Y-%m-%d")
                cursor.execute("""
                    INSERT INTO entries (date, journal, intention, dream, priorities, reflection, strategy)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (date_str, journal, intention, dream, priorities, reflection_text, strategy_text))
                conn.commit()

                # Show results
                st.subheader("🪞 Reflection")
                st.write(reflection_text)
                st.subheader("📅 Day Strategy")
                st.write(strategy_text if strategy_text else "No separate strategy generated.")

# View Past Entries Page

elif menu == "📜 View Past Entries":
    st.title("📜 Past Entries")

    # Search inputs
    search_date = st.date_input("Search by Date", value=None)
    search_text = st.text_input("Search by Keyword (Journal/Intention)")

    # Build query
    query = "SELECT id, date, journal, intention, dream, priorities, reflection, strategy FROM entries WHERE 1=1"
    params = []

    if search_date:
        query += " AND date = ?"
        params.append(search_date.strftime("%Y-%m-%d"))

    if search_text:
        query += " AND (journal LIKE ? OR intention LIKE ?)"
        params.extend([f"%{search_text}%", f"%{search_text}%"])

    query += " ORDER BY id DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()

    if not rows:
        st.info("No entries found.")
    else:
        for row in rows:
            st.markdown(f"### 📆 {row[1]}")
            st.write("**Journal:**", row[2])
            st.write("**Intention:**", row[3])
            st.write("**Dream:**", row[4])
            st.write("**Priorities:**", row[5])
            st.write("**Reflection:**", row[6])
            st.write("**Strategy:**", row[7] if row[7] else "—")

            if st.button(f"Delete Entry {row[0]}"):
                cursor.execute("DELETE FROM entries WHERE id = ?", (row[0],))
                conn.commit()
                st.success(f"Entry {row[0]} deleted successfully!")
                st.experimental_rerun()  # Refresh page to update list

conn.close()

