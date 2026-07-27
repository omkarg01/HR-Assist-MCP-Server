from typing import List, Dict, Optional
from difflib import get_close_matches
from hrms.schemas import EmployeeCreate


class EmployeeManager:
    def __init__(self):
        self.employees: Dict[str, Dict[str, str]] = {}
        self.manager_map: Dict[str, Optional[str]] = {}

    def get_next_emp_id(self) -> str:
        """
        Generate the next employee ID based on the existing IDs.
        """
        if not self.employees:
            return "E001"
        max_id = max(int(eid[1:]) for eid in self.employees.keys())
        return f"E{max_id + 1:03}"

    def resolve_manager_id(self, manager_ref: Optional[str]) -> Optional[str]:
        """
        Resolve a manager reference that may be an employee ID or a name.
        Empty / None means no manager.
        """
        if manager_ref is None:
            return None
        ref = str(manager_ref).strip()
        if not ref or ref.lower() in {"none", "null", "n/a", "-"}:
            return None
        if ref in self.employees:
            return ref
        matches = self.search_employee_by_name(ref)
        if not matches:
            known = self.format_directory(managers_only=True)
            raise ValueError(
                f"Manager '{manager_ref}' not found. Use a manager ID or name from:\n{known}"
            )
        return matches[0]

    def add_employee(self, emp: EmployeeCreate) -> None:
        """
        Add a new employee via Pydantic model.
        Raises ValueError if emp_id exists or manager_id is invalid.
        """
        name = emp.name
        manager_id = self.resolve_manager_id(emp.manager_id)
        if emp.emp_id in self.employees:
            raise ValueError(f"Employee ID '{emp.emp_id}' already exists.")
        payload = emp.model_dump()
        payload["manager_id"] = manager_id
        self.employees[emp.emp_id] = payload
        self.manager_map[emp.emp_id] = manager_id

    def list_employees(self) -> List[Dict[str, str]]:
        rows = []
        for emp_id, data in sorted(self.employees.items()):
            manager_id = self.manager_map.get(emp_id)
            manager_name = self.employees[manager_id]["name"] if manager_id else "—"
            rows.append(
                {
                    "emp_id": emp_id,
                    "name": data["name"],
                    "email": data.get("email") or "",
                    "role": data.get("role") or "",
                    "department": data.get("department") or "",
                    "manager_id": manager_id or "",
                    "manager_name": manager_name,
                }
            )
        return rows

    def list_managers(self) -> List[Dict[str, str]]:
        manager_ids = {mgr for mgr in self.manager_map.values() if mgr}
        # Also include top-level people with no manager (leadership)
        for emp_id, mgr in self.manager_map.items():
            if mgr is None:
                manager_ids.add(emp_id)
        rows = []
        for emp_id in sorted(manager_ids):
            data = self.employees[emp_id]
            reports = self.get_direct_reports(emp_id)
            rows.append(
                {
                    "emp_id": emp_id,
                    "name": data["name"],
                    "email": data.get("email") or "",
                    "role": data.get("role") or "",
                    "department": data.get("department") or "",
                    "direct_reports": len(reports),
                }
            )
        return rows

    def format_directory(self, managers_only: bool = False) -> str:
        rows = self.list_managers() if managers_only else self.list_employees()
        if not rows:
            return "No employees found."
        lines = []
        for row in rows:
            if managers_only:
                lines.append(
                    f"- {row['emp_id']}: {row['name']} "
                    f"({row.get('role') or 'Manager'}, {row.get('department') or 'N/A'}) "
                    f"| reports={row['direct_reports']}"
                )
            else:
                mgr = row["manager_id"] or "none"
                lines.append(
                    f"- {row['emp_id']}: {row['name']} "
                    f"({row.get('role') or 'Employee'}, {row.get('department') or 'N/A'}) "
                    f"| manager={mgr}"
                )
        return "\n".join(lines)

    def get_manager(self, emp_id: str) -> str:
        """
        Return manager's ID and name, or a message if none.
        """
        if emp_id not in self.employees:
            raise ValueError(f"Employee ID '{emp_id}' not found.")
        mgr_id = self.manager_map.get(emp_id)
        if not mgr_id:
            return "No manager assigned."
        mgr = self.employees[mgr_id]
        return f"{mgr_id}: {mgr['name']}"

    def search_employee_by_name(self, name_query: str, n: int = 5, cutoff: float = 0.5) -> List[str]:
        names = [e["name"] for e in self.employees.values()]
        query = name_query.strip().lower()
        # Prefer substring matches (e.g. "Tony" -> "Tony Sharma")
        substring_ids = [
            eid for eid, data in self.employees.items() if query in data["name"].lower()
        ]
        if substring_ids:
            return substring_ids[:n]
        matches = get_close_matches(name_query, names, n=n, cutoff=cutoff)
        return [eid for eid, data in self.employees.items() if data["name"] in matches]

    def get_employee_details(self, emp_id: str) -> Dict[str, str]:
        if emp_id not in self.employees:
            raise ValueError(f"Employee ID '{emp_id}' not found.")
        return self.employees[emp_id]

    def get_direct_reports(self, manager_id: str) -> List[str]:
        if manager_id not in self.employees:
            raise ValueError(f"Manager ID '{manager_id}' not found.")
        return [eid for eid, mgr in self.manager_map.items() if mgr == manager_id]


if __name__ == "__main__":
    em = EmployeeManager()
    em.add_employee(EmployeeCreate(emp_id="E001", name="John Doe", manager_id=None))
    em.add_employee(EmployeeCreate(emp_id="E002", name="Mama Doe", manager_id="E001"))
    print(em.format_directory())
    print(em.get_next_emp_id())