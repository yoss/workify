from django.urls import path
from . import views

app_name = 'employees'
urlpatterns = [
    path('', views.EmployeeList.as_view(), name='employee-list', kwargs={'all': False}),
    path('all/', views.EmployeeList.as_view(), name='employee-list-all', kwargs={'all': True}),
    path('new/', views.EmployeeCreate.as_view(), name='employee-create'),
    path('<slug:slug>/', views.EmployeeDetail.as_view(), name='employee-detail'),
    path('<slug:slug>/edit', views.EmployeeUpdate.as_view(), name='employee-update'),
    path('<slug:slug>/deactivate', views.EmployeeDeactivate.as_view(), name='employee-deactivate'),
    path('<slug:slug>/activate', views.EmployeeActivate.as_view(), name='employee-activate'),
]
