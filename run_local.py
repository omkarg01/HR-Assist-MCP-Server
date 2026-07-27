"""
Local demo runner for HR Assist (no Claude Desktop required).

Exercises the same HRMS managers used by the MCP server tools.
"""

from datetime import date, datetime, timedelta

from dotenv import load_dotenv

from hrms import (
    EmployeeCreate,
    EmployeeManager,
    LeaveApplyRequest,
    LeaveManager,
    MeetingCreate,
    MeetingManager,
    TicketCreate,
    TicketManager,
    TicketStatusUpdate,
)
from utils import seed_services

load_dotenv()


def main() -> None:
    employee_manager = EmployeeManager()
    leave_manager = LeaveManager()
    meeting_manager = MeetingManager()
    ticket_manager = TicketManager()

    seed = seed_services(employee_manager, leave_manager, meeting_manager, ticket_manager)
    print("=== HR Assist local demo ===")
    print(
        f"Seeded employees={seed['employees']}, leave_records={seed['leave_records']}, "
        f"meetings={seed['meetings']}, tickets={seed['tickets']}"
    )
    print()
    print("Sample managers (use these when creating employees):")
    print(employee_manager.format_directory(managers_only=True))
    print()
    print("All sample employees:")
    print(employee_manager.format_directory())
    print()

    # Lookup existing employee
    matches = employee_manager.search_employee_by_name("Tony Sharma")
    if not matches:
        tony_id = "E004"
    else:
        tony_id = matches[0]
    print("Employee lookup (Tony Sharma):", employee_manager.get_employee_details(tony_id))
    print("Leave balance:", leave_manager.get_leave_balance(tony_id))
    print()

    # Onboarding-style flow — manager can be ID or name
    new_id = employee_manager.get_next_emp_id()
    employee_manager.add_employee(
        EmployeeCreate(
            emp_id=new_id,
            name="Omkar Patel",
            manager_id="Sarah Johnson",  # name also works; or use "E001"
            email="omkar.patel@atliq.com",
        )
    )
    leave_manager.employee_leaves[new_id]["balance"] = 20
    print(f"Added employee {new_id}: Omkar Patel (manager resolved from 'Sarah Johnson')")

    ticket_msg = ticket_manager.create_ticket(
        TicketCreate(emp_id=new_id, item="Laptop", reason="New hire setup")
    )
    print(ticket_msg)
    print("Open tickets:", ticket_manager.list_tickets(employee_id=new_id, status="Open"))

    meeting_dt = datetime.now() + timedelta(days=1)
    meeting_msg = meeting_manager.schedule_meeting(
        MeetingCreate(
            emp_id=new_id,
            meeting_dt=meeting_dt,
            topic="Introductory meeting with manager",
        )
    )
    print(meeting_msg)
    print("Meetings:", meeting_manager.get_meetings(new_id))

    leave_msg = leave_manager.apply_leave(
        LeaveApplyRequest(emp_id=tony_id, leave_dates=[date.today() + timedelta(days=7)])
    )
    print(leave_msg)
    print(leave_manager.get_leave_history(tony_id))

    # Update a ticket if one exists
    open_tickets = ticket_manager.list_tickets(employee_id=new_id, status="Open")
    if open_tickets:
        tid = open_tickets[0]["ticket_id"]
        print(
            ticket_manager.update_ticket_status(
                TicketStatusUpdate(status="In Progress"), tid
            )
        )

    print()
    print("Local demo completed successfully.")
    print("To run as MCP server:  uv run python server.py")
    print("Or with inspector:     npx @modelcontextprotocol/inspector uv run python server.py")


if __name__ == "__main__":
    main()
