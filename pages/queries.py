import streamlit as st
from utils.database import get_db
from datetime import datetime


CATEGORIES = [
    "Plumbing", "Electrical", "Heating/AC", "Internet/WiFi",
    "Security", "Cleaning", "Noise Complaint", "Parking",
    "Laundry Room", "Common Areas", "Pest Control", "Other"
]

PRIORITIES = ["Low", "Medium", "High", "Urgent"]


def show():
    user = st.session_state.user
    st.markdown("""
    <div class="page-header">
        <div>
            <h1 class="page-title">Maintenance & Queries</h1>
            <p class="page-sub">Log issues, track progress, and communicate with management.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📋 My Queries", "➕ Log New Query"])

    with tab1:
        conn = get_db()
        c = conn.cursor()

        # Filter bar
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            filter_status = st.selectbox("Filter by Status", ["All", "Open", "In Progress", "Resolved"], key="q_status_filter")
        with col2:
            filter_cat = st.selectbox("Filter by Category", ["All"] + CATEGORIES, key="q_cat_filter")
        with col3:
            st.markdown("<br>", unsafe_allow_html=True)

        query = "SELECT * FROM queries WHERE user_id = ?"
        params = [user['id']]

        if filter_status != "All":
            query += " AND status = ?"
            params.append(filter_status.lower().replace(" ", "_"))

        if filter_cat != "All":
            query += " AND category = ?"
            params.append(filter_cat)

        query += " ORDER BY created_at DESC"
        c.execute(query, params)
        queries = c.fetchall()
        conn.close()

        if not queries:
            st.info("No queries found. Use the 'Log New Query' tab to submit one.")
        else:
            for q in queries:
                status_map = {
                    "open": ("🟡", "#f59e0b", "Open"),
                    "in_progress": ("🔵", "#3b82f6", "In Progress"),
                    "resolved": ("🟢", "#10b981", "Resolved"),
                    "closed": ("⚫", "#6b7280", "Closed"),
                }
                priority_map = {
                    "low": "🔽 Low", "medium": "▶️ Medium",
                    "high": "🔼 High", "urgent": "🚨 Urgent"
                }
                icon, color, label = status_map.get(q["status"], ("⚪", "#ccc", q["status"]))

                with st.expander(f"{icon} {q['title']}  —  {q['category']}  ·  {q['created_at'][:10]}"):
                    col_a, col_b, col_c = st.columns(3)
                    col_a.metric("Status", label)
                    col_b.metric("Priority", priority_map.get(q["priority"], q["priority"]))
                    col_c.metric("Logged", q["created_at"][:10])

                    st.markdown("**Description**")
                    st.write(q["description"])

                    if q["admin_response"]:
                        st.markdown("---")
                        st.markdown("**🏢 Management Response**")
                        st.info(q["admin_response"])
                    else:
                        st.caption("_Awaiting management response._")

    with tab2:
        st.markdown("### Submit a New Query")
        st.caption("All fields are required. Urgent issues will be escalated to management immediately.")

        col1, col2 = st.columns(2)
        with col1:
            category = st.selectbox("Category", CATEGORIES, key="new_q_cat")
        with col2:
            priority = st.selectbox("Priority", PRIORITIES, index=1, key="new_q_pri")

        title = st.text_input("Query Title", placeholder="e.g. Shower draining slowly in Room A204", key="new_q_title")
        description = st.text_area("Description", placeholder="Describe the issue in detail — when it started, how often it occurs, and any other relevant context.", height=150, key="new_q_desc")

        st.caption("📍 Your room number will be attached automatically from your profile.")

        if st.button("Submit Query", type="primary", use_container_width=True, key="submit_query"):
            if not title or not description:
                st.error("Please fill in the title and description.")
            else:
                conn = get_db()
                c = conn.cursor()
                c.execute("""
                    INSERT INTO queries (user_id, category, title, description, priority, status)
                    VALUES (?, ?, ?, ?, ?, 'open')
                """, (user['id'], category, title, description, priority.lower()))
                conn.commit()
                conn.close()
                st.success("✅ Query submitted successfully! Management will respond shortly.")
                st.balloons()
