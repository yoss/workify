def employee_detail_permission(self, employee):
    if not self.request.user.is_authenticated:
        return False
    if self.request.user.employee == employee:
        return True
    if self.request.user.has_perm('employees.view_all_employee_details'):
        return True
    return False