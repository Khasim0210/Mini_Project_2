import streamlit as st
import psycopg2
import pandas as pd
import google.generativeai as genai
import os

# 🔑 Connection string for Render PostgreSQL
CONN_STRING = (
    "postgresql://mini_project_2_xaqr_user:"
    "wjoxSyAypH75Opn6djCf3cbjChPr9Kt4"
    "@dpg-d4lu10euk2gs738k06jg-a.oregon-postgres.render.com/mini_project_2_xaqr"
)

APP_PASSWORD = "myproject"  # change password if needed

# 🌟 Gemini API Key (from Streamlit secrets or environment)
gemini_key = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY"))

# Configure Gemini if key is present
if gemini_key:
    genai.configure(api_key=gemini_key)

# Safest text model that should exist for most keys with google-generativeai 0.7.x
GEMINI_MODEL_NAME = "gemini-1.0-pro"


def get_conn():
    """Create a new PostgreSQL connection."""
    return psycopg2.connect(CONN_STRING)


def check_password():
    """
    Simple password gate for the app.
    """
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
    Wrapper to call Gemini (google-generativeai 0.7.2).
    Returns a short, clear answer or an error message.
    """
    if not gemini_key:
        return "No Gemini API key configured. Please set GEMINI_API_KEY in your environment or Streamlit secrets."

    try:
        # Create model instance
        model = genai.GenerativeModel(GEMINI_MODEL_NAME)

        # You can pass a single string as the content for text-only use
        full_prompt = (
            "You are a helpful assistant for a sales database project. "
            "Answer clearly and briefly.\n\n"
            f"User: {prompt}"
        )

        response = model.generate_content(full_prompt)

        # response.text contains the generated text
        return response.text

    except Exception as e:
        # Bubble up useful error info to the UI
        return f"Error talking to Gemini: {e}"


def main():
    st.set_page_config(page_title="Sales Dashboard", layout="wide")
    st.title("🛒 Sales Dashboard — Render DB Viewer (Gemini Powered)")

    # Password gate
    if not check_password():
        st.stop()

    col1, col2 = st.columns(2)

    # 🔹 LEFT SIDE — Browse Tables
    with col1:
        st.subheader("📁 Tables")

        try:
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

            if not table_list:
                st.warning("No tables found in the 'public' schema.")
            else:
                selected_table = st.selectbox("Select table", table_list)

                limit = st.slider("Rows", 5, 50, 10)
                query = f'SELECT * FROM "{selected_table}" LIMIT {limit};'
                st.code(query, language="sql")

                preview = pd.read_sql(query, conn)
                st.dataframe(preview, use_container_width=True)

        except Exception as e:
            st.error(f"Error reading tables: {e}")
        finally:
            try:
                conn.close()
            except Exception:
                pass

    # 🔹 RIGHT SIDE — Run Custom Queries + Gemini Helper
    with col2:
        st.subheader("🧪 Run SQL")

        default_query = 'SELECT * FROM "Product" LIMIT 5;'
        user_query = st.text_area("Write SQL query", default_query, height=140)

        if st.button("Run Query"):
            try:
                conn = get_conn()
                result = pd.read_sql(user_query, conn)
                st.dataframe(result, use_container_width=True)
            except Exception as e:
                st.error(str(e))
            finally:
                try:
                    conn.close()
                except Exception:
                    pass

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
