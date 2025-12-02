import streamlit as st
import psycopg2
import pandas as pd
import google.generativeai as genai
import os

# 🔑 Connection string for Render PostgreSQL
CONN_STRING = "postgresql://mini_project_2_xaqr_user:wjoxSyAypH75Opn6djCf3cbjChPr9Kt4@dpg-d4lu10euk2gs738k06jg-a.oregon-postgres.render.com/mini_project_2_xaqr"

APP_PASSWORD = "myproject"

# 🌟 Gemini API Key (from Streamlit secrets or environment)
gemini_key = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY"))
genai.configure(api_key=gemini_key)


def get_conn():
    return psycopg2.connect(CONN_STRING)


def check_password():
    if "auth_ok" not in st.session_state:
        st.session_state.auth_ok = False

    if not st.session_state.auth_ok:
        pwd = st.text_input("Enter password", type="password")
        if st.button("Login"):
            if pwd == APP_PASSWORD:
                st.session_state.auth_ok = True
            else:
                st.error("Wrong password ❌")
        return False

    return True


def ask_gemini(prompt: str) -> str:
    """
    Wrapper for Gemini API.
    """
    if not gemini_key:
        return "No Gemini API key configured."

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")

        response = model.generate_content(
            f"You are a helpful assistant for a sales database project. Answer clearly and briefly.\n\nUser: {prompt}"
        )

        return response.text
    except Exception as e:
        return f"Error talking to Gemini: {e}"


def main():
    st.set_page_config(page_title="Sales Dashboard", layout="wide")
    st.title("🛒 Sales Dashboard — Render DB Viewer")

    if not check_password():
        st.stop()

    col1, col2 = st.columns(2)

    # 🔹 LEFT SIDE — Browse Tables
    with col1:
        st.subheader("📁 Tables")

        conn = get_conn()
        tables = pd.read_sql(
            """
            SELECT table_name FROM information_schema.tables
            WHERE table_schema='public'
            ORDER BY table_name;
            """,
            conn,
        )

        table_list = tables["table_name"].tolist()
        selected_table = st.selectbox("Select table", table_list)

        limit = st.slider("Rows", 5, 50, 10)
        query = f'SELECT * FROM "{selected_table}" LIMIT {limit};'
        st.code(query, language="sql")

        preview = pd.read_sql(query, conn)
        conn.close()

        st.dataframe(preview, use_container_width=True)

    # 🔹 RIGHT SIDE — SQL + Gemini Chat
    with col2:
        st.subheader("🧪 Run SQL")

        default_query = 'SELECT * FROM "Product" LIMIT 5;'
        user_query = st.text_area("Write SQL query", default_query, height=140)

        if st.button("Run Query"):
            try:
                conn = get_conn()
                result = pd.read_sql(user_query, conn)
                conn.close()
                st.dataframe(result, use_container_width=True)
            except Exception as e:
                st.error(str(e))

        st.markdown("---")
        st.subheader("🤖 Gemini Helper")

        chat_prompt = st.text_area(
            "Ask Gemini something (about SQL, your data, etc.):",
            "Explain what the Product table represents.",
            height=120,
        )

        if st.button("Ask Gemini"):
            with st.spinner("Gemini is thinking..."):
                answer = ask_gemini(chat_prompt)
                st.markdown("**Answer:**")
                st.write(answer)


if __name__ == "__main__":
    main()