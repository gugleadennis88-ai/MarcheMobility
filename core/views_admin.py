"""
Views dell'area Amministratore: gestione utenti, controllori, corse,
segnalazioni e notifiche globali.

Anche qui usiamo una chiave di sessione dedicata (session['admin_id']).
La maggior parte di queste view sono semplici "wrapper" attorno ai
metodi che abbiamo gia' scritto sulla classe Admin in models.py: la
view legge il form, il modello fa il lavoro vero.
"""

from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404

from .models import (
    Admin, User, Controller, Route,
    UserReport, ControllerReport, NotificationType,
)


def _current_admin(request):
    admin_id = request.session.get('admin_id')
    if not admin_id:
        return None
    return Admin.objects.filter(idAdmin=admin_id).first()


def admin_login_view(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        if Admin.login(email, password):
            admin = Admin.objects.get(email=email)
            request.session['admin_id'] = admin.idAdmin
            messages.success(request, f'Benvenuto, {admin.firstName}!')
            return redirect('core:admin_home')
        messages.error(request, 'Credenziali non valide.')
    return render(request, 'core/admin/login.html')


def admin_logout_view(request):
    request.session.pop('admin_id', None)
    return redirect('core:admin_login')


def admin_home_view(request):
    admin = _current_admin(request)
    if not admin:
        return redirect('core:admin_login')
    return render(request, 'core/admin/home.html', {'admin': admin})


def create_controller_view(request):
    admin = _current_admin(request)
    if not admin:
        return redirect('core:admin_login')

    if request.method == 'POST':
        try:
            admin.createControllerAccount(
                firstName=request.POST['firstName'],
                lastName=request.POST['lastName'],
                email=request.POST['email'],
                phoneNumber=request.POST['phoneNumber'],
                codiceFiscale=request.POST['codiceFiscale'],
                password=request.POST['password'],
            )
            messages.success(request, 'Account controllore creato.')
            return redirect('core:manage_controllers')
        except Exception as exc:
            messages.error(request, f'Errore: {exc}')

    return render(request, 'core/admin/create_controller.html', {'admin': admin})


def manage_users_view(request):
    """Qui l'admin puo' sospendere, riattivare o eliminare un utente:
    le tre azioni richiamano semplicemente i metodi corrispondenti
    gia definiti nella classe Admin."""
    admin = _current_admin(request)
    if not admin:
        return redirect('core:admin_login')

    if request.method == 'POST':
        user = get_object_or_404(User, idUser=request.POST['user_id'])
        action = request.POST['action']
        if action == 'suspend':
            admin.suspendUser(user)
        elif action == 'reactivate':
            admin.reactivateUser(user)
        elif action == 'delete':
            admin.deleteUser(user)
        messages.success(request, f'Utente {user.email}: azione "{action}" applicata.')
        return redirect('core:manage_users')

    users = User.objects.all().order_by('-dateJoined')
    return render(request, 'core/admin/manage_users.html', {'admin': admin, 'users': users})


def manage_controllers_view(request):
    admin = _current_admin(request)
    if not admin:
        return redirect('core:admin_login')

    if request.method == 'POST':
        controller = get_object_or_404(Controller, idController=request.POST['controller_id'])
        action = request.POST['action']
        if action == 'suspend':
            admin.suspendController(controller)
        elif action == 'reactivate':
            admin.reactivateController(controller)
        elif action == 'delete':
            admin.deleteController(controller)
        messages.success(request, f'Controllore {controller.email}: azione "{action}" applicata.')
        return redirect('core:manage_controllers')

    controllers = Controller.objects.all().order_by('-dateJoined')
    return render(request, 'core/admin/manage_controllers.html', {
        'admin': admin, 'controllers': controllers
    })


def manage_routes_view(request):
    admin = _current_admin(request)
    if not admin:
        return redirect('core:admin_login')

    if request.method == 'POST':
        if request.POST.get('action') == 'delete':
            route = get_object_or_404(Route, idRoute=request.POST['route_id'])
            admin.removeRoute(route)
            messages.success(request, 'Corsa eliminata.')
        else:
            admin.addRoute(
                origin=request.POST['origin'],
                destination=request.POST['destination'],
                duration=request.POST['duration'],
                departureTime=request.POST['departureTime'],
                arrivalTime=request.POST['arrivalTime'],
                daysOfWeek=request.POST['daysOfWeek'],
                price=request.POST['price'],
            )
            messages.success(request, 'Corsa aggiunta.')
        return redirect('core:manage_routes')

    routes = Route.objects.all().order_by('departureTime')
    return render(request, 'core/admin/manage_routes.html', {'admin': admin, 'routes': routes})


def manage_reports_view(request):
    """Le segnalazioni di utenti e controllori sono due modelli
    diversi (UserReport / ControllerReport), quindi qui le teniamo
    separate ma le gestiamo con la stessa logica"""
    admin = _current_admin(request)
    if not admin:
        return redirect('core:admin_login')

    if request.method == 'POST':
        report_type = request.POST['report_type']
        response_text = request.POST['response']
        if report_type == 'user':
            report = get_object_or_404(UserReport, idReport=request.POST['report_id'])
            admin.respondToUserReport(report, response_text)
        else:
            report = get_object_or_404(ControllerReport, idReportController=request.POST['report_id'])
            admin.respondToControllerReport(report, response_text)
        messages.success(request, 'Risposta inviata, segnalazione chiusa.')
        return redirect('core:manage_reports')

    user_reports = UserReport.objects.all().order_by('-date')
    controller_reports = ControllerReport.objects.all().order_by('-date')
    return render(request, 'core/admin/manage_reports.html', {
        'admin': admin, 'user_reports': user_reports, 'controller_reports': controller_reports
    })


def send_notification_view(request):
    admin = _current_admin(request)
    if not admin:
        return redirect('core:admin_login')

    if request.method == 'POST':
        notification = admin.sendGlobalNotification(
            title=request.POST['title'],
            message=request.POST['message'],
            type=request.POST['type'],
        )
        # nella demo mandiamo la notifica subito a tutti; in un
        # sistema reale potrebbe essere schedulata per una data futura
        notification.deliver(users=User.objects.all(), controllers=Controller.objects.all())
        messages.success(request, 'Notifica inviata a tutti gli utenti e controllori.')
        return redirect('core:admin_home')

    return render(request, 'core/admin/send_notification.html', {
        'admin': admin, 'NotificationType': NotificationType
    })
