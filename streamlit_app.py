"""
HR Assist — Streamlit web app
Uses the same HRMS managers as the MCP server.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Optional

import streamlit as st
from dotenv import load_dotenv

from hrms import (
    EmployeeCreate,
    EmployeeManager,
    LeaveApplyRequest,
    LeaveManager,
    MeetingCancelRequest,
    MeetingCreate,
    MeetingManager,
    TicketCreate,
    TicketManager,
    TicketStatusUpdate,
)
from utils import seed_services

load_dotenv()

st.set_page_config(
    page_title="HR Assist",
    page_icon="👥",
    layout="wide",
)


def _auto_email(name: str) -> str:
    slug = "".join(ch.lower() if ch.isalnum() else "." for ch in name).strip(".")
    while ".." in slug:
        slug = slug.replace("..", ".")
    return f"{slug}@atliq.com"


def init_services() -> None:
    if "ready" in st.session_state:
        return
    em = EmployeeManager()
    lm = LeaveManager()
    mm = MeetingManager()
    tm = TicketManager()
    seed = seed_services(em, lm, mm, tm)
    st.session_state.employee_manager = em
    st.session_state.leave_manager = lm
    st.session_state.meeting_manager = mm
    st.session_state.ticket_manager = tm
    st.session_state.seed = seed
    st.session_state.messages = []
    st.session_state.ready = True


def manager_options() -> list[str]:
    em: EmployeeManager = st.session_state.employee_manager
    opts = []
    for row in em.list_managers():
        opts.append(f"{row['emp_id']} — {row['name']} ({row.get('role') or 'Manager'})")
    return opts


def employee_options() -> list[str]:
    em: EmployeeManager = st.session_state.employee_manager
    return [
        f"{row['emp_id']} — {row['name']}"
        for row in em.list_employees()
    ]


def parse_emp_id(label: str) -> str:
    return label.split("—", 1)[0].strip()


def add_employee_flow(
    name: str,
    manager_label: str,
    email: str = "",
    create_onboarding: bool = True,
) -> str:
    em: EmployeeManager = st.session_state.employee_manager
    lm: LeaveManager = st.session_state.leave_manager
    mm: MeetingManager = st.session_state.meeting_manager
    tm: TicketManager = st.session_state.ticket_manager

    manager_id = parse_emp_id(manager_label) if manager_label else "E001"
    email = email.strip() or _auto_email(name)
    emp_id = em.get_next_emp_id()
    em.add_employee(
        EmployeeCreate(
            emp_id=emp_id,
            name=name.strip(),
            manager_id=manager_id,
            email=email,
        )
    )
    lm.employee_leaves[emp_id]["balance"] = 20

    lines = [
        f"✅ Added **{name}** (`{emp_id}`)",
        f"- Email: `{email}`",
        f"- Manager: `{manager_id}`",
        f"- Leave balance: 20 days",
    ]

    if create_onboarding:
        for item in ("Laptop", "ID Card", "Access Badge"):
            msg = tm.create_ticket(
                TicketCreate(emp_id=emp_id, item=item, reason="New hire setup")
            )
            lines.append(f"- {msg}")
        meeting_dt = datetime.combine(date.today() + timedelta(days=1), time(10, 0))
        meeting_msg = mm.schedule_meeting(
            MeetingCreate(
                emp_id=emp_id,
                meeting_dt=meeting_dt,
                topic="Introductory meeting with manager",
            )
        )
        lines.append(f"- {meeting_msg}")

    return "\n".join(lines)


def render_directory() -> None:
    em: EmployeeManager = st.session_state.employee_manager
    st.subheader("Employee directory")
    rows = em.list_employees()
    st.dataframe(rows, use_container_width=True, hide_index=True)

    st.subheader("Managers")
    st.dataframe(em.list_managers(), use_container_width=True, hide_index=True)


def render_onboard() -> None:
    st.subheader("Onboard new employee")
    managers = manager_options()
    with st.form("onboard_form", clear_on_submit=True):
        name = st.text_input("Full name *", placeholder="Riya Shah")
        manager = st.selectbox("Manager *", managers, index=0)
        email = st.text_input("Email (optional)", placeholder="auto-generated if empty")
        do_tickets = st.checkbox("Create onboarding tickets + intro meeting", value=True)
        submitted = st.form_submit_button("Create employee", type="primary")

    if submitted:
        if not name.strip():
            st.error("Please enter a name.")
            return
        try:
            result = add_employee_flow(name, manager, email, create_onboarding=do_tickets)
            st.success("Employee created")
            st.markdown(result)
        except Exception as exc:
            st.error(str(exc))


def render_leave() -> None:
    st.subheader("Leave")
    employees = employee_options()
    emp_label = st.selectbox("Employee", employees, key="leave_emp")
    emp_id = parse_emp_id(emp_label)
    lm: LeaveManager = st.session_state.leave_manager

    col1, col2 = st.columns(2)
    with col1:
        st.info(lm.get_leave_balance(emp_id))
        st.write(lm.get_leave_history(emp_id))
    with col2:
        with st.form("leave_form"):
            leave_date = st.date_input("Leave date", value=date.today() + timedelta(days=1))
            submitted = st.form_submit_button("Apply leave")
        if submitted:
            try:
                msg = lm.apply_leave(
                    LeaveApplyRequest(emp_id=emp_id, leave_dates=[leave_date])
                )
                st.success(msg)
            except Exception as exc:
                st.error(str(exc))


def render_tickets() -> None:
    st.subheader("Tickets")
    employees = employee_options()
    emp_label = st.selectbox("Employee", employees, key="ticket_emp")
    emp_id = parse_emp_id(emp_label)
    tm: TicketManager = st.session_state.ticket_manager

    tickets = tm.list_tickets(employee_id=emp_id)
    st.dataframe(tickets or [{"info": "No tickets"}], use_container_width=True, hide_index=True)

    with st.form("ticket_form"):
        item = st.selectbox(
            "Item",
            ["Laptop", "Monitor", "Keyboard", "Mouse", "Headset", "ID Card", "Access Badge"],
        )
        reason = st.text_input("Reason", value="New hire setup")
        submitted = st.form_submit_button("Create ticket")
    if submitted:
        msg = tm.create_ticket(TicketCreate(emp_id=emp_id, item=item, reason=reason))
        st.success(msg)
        st.rerun()

    open_tickets = tm.list_tickets(employee_id=emp_id, status="Open")
    if open_tickets:
        with st.form("ticket_status_form"):
            tid = st.selectbox("Update ticket", [t["ticket_id"] for t in open_tickets])
            status = st.selectbox("New status", ["In Progress", "Closed", "Rejected"])
            update = st.form_submit_button("Update status")
        if update:
            msg = tm.update_ticket_status(TicketStatusUpdate(status=status), tid)
            st.success(msg)
            st.rerun()


def render_meetings() -> None:
    st.subheader("Meetings")
    employees = employee_options()
    emp_label = st.selectbox("Employee", employees, key="meeting_emp")
    emp_id = parse_emp_id(emp_label)
    mm: MeetingManager = st.session_state.meeting_manager

    meetings = mm.get_meetings(emp_id)
    st.dataframe(meetings or [{"info": "No meetings"}], use_container_width=True, hide_index=True)

    with st.form("meeting_form"):
        meeting_day = st.date_input("Date", value=date.today() + timedelta(days=1))
        meeting_time = st.time_input("Time", value=time(10, 0))
        topic = st.text_input("Topic", value="1:1 sync")
        submitted = st.form_submit_button("Schedule meeting")
    if submitted:
        try:
            dt = datetime.combine(meeting_day, meeting_time)
            msg = mm.schedule_meeting(
                MeetingCreate(emp_id=emp_id, meeting_dt=dt, topic=topic)
            )
            st.success(msg)
            st.rerun()
        except Exception as exc:
            st.error(str(exc))


def render_lookup() -> None:
    st.subheader("Lookup employee")
    em: EmployeeManager = st.session_state.employee_manager
    query = st.text_input("Name (partial OK)", placeholder="Tony / Sarah / Priya")
    if st.button("Search", type="primary") or query:
        if not query.strip():
            return
        matches = em.search_employee_by_name(query)
        if not matches:
            st.warning("No match. Try list_managers names like Sarah Johnson, David Wilson.")
            return
        for emp_id in matches:
            details = em.get_employee_details(emp_id)
            manager = em.get_manager(emp_id)
            st.json({**details, "manager": manager})


def main() -> None:
    init_services()
    seed = st.session_state.seed

    st.title("HR Assist")
    st.caption(
        "Streamlit front-end for employee onboarding, leave, tickets, and meetings. "
        f"Seeded {seed['employees']} employees · {seed['tickets']} tickets · {seed['meetings']} meetings"
    )

    tab_dir, tab_onboard, tab_leave, tab_tickets, tab_meetings, tab_lookup = st.tabs(
        ["Directory", "Onboard", "Leave", "Tickets", "Meetings", "Lookup"]
    )

    with tab_dir:
        render_directory()
    with tab_onboard:
        render_onboard()
        st.info(
            "Tip: pick a manager from the dropdown (E001 Sarah Johnson, E003 David Wilson, "
            "E009 Priya Nair, etc.)."
        )
    with tab_leave:
        render_leave()
    with tab_tickets:
        render_tickets()
    with tab_meetings:
        render_meetings()
    with tab_lookup:
        render_lookup()

    with st.sidebar:
        st.header("HR Assist")
        st.write("Web UI over the same HRMS used by the MCP server.")
        if st.button("Reset demo data"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        st.divider()
        st.markdown(
            """
**Sample managers**
- E001 Sarah Johnson
- E002 Michael Chen
- E003 David Wilson
- E006 Emily Kim
- E009 Priya Nair
            """
        )


if __name__ == "__main__":
    main()
