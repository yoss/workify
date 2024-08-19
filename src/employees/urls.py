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
    path('<slug:slug>/documents/new', views.EmployeeDocumentCreate.as_view(), name='employee-document-create'),
    path('<slug:slug>/documents/<int:pk>/edit', views.EmployeeDocumentUpdate.as_view(), name='employee-document-update'),
    path('<slug:slug>/documents/<int:pk>/delete', views.EmployeeDocumentDelete.as_view(), name='employee-document-delete'),
    path('<slug:slug>/rate/new', views.EmployeeRateCreate.as_view(), name='employee-rate-create'),
    path('<slug:slug>/rate/<int:pk>/edit', views.EmployeeRateUpdate.as_view(), name='employee-rate-update'),
    path('<slug:slug>/rate/<int:pk>/delete', views.EmployeeRateDelete.as_view(), name='employee-rate-delete'),
]