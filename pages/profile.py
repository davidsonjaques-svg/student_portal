import streamlit as st
from utils.database import get_db
import hashlib


def show():
    user = st.session_state.user

    st.markdown("""
    <div class="page-header">
        <div>
            <h1 class="page-title">My Profile</h1>
            <p class="page-sub">Manage your account details and preferences.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_left, col_right = st.columns([1, 2])

    with col_left:
        initials = "".join([n[0].upper() for n in user['full_name'].split()[:2]])
        st.markdown(f"""
        <div class="profile-card">
            <div class="big-avatar">{initials}</div>
            <div class="profile-name-lg">{user['full_name']}</div>
            <div class="profile-detail">🏠 Room {user['room_number']}</div>
            <div class="profile-detail">🆔 {user['student_number']}</div>
            <div class="profile-detail">📧 {user['email']}</div>
            <div class="profile-detail">🎓 {"Admin" if user['role'] == 'admin' else 'Student'}</div>
            <div class="profile-detail">📅 Member since {user['created_at'][:10]}</div>
        </div>
        """, unsafe_allow_html=True)

    with col_right:
        tab1, tab2 = st.tabs(["✏️ Edit Profile", "🔒 Change Password"])

        with tab1:
            st.markdown("#### Update your details")
            new_name = st.text_input("Full Name", value=user['full_name'], key="edit_name")
            new_room = st.text_input("Room Number", value=user['room_number'], key="edit_room")
            new_bio = st.text_area("Bio (optional)", value=user.get('profile_bio', ''), placeholder="Tell the residence a bit about yourself...", key="edit_bio")

            if st.button("Save Changes", type="primary", key="save_profile"):
                conn = get_db()
                c = conn.cursor()
                c.execute("""
                    UPDATE users SET full_name = ?, room_number = ?, profile_bio = ?
                    WHERE id = ?
                """, (new_name, new_room, new_bio, user['id']))
                conn.commit()
                row = c.execute("SELECT * FROM users WHERE id = ?", (user['id'],)).fetchone()
                conn.close()
                st.session_state.user = dict(row)
                st.success("Profile updated.")
                st.rerun()

        with tab2:
            st.markdown("#### Change your password")
            current_pw = st.text_input("Current Password", type="password", key="cur_pw")
            new_pw = st.text_input("New Password", type="password", key="new_pw")
            confirm_pw = st.text_input("Confirm New Password", type="password", key="confirm_pw")

            if st.button("Update Password", type="primary", key="update_pw"):
                if not all([current_pw, new_pw, confirm_pw]):
                    st.error("All fields are required.")
                elif new_pw != confirm_pw:
                    st.error("New passwords do not match.")
                elif len(new_pw) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    cur_hash = hashlib.sha256(current_pw.encode()).hexdigest()
                    if cur_hash != user['password_hash']:
                        st.error("Current password is incorrect.")
                    else:
                        new_hash = hashlib.sha256(new_pw.encode()).hexdigest()
                        conn = get_db()
                        conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, user['id']))
                        conn.commit()
                        conn.close()
                        st.success("Password updated successfully.")
