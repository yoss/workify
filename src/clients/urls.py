from django.urls import path
from . import views

app_name = 'clients'
urlpatterns = [
    path('', views.ClientList.as_view(), name='client-list', kwargs={'all': False}),
    path('all/', views.ClientList.as_view(), name='client-list-all', kwargs={'all': True}),
    path('new/', views.ClientCreate.as_view(), name='client-create'),
    path('<slug:slug>/', views.ClientDetail.as_view(), name='client-detail'),
    path('<slug:slug>/edit', views.ClientUpdate.as_view(), name='client-update'),
    path('<slug:slug>/deactivate', views.ClientDeactivate.as_view(), name='client-deactivate'),
    path('<slug:slug>/activate', views.ClientActivate.as_view(), name='client-activate'),

]