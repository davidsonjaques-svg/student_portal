import streamlit as st
from utils.database import get_db
from datetime import datetime

NOTICE_CATEGORIES = ["General", "Lost & Found", "For Sale", "Events", "Study Groups", "Carpooling", "Accommodation", "Other"]


def show():
    user = st.session_state.user
    st.markdown("""
    <div class="page-header">
        <div>
            <h1 class="page-title">📋 Notice Board</h1>
            <p class="page-sub">Community notices posted by students and management.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📌 View Notices", "✍️ Post a Notice"])

    with tab1:
        conn = get_db()
        c = conn.cursor()

        col1, col2 = st.columns([2, 1])
        with col1:
            search = st.text_input("Search notices", placeholder="Search by title or keyword...", key="notice_search")
        with col2:
            cat_filter = st.selectbox("Category", ["All"] + NOTICE_CATEGORIES, key="notice_cat_filter")

        query = """
            SELECT n.*, u.full_name, u.room_number FROM notices n
            JOIN users u ON n.user_id = u.id
            WHERE 1=1
        """
        params = []
        if search:
            query += " AND (n.title LIKE ? OR n.body LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])
        if cat_filter != "All":
            query += " AND n.category = ?"
            params.append(cat_filter)

        query += " ORDER BY n.pinned DESC, n.created_at DESC"
        c.execute(query, params)
        notices = c.fetchall()
        conn.close()

        if not notices:
            st.info("No notices found.")
        else:
            for n in notices:
                pin_str = "📌 " if n["pinned"] else ""
                is_mine = n["user_id"] == user["id"]
                is_admin = user.get("role") == "admin"

                with st.container():
                    st.markdown(f"""
                    <div class="notice-card {'pinned-notice' if n['pinned'] else ''}">
                        <div class="notice-header">
                            <span class="notice-title">{pin_str}{n['title']}</span>
                            <span class="notice-cat-tag">{n['category']}</span>
                        </div>
                        <div class="notice-body">{n['body']}</div>
                        <div class="notice-footer">
                            Posted by <strong>{n['full_name']}</strong> · Room {n['room_number']} · {n['created_at'][:10]}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    if is_mine or is_admin:
                        if st.button(f"🗑 Delete", key=f"del_notice_{n['id']}"):
                            conn2 = get_db()
                            conn2.execute("DELETE FROM notices WHERE id = ?", (n['id'],))
                            conn2.commit()
                            conn2.close()
                            st.success("Notice removed.")
                            st.rerun()

    with tab2:
        st.markdown("### Post a New Notice")
        st.caption("Share something with the residence community. Please keep it respectful and relevant.")

        notice_title = st.text_input("Notice Title", placeholder="e.g. Selling mini-fridge in good condition", key="new_notice_title")
        notice_cat = st.selectbox("Category", NOTICE_CATEGORIES, key="new_notice_cat")
        notice_body = st.text_area("Notice Content", placeholder="Provide all relevant details here...", height=150, key="new_notice_body")

        if st.button("Post Notice", type="primary", use_container_width=True, key="post_notice_btn"):
            if not notice_title or not notice_body:
                st.error("Please fill in all fields.")
            else:
                conn = get_db()
                c = conn.cursor()
                c.execute("""
                    INSERT INTO notices (user_id, title, body, category)
                    VALUES (?, ?, ?, ?)
                """, (user['id'], notice_title, notice_body, notice_cat))
                conn.commit()
                conn.close()
                st.success("✅ Notice posted successfully!")
                st.rerun()
