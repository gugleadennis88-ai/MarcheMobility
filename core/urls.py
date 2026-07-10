from django.urls import path
from . import views, views_controller, views_admin

app_name = 'core'

urlpatterns = [
    # Viaggiatore
    path('', views.login_view, name='root'),
    path('home/', views.home_view, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('routes/', views.search_route_view, name='search_route'),
    path('routes/<int:route_id>/purchase/', views.purchase_ticket_view, name='purchase_ticket'),
    path('tickets/', views.ticket_history_view, name='ticket_history'),
    path('tickets/valid/', views.valid_tickets_view, name='valid_tickets'),
    path('tickets/<int:ticket_id>/qr/', views.ticket_qr_image_view, name='ticket_qr'),
    path('report/', views.send_report_view, name='send_report'),

    # Controllore
    path('controllore/login/', views_controller.controller_login_view, name='controller_login'),
    path('controllore/logout/', views_controller.controller_logout_view, name='controller_logout'),
    path('controllore/', views_controller.controller_home_view, name='controller_home'),
    path('controllore/verifica/', views_controller.verify_ticket_view, name='verify_ticket'),
    path('controllore/multe/', views_controller.view_fines_view, name='view_fines'),
    path('controllore/multe/emetti/<int:inspection_id>/',
         views_controller.issue_fine_view, name='issue_fine'),
    path('controllore/segnala/', views_controller.controller_send_report_view,
         name='controller_send_report'),

    # Amministratore
    path('admin-panel/login/', views_admin.admin_login_view, name='admin_login'),
    path('admin-panel/logout/', views_admin.admin_logout_view, name='admin_logout'),
    path('admin-panel/', views_admin.admin_home_view, name='admin_home'),
    path('admin-panel/controllori/nuovo/', views_admin.create_controller_view,
         name='create_controller'),
    path('admin-panel/utenti/', views_admin.manage_users_view, name='manage_users'),
    path('admin-panel/controllori/', views_admin.manage_controllers_view,
         name='manage_controllers'),
    path('admin-panel/corse/', views_admin.manage_routes_view, name='manage_routes'),
    path('admin-panel/segnalazioni/', views_admin.manage_reports_view, name='manage_reports'),
    path('admin-panel/notifiche/', views_admin.send_notification_view, name='send_notification'),
]
