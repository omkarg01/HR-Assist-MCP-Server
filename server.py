from datetime import datetime
from typing import List, Dict, Optional
import os

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from emails import EmailSender
from hrms import *
from utils import seed_services

load_dotenv()

employee_manager = EmployeeManager()
meeting_manager = MeetingManager()
leave_manager = LeaveManager()
ticket_manager = TicketManager()

seed_services(employee_manager, leave_manager, meeting_manager, ticket_manager)

_email_user = (os.getenv("CB_EMAIL") or "").strip()
_email_pwd = (os.getenv("CB_EMAIL_PWD") or "").strip()
emailer = None
if _email_user and _email_pwd and "your" not in _email_user.lower():
    emailer = EmailSender(
        smtp_server="smtp.gmail.com",
        port=587,
        username=_email_user,
        password=_email_pwd,
        use_tls=True,
    )

mcp = FastMCP("hr-assist")


@mcp.tool()
def list_employees() -> str:
    """
    List all sample employees with IDs, roles, departments, and managers.
    Use this before creating a new employee so you know valid manager IDs/names.
    """
    return employee_manager.format_directory(managers_only=False)


@mcp.tool()
def list_managers() -> str:
    """
    List managers you can assign when creating a new employee.
    Preferred manager IDs: E001 (Sarah Johnson), E002 (Michael Chen),
    E003 (David Wilson), E006 (Emily Kim), E009 (Priya Nair).
    """
    return employee_manager.format_directory(managers_only=True)


@mcp.tool()
def add_employee(emp_name: str, manager_id: str = "E001", email: str = "") -> str:
    """
    Add a new employee to the HRMS system.

    :param emp_name: New employee full name
    :param manager_id: Manager employee ID OR manager name.
        Examples: "E001", "Sarah Johnson", "David Wilson".
        Defaults to E001 (Sarah Johnson) if omitted.
    :param email: Employee email. If empty, auto-generated as name@atliq.com
    :return: Confirmation message with new employee ID
    """
    resolved_manager = employee_manager.resolve_manager_id(manager_id)
    if not email:
        slug = "".join(ch.lower() if ch.isalnum() else "." for ch in emp_name).strip(".")
        while ".." in slug:
            slug = slug.replace("..", ".")
        email = f"{slug}@atliq.com"

    emp = EmployeeCreate(
        emp_id=employee_manager.get_next_emp_id(),
        name=emp_name,
        manager_id=resolved_manager,
        email=email,
    )
    employee_manager.add_employee(emp)
    # Ensure leave balance exists for the new hire
    _ = leave_manager.get_leave_balance(emp.emp_id)
    leave_manager.employee_leaves[emp.emp_id]["balance"] = 20

    manager_label = "none"
    if resolved_manager:
        mgr = employee_manager.get_employee_details(resolved_manager)
        manager_label = f"{resolved_manager} ({mgr['name']})"

    return (
        f"Employee {emp_name} added successfully.\n"
        f"- emp_id: {emp.emp_id}\n"
        f"- email: {email}\n"
        f"- manager: {manager_label}\n"
        f"Tip: call list_managers() to see valid managers."
    )


@mcp.tool()
def get_employee_details(name: str) -> Dict[str, str]:
    """
    Get employee details by name (or partial name).
    :param name: Name of the employee, e.g. "Tony" or "Sarah Johnson"
    :return: Employee details
    """
    matches = employee_manager.search_employee_by_name(name)

    if len(matches) == 0:
        directory = employee_manager.format_directory()
        raise ValueError(f"No employees found with name '{name}'. Known employees:\n{directory}")

    emp_id = matches[0]
    details = employee_manager.get_employee_details(emp_id)
    manager_id = employee_manager.manager_map.get(emp_id)
    return {
        **details,
        "manager_id": manager_id or "",
        "manager_name": (
            employee_manager.employees[manager_id]["name"] if manager_id else ""
        ),
    }


@mcp.tool()
def send_email(to_emails: List[str], subject: str, body: str, html: bool = False) -> str:
    if emailer is None:
        return (
            "Email skipped: set CB_EMAIL and CB_EMAIL_PWD in .env to enable sending. "
            f"Would have sent to {to_emails} | subject={subject}"
        )
    emailer.send_email(subject, body, to_emails, from_email=emailer.username, html=html)
    return "Email sent successfully."


