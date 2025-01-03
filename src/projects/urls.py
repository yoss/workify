from django.urls import path
from . import views

app_name = 'projects'
urlpatterns = [
    path('', views.ProjectList.as_view(), name='project-list', kwargs={'all': False}),
    path('all/', views.ProjectList.as_view(), name='project-list-all', kwargs={'all': True}),
    path('new/', views.ProjectCreate.as_view(), name='project-create'),
    path('<slug:slug>/', views.ProjectDetail.as_view(), name='project-detail'),
    path('<slug:slug>/edit', views.ProjectUpdate.as_view(), name='project-update'),
    path('<slug:slug>/deactivate', views.ProjectDeactivate.as_view(), name='project-deactivate'),
    path('<slug:slug>/activate', views.ProjectActivate.as_view(), name='project-activate'),
    path('<slug:slug>/budget', views.ProjectBudgetList.as_view(), name='project-budget-list'),
    path('<slug:slug>/budget/new', views.ProjectBudgetCreate.as_view(), name='project-budget-create'),
    path('<slug:slug>/budget/<int:pk>/edit', views.ProjectBudgetUpdate.as_view(), name='project-budget-update'),
    path('<slug:slug>/budget/<int:pk>/delete', views.ProjectBudgetDelete.as_view(), name='project-budget-delete'),
]