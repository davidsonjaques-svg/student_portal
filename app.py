import streamlit as st
from datetime import datetime
import hashlib
import json
import os
from utils.database import init_db, get_db
from utils.auth import login_user, register_user, get_current_user
from pages import dashboard, queries, notices, admin, profile

st.set_page_config(
    page_title="ResLife Portal",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load CSS
with open("assets/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Initialise DB
init_db()

# Session state defaults
if "user" not in st.session_state:
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "dashboard"


def show_login():
    st.markdown("""
    <div class="auth-container">
        <div class="auth-logo">
            <div class="logo-icon">🏠</div>
            <h1 class="logo-title">ResLife Portal</h1>
            <p class="logo-sub">Student Residence Management System</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Sign In", "Register"])

    with tab1:
        with st.container():
            st.markdown('<div class="auth-form">', unsafe_allow_html=True)
            email = st.text_input("Email address", key="login_email", placeholder="student@university.ac.za")
            password = st.text_input("Password", type="password", key="login_password", placeholder="Enter your password")

            if st.button("Sign In", use_container_width=True, type="primary", key="login_btn"):
                if email and password:
                    user = login_user(email, password)
                    if user:
                        st.session_state.user = user
                        st.success(f"Welcome back, {user['full_name'].split()[0]}!")
                        st.rerun()
                    else:
                        st.error("Invalid email or password.")
                else:
                    st.warning("Please enter your email and password.")
            st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        with st.container():
            st.markdown('<div class="auth-form">', unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                first_name = st.text_input("First Name", key="reg_first")
            with col2:
                last_name = st.text_input("Last Name", key="reg_last")

            reg_email = st.text_input("Student Email", key="reg_email", placeholder="student@university.ac.za")
            student_number = st.text_input("Student Number", key="reg_student_no", placeholder="e.g. 202312345")
            room_number = st.text_input("Room Number", key="reg_room", placeholder="e.g. A204")

            col3, col4 = st.columns(2)
            with col3:
                reg_password = st.text_input("Password", type="password", key="reg_password")
            with col4:
                confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm")

            if st.button("Create Account", use_container_width=True, type="primary", key="reg_btn"):
                if not all([first_name, last_name, reg_email, student_number, room_number, reg_password]):
                    st.warning("Please complete all fields.")
                elif reg_password != confirm_password:
                    st.error("Passwords do not match.")
                elif len(reg_password) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    full_name = f"{first_name} {last_name}"
                    result = register_user(full_name, reg_email, student_number, room_number, reg_password)
                    if result["success"]:
                        st.success("Account created! Please sign in.")
                    else:
                        st.error(result["message"])
            st.markdown('</div>', unsafe_allow_html=True)


def show_sidebar():
    user = st.session_state.user
    is_admin = user.get("role") == "admin"

    with st.sidebar:
        st.markdown(f"""
        <div class="sidebar-profile">
            <div class="avatar">{user['full_name'][0].upper()}</div>
            <div class="profile-info">
                <div class="profile-name">{user['full_name']}</div>
                <div class="profile-meta">Room {user['room_number']} · {user['student_number']}</div>
                {"<span class='admin-badge'>Admin</span>" if is_admin else ""}
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        nav_items = [
            ("🏠", "Dashboard", "dashboard"),
            ("🔧", "Log a Query", "queries"),
            ("📋", "Notice Board", "notices"),
            ("👤", "My Profile", "profile"),
        ]
        if is_admin:
            nav_items.append(("⚙️", "Admin Panel", "admin"))

        for icon, label, page_key in nav_items:
            active = "nav-active" if st.session_state.page == page_key else ""
            if st.sidebar.button(f"{icon}  {label}", key=f"nav_{page_key}",
                                  use_container_width=True,
                                  type="primary" if st.session_state.page == page_key else "secondary"):
                st.session_state.page = page_key
                st.rerun()

        st.divider()
        if st.button("🚪  Sign Out", use_container_width=True, key="signout"):
            st.session_state.user = None
            st.session_state.page = "dashboard"
            st.rerun()

        st.markdown("""
        <div class="sidebar-footer">
            <small>ResLife Portal v1.0<br>Powered by ScaleForce Capital</small>
        </div>
        """, unsafe_allow_html=True)


def main():
    if st.session_state.user is None:
        show_login()
    else:
        show_sidebar()
        page = st.session_state.page
        if page == "dashboard":
            dashboard.show()
        elif page == "queries":
            queries.show()
        elif page == "notices":
            notices.show()
        elif page == "profile":
            profile.show()
        elif page == "admin":
            if st.session_state.user.get("role") == "admin":
                admin.show()
            else:
                st.error("Access denied.")


if __name__ == "__main__":
    main()
