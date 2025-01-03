from django.urls import path
from . import views

app_name = 'budgets'
urlpatterns = [
    path('', views.BudgetList.as_view(), name='budget-list', kwargs={'all': False}),
    path('all/', views.BudgetList.as_view(), name='budget-list-all', kwargs={'all': True}),
    path('new/', views.BudegetCreate.as_view(), name='budget-create'),
    path('autocomplete/', views.BudgetAutocomplete.as_view(), name='budget-autocomplete'),
    # path('api/', views.BudgetList.as_view(), name='employee-autocomplete'),
    path('<int:pk>/', views.BudgetList.as_view(), name='budget-detail'),
    path('<int:pk>/edit', views.BudgetList.as_view(), name='budget-update'),
    path('<int:pk>/deactivate', views.BudgetList.as_view(), name='budget-deactivate'),
    path('<int:pk>/activate', views.BudgetList.as_view(), name='budget-activate'),
]