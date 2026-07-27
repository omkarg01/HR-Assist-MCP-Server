from collections import defaultdict
from typing import Dict

from hrms.schemas import LeaveApplyRequest


class LeaveManager:
    def __init__(self):
        self.employee_leaves: Dict[str, Dict] = defaultdict(
            lambda: {"balance": 20, "history": []}
        )

    def get_leave_balance(self, employee_id: str) -> str:
        data = self.employee_leaves.get(employee_id)
        if data:
            return f"{employee_id} has {data['balance']} leave days remaining."
        return "Employee ID not found."

    def apply_leave(self, req: LeaveApplyRequest) -> str:
        employee_id = req.emp_id
        if employee_id not in self.employee_leaves:
            return "Employee ID not found."
        requested = len(req.leave_dates)
        available = self.employee_leaves[employee_id]["balance"]
        if available < requested:
            return (
                f"Insufficient leave balance: requested {requested}, available {available}."
            )
        self.employee_leaves[employee_id]["balance"] -= requested
        request_id = (
            max(
                (record.get("request_id", 0) for record in self.employee_leaves[employee_id]["history"]),
                default=0,
            )
            + 1
        )
        for leave_date in req.leave_dates:
            self.employee_leaves[employee_id]["history"].append(
                {
                    "history_id": len(self.employee_leaves[employee_id]["history"]) + 1,
                    "emp_id": employee_id,
                    "leave_date": leave_date,
                    "request_id": request_id,
                }
            )
        return (
            f"Leave applied for {requested} day(s). Remaining balance: "
            f"{self.employee_leaves[employee_id]['balance']}"
        )

    def get_leave_history(self, employee_id: str) -> str:
        data = self.employee_leaves.get(employee_id)
        if not data:
            return "Employee ID not found."
        hist = data["history"]
        dates = []
        for record in hist:
            leave_date = record["leave_date"] if isinstance(record, dict) else record
            if hasattr(leave_date, "strftime"):
                dates.append(leave_date.strftime("%B %d, %Y"))
            else:
                dates.append(str(leave_date))
        return f"Leave history for {employee_id}: {', '.join(dates)}."

if __name__ == "__main__":
    lm = LeaveManager()
    print(lm.get_leave_history("E004"))