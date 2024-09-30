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
    path('<slug:slug>/contract', views.ContractList.as_view(), name='contract-list', kwargs={'all': False}),
    path('<slug:slug>/contract/all/', views.ContractList.as_view(), name='contract-list-all', kwargs={'all': True}),
    path('<slug:slug>/contract/new/', views.ContractCreate.as_view(), name='contract-create'),
    path('<slug:client_slug>/contract/<slug:slug>/', views.ContractDetail.as_view(), name='contract-detail'),
    path('<slug:client_slug>/contract/<slug:slug>/edit', views.ContractUpdate.as_view(), name='contract-update'),
    path('<slug:client_slug>/contract/<slug:slug>/audit', views.ContractAudit.as_view(), name='contract-audit'),
    path('<slug:client_slug>/contract/<slug:slug>/deactivate', views.ContractDeactivate.as_view(), name='contract-deactivate'),
    path('<slug:client_slug>/contract/<slug:slug>/activate', views.ContractActivate.as_view(), name='contract-activate'),
    
    path('<slug:client_slug>/contract/<slug:slug>/item/', views.ContractItemList.as_view(), name='contract-item-list'),
    path('<slug:client_slug>/contract/<slug:slug>/item/new/', views.ContractItemCreate.as_view(), name='contract-item-create'),
    path('<slug:client_slug>/contract/<slug:slug>/item/<int:pk>/delete', views.ContractItemDelete.as_view(), name='contract-item-delete'),
    path('<slug:client_slug>/contract/<slug:slug>/item/<int:pk>/edit', views.ContractItemUpdate.as_view(), name='contract-item-update'),
    
    path('<slug:client_slug>/contract/<slug:slug>/invoice', views.SalesInvoiceList.as_view(), name='sales-invoice-list-contract'),
    path('<slug:client_slug>/contract/<slug:slug>/item/<int:pk>/invoices', views.SalesInvoiceList.as_view(), name='sales-invoice-list-contractitem'),
    path('<slug:client_slug>/contract/<slug:slug>/invoice/new', views.SalesInvoiceCreate.as_view(), name='sales-invoice-create'),
    path('invoice/<int:pk>', views.SalesInvoiceView.as_view(), name='sales-invoice-view'),
    path('invoice/<int:pk>/edit', views.SalesInvoiceUpdate.as_view(), name='sales-invoice-update'),
    path('invoice/<int:pk>/settle', views.SalesInvoiceSettle.as_view(), name='sales-invoice-settle'),
    path('invoice/<int:pk>/delete', views.SalesInvoiceDelete.as_view(), name='sales-invoice-delete'),
]