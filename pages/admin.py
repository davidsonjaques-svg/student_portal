import streamlit as st
from utils.database import get_db
from datetime import datetime


def show():
    user = st.session_state.user

    st.markdown("""
    <div class="page-header">
        <div>
            <h1 class="page-title">⚙️ Admin Panel</h1>
            <p class="page-sub">Manage queries, students, announcements, and notices.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["🔧 Manage Queries", "👥 Students", "📢 Announcements", "📊 Overview"])

    with tab1:
        conn = get_db()
        c = conn.cursor()

        col1, col2 = st.columns(2)
        with col1:
            status_filter = st.selectbox("Filter by Status", ["All", "Open", "In Progress", "Resolved", "Closed"], key="admin_q_status")
        with col2:
            priority_filter = st.selectbox("Filter by Priority", ["All", "Urgent", "High", "Medium", "Low"], key="admin_q_prio")

        query = """
            SELECT q.*, u.full_name, u.room_number, u.student_number 
            FROM queries q JOIN users u ON q.user_id = u.id WHERE 1=1
        """
        params = []
        if status_filter != "All":
            query += " AND q.status = ?"
            params.append(status_filter.lower().replace(" ", "_"))
        if priority_filter != "All":
            query += " AND q.priority = ?"
            params.append(priority_filter.lower())

        query += " ORDER BY CASE q.priority WHEN 'urgent' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 ELSE 4 END, q.created_at DESC"
        c.execute(query, params)
        queries = c.fetchall()

        st.markdown(f"**{len(queries)} queries found**")

        for q in queries:
            priority_colors = {"urgent": "🚨", "high": "🔴", "medium": "🟡", "low": "🟢"}
            prio_icon = priority_colors.get(q["priority"], "⚪")
            status_labels = {"open": "Open", "in_progress": "In Progress", "resolved": "Resolved", "closed": "Closed"}

            with st.expander(f"{prio_icon} [{q['status'].upper()}] {q['title']} — {q['full_name']} (Room {q['room_number']})"):
                col_a, col_b, col_c = st.columns(3)
                col_a.write(f"**Student:** {q['full_name']}")
                col_b.write(f"**Room:** {q['room_number']}")
                col_c.write(f"**Student No:** {q['student_number']}")

                st.write(f"**Category:** {q['category']} | **Priority:** {q['priority'].title()} | **Logged:** {q['created_at'][:10]}")
                st.markdown("**Description:**")
                st.write(q["description"])

                st.divider()
                new_status = st.selectbox(
                    "Update Status",
                    ["open", "in_progress", "resolved", "closed"],
                    index=["open", "in_progress", "resolved", "closed"].index(q["status"]),
                    key=f"status_{q['id']}"
                )
                response = st.text_area(
                    "Response to Student",
                    value=q["admin_response"] or "",
                    placeholder="Type your response here. Students will see this on their query.",
                    key=f"resp_{q['id']}"
                )

                if st.button("Update Query", key=f"upd_{q['id']}", type="primary"):
                    conn2 = get_db()
                    conn2.execute("""
                        UPDATE queries SET status = ?, admin_response = ?, updated_at = ?
                        WHERE id = ?
                    """, (new_status, response, datetime.now().isoformat(), q["id"]))
                    conn2.commit()
                    conn2.close()
                    st.success("Query updated.")
                    st.rerun()
        conn.close()

    with tab2:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE role = 'student' ORDER BY full_name")
        students = c.fetchall()
        conn.close()

        st.markdown(f"**{len(students)} registered students**")
        search_s = st.text_input("Search students", placeholder="Name, student number, or room...", key="student_search")

        for s in students:
            if search_s and search_s.lower() not in f"{s['full_name']} {s['student_number']} {s['room_number']}".lower():
                continue
            conn = get_db()
            q_count = conn.execute("SELECT COUNT(*) FROM queries WHERE user_id = ?", (s['id'],)).fetchone()[0]
            conn.close()

            st.markdown(f"""
            <div class="student-row">
                <div class="sr-avatar">{s['full_name'][0].upper()}</div>
                <div class="sr-info">
                    <div class="sr-name">{s['full_name']}</div>
                    <div class="sr-meta">Room {s['room_number']} · {s['student_number']} · {s['email']}</div>
                </div>
                <div class="sr-stats">{q_count} queries</div>
            </div>
            """, unsafe_allow_html=True)

    with tab3:
        conn = get_db()
        c = conn.cursor()

        st.markdown("### Post an Announcement")
        ann_title = st.text_input("Title", key="ann_title", placeholder="e.g. Water shutdown notice")
        ann_body = st.text_area("Message", key="ann_body", height=120, placeholder="Message to all students...")
        ann_urgent = st.checkbox("Mark as Urgent", key="ann_urgent")

        if st.button("Post Announcement", type="primary", key="post_ann"):
            if ann_title and ann_body:
                conn.execute("""
                    INSERT INTO announcements (user_id, title, body, urgent)
                    VALUES (?, ?, ?, ?)
                """, (user['id'], ann_title, ann_body, 1 if ann_urgent else 0))
                conn.commit()
                st.success("Announcement posted to all students.")
                st.rerun()
            else:
                st.error("Please fill in all fields.")

        st.divider()
        st.markdown("### Existing Announcements")
        c.execute("SELECT * FROM announcements ORDER BY created_at DESC")
        anns = c.fetchall()

        for a in anns:
            col1, col2 = st.columns([5, 1])
            with col1:
                st.markdown(f"**{'🚨 ' if a['urgent'] else '📢 '}{a['title']}** · {a['created_at'][:10]}")
                st.caption(a['body'])
            with col2:
                if st.button("Delete", key=f"del_ann_{a['id']}"):
                    conn.execute("DELETE FROM announcements WHERE id = ?", (a['id'],))
                    conn.commit()
                    st.rerun()

        conn.close()

    with tab4:
        conn = get_db()
        c = conn.cursor()

        total_students = c.execute("SELECT COUNT(*) FROM users WHERE role='student'").fetchone()[0]
        total_queries = c.execute("SELECT COUNT(*) FROM queries").fetchone()[0]
        open_q = c.execute("SELECT COUNT(*) FROM queries WHERE status='open'").fetchone()[0]
        in_prog = c.execute("SELECT COUNT(*) FROM queries WHERE status='in_progress'").fetchone()[0]
        resolved = c.execute("SELECT COUNT(*) FROM queries WHERE status='resolved'").fetchone()[0]
        total_notices = c.execute("SELECT COUNT(*) FROM notices").fetchone()[0]
        conn.close()

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Students", total_students)
        col2.metric("Total Queries", total_queries)
        col3.metric("Total Notices", total_notices)

        col4, col5, col6 = st.columns(3)
        col4.metric("Open Queries", open_q, delta=f"-{open_q} to clear" if open_q > 0 else None, delta_color="inverse")
        col5.metric("In Progress", in_prog)
        col6.metric("Resolved", resolved)

        if total_queries > 0:
            resolution_rate = round((resolved / total_queries) * 100)
            st.progress(resolution_rate / 100, text=f"Resolution Rate: {resolution_rate}%")