@mcp.tool()
def create_ticket(emp_id: str, item: str, reason:str) -> str:
    """
    Create a ticket for buying required items for an employee.
    :param emp_id: Employee ID
    :param item: Item requested (Laptop, ID Card, etc.)
    :param reason: Reason for the request
    :return: Confirmation message
    """
    ticket_req = TicketCreate(emp_id=emp_id, item=item, reason=reason)
    return ticket_manager.create_ticket(ticket_req)

@mcp.tool()
def update_ticket_status(ticket_id: str, status: str) -> str:
    """
    Update the status of a ticket.
    :param ticket_id: Ticket ID
    :param status: New status of the ticket
    :return: Confirmation message
    """
    ticket_status_update = TicketStatusUpdate(status=status)
    return ticket_manager.update_ticket_status(ticket_status_update, ticket_id)

@mcp.tool()
def list_tickets(employee_id: str = "", status: str = "") -> str:
    """
    List tickets for an employee with optional status filter.
    :param employee_id: Employee ID (optional)
    :param status: Ticket status (optional)
    :return: List of tickets
    """
    return ticket_manager.list_tickets(
        employee_id=employee_id or None,
        status=status or None,
    )


@mcp.tool()
def schedule_meeting(employee_id: str, meeting_datetime: datetime, topic: str) -> str:
    """
    Schedule a meeting for an employee.
    :param employee_id: Employee ID
    :param meeting_datetime: Date and time of the meeting in python datetime format
    :param topic: Topic of the meeting
    :return: Confirmation message
    """
    meeting_req = MeetingCreate(
        emp_id=employee_id,
        meeting_dt=meeting_datetime,
        topic=topic
    )
    return meeting_manager.schedule_meeting(meeting_req)


@mcp.tool()
def get_meetings(employee_id: str) -> str:
    """
    Get the list of meetings scheduled for an employee.
    :param employee_id: Employee ID
    :return: List of meetings
    """
    return meeting_manager.get_meetings(employee_id)


@mcp.tool()
def cancel_meeting(employee_id: str, meeting_datetime: datetime, topic: str) -> str:
    """
    Cancel a scheduled meeting for an employee.
    :param employee_id: Employee ID
    :param meeting_datetime: Date and time of the meeting in python datetime format
    :param topic: Topic of the meeting (optional)
    :return: Confirmation message
    """
    meeting_req = MeetingCancelRequest(
        emp_id=employee_id,
        meeting_dt=meeting_datetime,
        topic=topic
    )
    return meeting_manager.cancel_meeting(meeting_req)


@mcp.tool()
def get_employee_leave_balance(emp_id: str) -> str:
    """
    Get the leave balance of an employee.
    :param emp_id: Employee ID
    :return: Leave balance message
    """
    return leave_manager.get_leave_balance(emp_id)

@mcp.tool()
def apply_leave(emp_id: str, leave_dates: list) -> str:
    """
    Apply for leave for an employee.
    :param emp_id: Employee ID
    :param leave_dates: List of leave dates
    :return: Leave application status message
    """
    req = LeaveApplyRequest(emp_id=emp_id, leave_dates=leave_dates)
    return leave_manager.apply_leave(req)


@mcp.tool()
def get_leave_history(emp_id: str) -> str:
    """
    Get the leave history of an employee.
    :param emp_id: Employee ID
    :return: Leave history message
    """
    return leave_manager.get_leave_history(emp_id)


@mcp.prompt("onboard_new_employee")
def onboard_new_employee(employee_name: str, manager_name: str = "Sarah Johnson"):
    return f"""Onboard a new employee with the following details:
    - Name: {employee_name}
    - Manager Name: {manager_name}

    Sample managers you can use:
    - E001 Sarah Johnson (VP Engineering)
    - E002 Michael Chen (VP Product)
    - E003 David Wilson (Engineering Manager)
    - E006 Emily Kim (Product Manager)
    - E009 Priya Nair (HR Manager)

    Steps to follow:
    - Call list_managers if needed, then add_employee with manager name or ID.
    - Send a welcome email to the employee with their login credentials. (Format: employee_name@atliq.com)
    - Notify the manager about the new employee's onboarding.
    - Raise tickets for a new laptop, id card, and other necessary equipment.
    - Schedule an introductory meeting between the employee and the manager.
    """



if __name__ == "__main__":
    mcp.run(transport="stdio")
