import streamlit as st
from utils.database import get_db
from datetime import datetime


def show():
    user = st.session_state.user

    st.markdown(f"""
    <div class="page-header">
        <div>
            <h1 class="page-title">Good {"morning" if datetime.now().hour < 12 else "afternoon" if datetime.now().hour < 18 else "evening"}, {user['full_name'].split()[0]} 👋</h1>
            <p class="page-sub">Here's what's happening at the residence today.</p>
        </div>
        <div class="header-meta">
            <span class="room-badge">Room {user['room_number']}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    conn = get_db()
    c = conn.cursor()

    # Stats
    c.execute("SELECT COUNT(*) FROM queries WHERE user_id = ?", (user['id'],))
    total_queries = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM queries WHERE user_id = ? AND status = 'open'", (user['id'],))
    open_queries = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM queries WHERE user_id = ? AND status = 'resolved'", (user['id'],))
    resolved_queries = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM notices WHERE user_id = ?", (user['id'],))
    my_notices = c.fetchone()[0]

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-icon">🔧</div>
            <div class="stat-num">{total_queries}</div>
            <div class="stat-label">Total Queries</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="stat-card stat-orange">
            <div class="stat-icon">⏳</div>
            <div class="stat-num">{open_queries}</div>
            <div class="stat-label">Open Queries</div>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="stat-card stat-green">
            <div class="stat-icon">✅</div>
            <div class="stat-num">{resolved_queries}</div>
            <div class="stat-label">Resolved</div>
        </div>""", unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="stat-card stat-purple">
            <div class="stat-icon">📋</div>
            <div class="stat-num">{my_notices}</div>
            <div class="stat-label">My Notices Posted</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='margin-top:2rem'></div>", unsafe_allow_html=True)

    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.markdown("### 📢 Management Announcements")
        c.execute("SELECT a.*, u.full_name FROM announcements a JOIN users u ON a.user_id = u.id ORDER BY a.created_at DESC LIMIT 5")
        announcements = c.fetchall()

        if not announcements:
            st.info("No announcements at this time.")
        else:
            for ann in announcements:
                urgency_class = "urgent" if ann["urgent"] else ""
                st.markdown(f"""
                <div class="announcement-card {urgency_class}">
                    <div class="ann-header">
                        {"🚨 " if ann['urgent'] else "📌 "}<strong>{ann['title']}</strong>
                        {"<span class='urgent-tag'>URGENT</span>" if ann['urgent'] else ""}
                    </div>
                    <p class="ann-body">{ann['body']}</p>
                    <div class="ann-meta">Management · {ann['created_at'][:10]}</div>
                </div>
                """, unsafe_allow_html=True)

    with col_right:
        st.markdown("### 🔧 My Recent Queries")
        c.execute("""
            SELECT * FROM queries WHERE user_id = ? 
            ORDER BY created_at DESC LIMIT 4
        """, (user['id'],))
        recent_queries = c.fetchall()

        if not recent_queries:
            st.info("No queries logged yet.")
            if st.button("Log your first query →", type="primary"):
                st.session_state.page = "queries"
                st.rerun()
        else:
            for q in recent_queries:
                status_colors = {"open": "#f59e0b", "in_progress": "#3b82f6", "resolved": "#10b981"}
                color = status_colors.get(q["status"], "#6b7280")
                st.markdown(f"""
                <div class="mini-query-card">
                    <div class="mq-title">{q['title']}</div>
                    <div class="mq-meta">
                        <span class="mq-cat">{q['category']}</span>
                        <span class="mq-status" style="color:{color}">● {q['status'].replace('_',' ').title()}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("### 📋 Latest Notices")
        c.execute("""
            SELECT n.*, u.full_name FROM notices n 
            JOIN users u ON n.user_id = u.id 
            ORDER BY n.pinned DESC, n.created_at DESC LIMIT 3
        """)
        latest_notices = c.fetchall()
        for notice in latest_notices:
            pin = "📌 " if notice["pinned"] else ""
            st.markdown(f"""
            <div class="mini-notice-card">
                <div class="mn-title">{pin}{notice['title']}</div>
                <div class="mn-meta">{notice['full_name']} · {notice['created_at'][:10]}</div>
            </div>
            """, unsafe_allow_html=True)

    conn.close()
