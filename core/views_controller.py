"""
Views dell'area Controllore: login, verifica biglietto, multe,
segnalazioni.

Come per l'area Viaggiatore, teniamo il controllore loggato con una
chiave separata nella sessione (session['controller_id']), cosi'
Viaggiatore e Controllore possono restare due sessioni indipendenti.
"""

from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404

from .models import Controller, TicketInspection, InspectionResult


def _current_controller(request):
    controller_id = request.session.get('controller_id')
    if not controller_id:
        return None
    return Controller.objects.filter(idController=controller_id).first()


def controller_login_view(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        if Controller.login(email, password):
            controller = Controller.objects.get(email=email)
            request.session['controller_id'] = controller.idController
            messages.success(request, f'Benvenuto, {controller.firstName}!')
            return redirect('core:controller_home')
        messages.error(request, 'Credenziali non valide.')
    return render(request, 'core/controller/login.html')


def controller_logout_view(request):
    request.session.pop('controller_id', None)
    return redirect('core:controller_login')


def controller_home_view(request):
    controller = _current_controller(request)
    if not controller:
        return redirect('core:controller_login')
    return render(request, 'core/controller/home.html', {'controller': controller})


def verify_ticket_view(request):
    """Il controllore inserisce il codice QR e noi chiamiamo
    verifyTicket(), che si occupa di cercare
    il biglietto e deciderne l'esito (valido / non valido / scaduto)."""
    controller = _current_controller(request)
    if not controller:
        return redirect('core:controller_login')

    inspection = None
    if request.method == 'POST':
        qr_code = request.POST.get('qrCodeData', '').strip()
        inspection = controller.verifyTicket(qr_code)

    return render(request, 'core/controller/verify_ticket.html', {
        'controller': controller, 'inspection': inspection,
        'InspectionResult': InspectionResult,
    })


def issue_fine_view(request, inspection_id):
    controller = _current_controller(request)
    if not controller:
        return redirect('core:controller_login')

    inspection = get_object_or_404(TicketInspection, idInspection=inspection_id,
                                    controller=controller)

    if request.method == 'POST':
        fine = inspection.issueFine(
            amount=request.POST['amount'],
            reason=request.POST['reason'],
            location=request.POST.get('location', ''),
        )
        messages.success(request, f'Multa emessa: {fine.amount} EUR - {fine.reason}')
        return redirect('core:view_fines')

    return render(request, 'core/controller/issue_fine.html', {
        'controller': controller, 'inspection': inspection
    })


def view_fines_view(request):
    controller = _current_controller(request)
    if not controller:
        return redirect('core:controller_login')

    fines = controller.viewFines()
    return render(request, 'core/controller/view_fines.html', {
        'controller': controller, 'fines': fines
    })


def controller_send_report_view(request):
    controller = _current_controller(request)
    if not controller:
        return redirect('core:controller_login')

    if request.method == 'POST':
        controller.sendReport(
            title=request.POST['title'],
            message=request.POST['message'],
        )
        messages.success(request, "Segnalazione inviata all'amministratore.")
        return redirect('core:controller_home')

    return render(request, 'core/controller/send_report.html', {'controller': controller})
