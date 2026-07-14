"""ChatGPT-style Streamlit frontend for the AI Healthcare Care Coordinator.

This talks to the existing FastAPI backend over HTTP only (via `requests`);
it does not import any backend modules directly except for the read-only
admin dashboard pages, which query the database directly exactly as the
original project did. The chat experience is intentionally modeled after
ChatGPT / Gemini: dark theme, left sidebar with conversation history, chat
bubbles with avatars, streaming responses with a typing indicator, markdown
rendering, and file upload.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Generator, Optional

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

from config import settings
from database.session import SessionLocal
from models.models import Appointment, Doctor, Medicine, Patient, Treatment

API_BASE_URL = settings.API_BASE_URL.rstrip("/")
USER_AVATAR = "🧑"
ASSISTANT_AVATAR = "🩺"
APP_TITLE = settings.APP_NAME

st.set_page_config(page_title=APP_TITLE, page_icon="🩺", layout="wide")


# ----------------------------------------------------------------------
# Styling: mobile-friendly tweaks + chat bubble polish on top of the
# dark theme already defined in .streamlit/config.toml
# ----------------------------------------------------------------------
st.markdown(
    """
    <style>
    .app-brand {
        display: flex;
        align-items: center;
        gap: 10px;
        font-size: 1.15rem;
        font-weight: 700;
        margin-bottom: 4px;
    }
    .app-tagline {
        color: #8ea0ba;
        font-size: 0.85rem;
        margin-bottom: 18px;
    }
    .thread-btn button {
        text-align: left !important;
        justify-content: flex-start !important;
    }
    [data-testid="stChatMessage"] {
        border-radius: 16px;
        padding: 4px 2px;
    }
    @media (max-width: 700px) {
        [data-testid="stSidebar"] { width: 240px !important; }
        .app-tagline { display: none; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ----------------------------------------------------------------------
# API helper functions (all talk to the FastAPI backend over HTTP)
# ----------------------------------------------------------------------
def api_login(username: str, password: str) -> Optional[str]:
    try:
        resp = requests.post(
            f"{API_BASE_URL}/api/auth/login",
            data={"username": username, "password": password},
            timeout=15,
        )
        if resp.status_code == 200:
            return resp.json().get("access_token")
        return None
    except requests.RequestException as exc:
        st.error(f"Could not reach the backend at {API_BASE_URL}: {exc}")
        return None


def api_register(username: str, email: str, password: str, full_name: str) -> tuple[bool, str]:
    try:
        resp = requests.post(
            f"{API_BASE_URL}/api/auth/register",
            json={
                "username": username,
                "email": email,
                "password": password,
                "full_name": full_name,
                "role": "patient",
            },
            timeout=15,
        )
        if resp.status_code == 200:
            return True, "Account created successfully. You can now log in."
        detail = resp.json().get("detail", "Registration failed.")
        return False, detail
    except requests.RequestException as exc:
        return False, f"Could not reach the backend at {API_BASE_URL}: {exc}"


def _auth_headers() -> dict:
    token = st.session_state.get("access_token")
    return {"Authorization": f"Bearer {token}"} if token else {}


def api_stream_chat(message: str) -> Generator[str, None, None]:
    """Streams the assistant's reply from /api/assistant/chat/stream."""
    try:
        with requests.post(
            f"{API_BASE_URL}/api/assistant/chat/stream",
            json={"message": message},
            headers=_auth_headers(),
            stream=True,
            timeout=120,
        ) as resp:
            if resp.status_code != 200:
                yield f"The assistant returned an error (HTTP {resp.status_code}). Please try again."
                return
            for chunk in resp.iter_content(chunk_size=None, decode_unicode=True):
                if chunk:
                    yield chunk
    except requests.RequestException as exc:
        yield f"I couldn't reach the backend at `{API_BASE_URL}`. Please make sure the FastAPI server is running. ({exc})"


def api_upload_file(uploaded_file) -> str:
    try:
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
        resp = requests.post(
            f"{API_BASE_URL}/api/assistant/upload",
            files=files,
            headers=_auth_headers(),
            timeout=60,
        )
        if resp.status_code == 200:
            data = resp.json()
            return f"📎 Uploaded **{uploaded_file.name}** successfully. {data.get('summary', '')}"
        return f"File upload failed (HTTP {resp.status_code})."
    except requests.RequestException as exc:
        return f"File upload failed: {exc}"


# ----------------------------------------------------------------------
# Session state
# ----------------------------------------------------------------------
def _new_thread(title: str = "New chat") -> str:
    thread_id = str(uuid.uuid4())
    st.session_state.threads[thread_id] = {
        "title": title,
        "messages": [
            {
                "role": "assistant",
                "content": (
                    "Hi, I'm your **AI Healthcare Care Coordinator**. 👋\n\n"
                    "I can help with appointments, medications, treatments, doctor "
                    "questions, and general health education. What can I help you with today?"
                ),
            }
        ],
    }
    return thread_id


if "access_token" not in st.session_state:
    st.session_state.access_token = None
if "username" not in st.session_state:
    st.session_state.username = None
if "threads" not in st.session_state:
    st.session_state.threads = {}
if "active_thread_id" not in st.session_state:
    st.session_state.active_thread_id = _new_thread()


# ----------------------------------------------------------------------
# Sidebar
# ----------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        f'<div class="app-brand">🩺 {APP_TITLE}</div>'
        '<div class="app-tagline">Your always-on healthcare companion</div>',
        unsafe_allow_html=True,
    )

    # ---- Auth ----
    if st.session_state.access_token:
        st.success(f"Signed in as **{st.session_state.username}**")
        if st.button("Log out", use_container_width=True):
            st.session_state.access_token = None
            st.session_state.username = None
            st.rerun()
    else:
        with st.expander("🔐 Log in / Sign up", expanded=False):
            tab_login, tab_register = st.tabs(["Log in", "Sign up"])
            with tab_login:
                login_user = st.text_input("Username", key="login_user")
                login_pass = st.text_input("Password", type="password", key="login_pass")
                if st.button("Log in", key="login_btn", use_container_width=True):
                    token = api_login(login_user, login_pass)
                    if token:
                        st.session_state.access_token = token
                        st.session_state.username = login_user
                        st.rerun()
                    else:
                        st.error("Invalid username or password.")
            with tab_register:
                reg_name = st.text_input("Full name", key="reg_name")
                reg_user = st.text_input("Username", key="reg_user")
                reg_email = st.text_input("Email", key="reg_email")
                reg_pass = st.text_input("Password", type="password", key="reg_pass")
                if st.button("Create account", key="reg_btn", use_container_width=True):
                    ok, msg = api_register(reg_user, reg_email, reg_pass, reg_name)
                    (st.success if ok else st.error)(msg)
        st.caption("You can also chat as a guest without logging in.")

    st.divider()

    # ---- New chat / history ----
    if st.button("➕ New chat", use_container_width=True):
        st.session_state.active_thread_id = _new_thread()
        st.rerun()

    st.caption("Conversation history")
    for thread_id, thread in reversed(list(st.session_state.threads.items())):
        label = ("📌 " if thread_id == st.session_state.active_thread_id else "💬 ") + thread["title"]
        with st.container():
            if st.button(label, key=f"thread_{thread_id}", use_container_width=True):
                st.session_state.active_thread_id = thread_id
                st.rerun()

    st.divider()
    if st.button("🗑️ Clear current chat", use_container_width=True):
        active = st.session_state.active_thread_id
        st.session_state.threads[active]["messages"] = st.session_state.threads[active]["messages"][:1]
        st.rerun()

    st.divider()
    page = st.selectbox(
        "Workspace",
        [
            "AI Assistant",
            "Dashboard",
            "Patients",
            "Doctors",
            "Appointments",
            "Treatments",
            "Medications",
            "Reports",
            "Analytics",
            "Settings",
        ],
    )


# ----------------------------------------------------------------------
# AI Assistant (ChatGPT-style chat page)
# ----------------------------------------------------------------------
if page == "AI Assistant":
    st.markdown(f"### 🩺 {APP_TITLE}")
    st.caption("Healthcare topics only — symptoms, medications, treatments, appointments, and more.")

    active_thread = st.session_state.threads[st.session_state.active_thread_id]

    chat_container = st.container()
    with chat_container:
        for msg in active_thread["messages"]:
            avatar = USER_AVATAR if msg["role"] == "user" else ASSISTANT_AVATAR
            with st.chat_message(msg["role"], avatar=avatar):
                st.markdown(msg["content"])

    uploaded_file = st.file_uploader(
        "Attach a file (optional)", label_visibility="collapsed", key=f"upload_{st.session_state.active_thread_id}"
    )
    if uploaded_file is not None:
        upload_result = api_upload_file(uploaded_file)
        active_thread["messages"].append({"role": "assistant", "content": upload_result})
        st.rerun()

    prompt = st.chat_input("Ask about your care plan, medications, symptoms, or appointments...")

    if prompt:
        active_thread["messages"].append({"role": "user", "content": prompt})
        if active_thread["title"] == "New chat":
            active_thread["title"] = (prompt[:32] + "…") if len(prompt) > 32 else prompt

        with chat_container:
            with st.chat_message("user", avatar=USER_AVATAR):
                st.markdown(prompt)

            with st.chat_message("assistant", avatar=ASSISTANT_AVATAR):
                placeholder = st.empty()
                placeholder.markdown("_🩺 typing…_")
                full_response = ""
                for chunk in api_stream_chat(prompt):
                    full_response += chunk
                    placeholder.markdown(full_response + "▌")
                placeholder.markdown(full_response or "_(no response)_")

        active_thread["messages"].append({"role": "assistant", "content": full_response})
        st.rerun()


# ----------------------------------------------------------------------
# Admin / operations dashboard pages (preserved from the original project)
# ----------------------------------------------------------------------
else:
    session = SessionLocal()
    try:
        if page == "Dashboard":
            st.header("Operations Summary")
            patient_count = session.query(Patient).count()
            doctor_count = session.query(Doctor).count()
            appointment_count = session.query(Appointment).count()
            treatment_count = session.query(Treatment).count()

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Patients", patient_count)
            col2.metric("Doctors", doctor_count)
            col3.metric("Appointments", appointment_count)
            col4.metric("Treatments", treatment_count)

            chart_data = pd.DataFrame(
                {
                    "Category": ["Patients", "Doctors", "Appointments", "Treatments"],
                    "Count": [patient_count, doctor_count, appointment_count, treatment_count],
                }
            )
            fig = px.pie(chart_data, names="Category", values="Count", title="Healthcare Workload Distribution")
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#f6f8fc")
            st.plotly_chart(fig, use_container_width=True)

        elif page == "Patients":
            st.header("Patient Records")
            patients = session.query(Patient).all()
            patient_df = pd.DataFrame(
                [
                    {
                        "ID": p.id,
                        "Name": f"{p.first_name} {p.last_name}",
                        "Email": p.email,
                        "Phone": p.phone,
                        "Conditions": p.medical_conditions,
                    }
                    for p in patients
                ]
            )
            st.dataframe(patient_df, use_container_width=True)

        elif page == "Doctors":
            st.header("Doctors")
            doctors = session.query(Doctor).all()
            doctor_df = pd.DataFrame(
                [
                    {"ID": d.id, "Name": f"{d.first_name} {d.last_name}", "Specialty": d.specialty, "Email": d.email}
                    for d in doctors
                ]
            )
            st.dataframe(doctor_df, use_container_width=True)

        elif page == "Appointments":
            st.header("Appointments")
            appointments = session.query(Appointment).all()
            appointment_df = pd.DataFrame(
                [
                    {
                        "ID": a.id,
                        "Patient ID": a.patient_id,
                        "Doctor ID": a.doctor_id,
                        "Scheduled Time": a.scheduled_time,
                        "Status": a.status,
                    }
                    for a in appointments
                ]
            )
            st.dataframe(appointment_df, use_container_width=True)

        elif page == "Treatments":
            st.header("Treatment Plans")
            treatments = session.query(Treatment).all()
            treatment_df = pd.DataFrame(
                [
                    {
                        "ID": t.id,
                        "Patient ID": t.patient_id,
                        "Doctor ID": t.doctor_id,
                        "Status": t.status,
                        "Plan": t.plan,
                    }
                    for t in treatments
                ]
            )
            st.dataframe(treatment_df, use_container_width=True)

        elif page == "Medications":
            st.header("Medication Reminders")
            medicines = session.query(Medicine).all()
            medicine_df = pd.DataFrame(
                [
                    {
                        "ID": m.id,
                        "Patient ID": m.patient_id,
                        "Name": m.name,
                        "Dosage": m.dosage,
                        "Frequency": m.frequency,
                    }
                    for m in medicines
                ]
            )
            st.dataframe(medicine_df, use_container_width=True)

        elif page == "Reports":
            st.header("Reports")
            st.write("Generate patient, doctor, and appointment reports from the API backend.")

        elif page == "Analytics":
            st.header("Analytics")
            st.write("Analytics capabilities are available via FastAPI endpoints and will be expanded in production.")

        elif page == "Settings":
            st.header("Settings")
            st.write(f"Backend API base URL: `{API_BASE_URL}`")
            st.write("Configure environment variables (API keys, SMTP, etc.) in the `.env` file.")
            st.write(f"Server time: {datetime.utcnow().isoformat()} UTC")
    finally:
        session.close()
