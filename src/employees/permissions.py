def employee_detail_permission(self):
    employee = self.get_object()
    if self.request.user.employee == employee:
        return True
    if self.request.user.has_perm('employees.view_all_employee_details'):
        return True
    return False