"""
Views dell'area Viaggiatore: registrazione, login, ricerca corse,
acquisto biglietto, storico.

Usiamo la sessione di Django (request.session) per tenere traccia
dell'utente loggato, salvando solo il suo id (session['user_id']).
Non usiamo il sistema di login integrato di Django perche' User,
Admin e Controller sono tre classi separate nel nostro modello, non
tre "ruoli" della stessa classe.
"""

import io

import qrcode
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404

from .models import User, Route, Ticket, TicketPaymentMethod, GlobalNotification


def _current_user(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return None
    return User.objects.filter(idUser=user_id).first()


def home_view(request):
    """La homepage dopo il login: qui mostriamo le scorciatoie
    principali e le ultime notifiche ricevute dall'utente."""
    user = _current_user(request)
    if not user:
        return redirect('core:login')

    notifiche = GlobalNotification.objects.filter(
        userRecipients=user
    ).order_by('-dateSent')[:5]

    return render(request, 'core/home.html', {'user': user, 'notifiche': notifiche})


def register_view(request):
    if request.method == 'POST':
        try:
            user = User.register(
                firstName=request.POST['firstName'],
                lastName=request.POST['lastName'],
                email=request.POST['email'],
                phoneNumber=request.POST['phoneNumber'],
                password=request.POST['password'],
                codiceFiscale=request.POST['codiceFiscale'],
            )
            # nella demo verifichiamo subito l'account, invece di
            # aspettare che l'utente clicchi il link ricevuto via email
            user.verifyAccount(user.token)
            messages.success(request, 'Registrazione completata. Ora puoi accedere.')
            return redirect('core:login')
        except Exception as exc:
            messages.error(request, f'Errore nella registrazione: {exc}')
    return render(request, 'core/register.html')


def login_view(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        if User.login(email, password):
            user = User.objects.get(email=email)
            request.session['user_id'] = user.idUser
            messages.success(request, f'Benvenuto, {user.firstName}!')
            return redirect('core:home')
        messages.error(request, 'Credenziali non valide.')
    return render(request, 'core/login.html')


def logout_view(request):
    request.session.flush()
    return redirect('core:login')


def search_route_view(request):
    user = _current_user(request)
    if not user:
        return redirect('core:login')

    results = []
    if request.method == 'POST':
        origin = request.POST.get('origin', '')
        destination = request.POST.get('destination', '')
        # qui usiamo icontains per non essere troppo rigidi su
        # maiuscole/minuscole quando l'utente scrive la citta'
        all_routes = Route.objects.filter(origin__icontains=origin,
                                           destination__icontains=destination)
        results = list(all_routes)

    return render(request, 'core/search_route.html', {'user': user, 'results': results})


def purchase_ticket_view(request, route_id):
    user = _current_user(request)
    if not user:
        return redirect('core:login')

    route = get_object_or_404(Route, idRoute=route_id)

    if request.method == 'POST':
        quantity = int(request.POST.get('quantitySeats', 1))
        payment_method = request.POST.get('paymentMethod', TicketPaymentMethod.PAYPAL)
        ticket = user.purchaseTicket(route=route, quantitySeats=quantity,
                                      paymentMethod=payment_method)
        messages.success(
            request,
            f'Biglietto acquistato! Codice QR: {ticket.qrCodeData} '
            f'- Totale: {ticket.getTotalPrice()} EUR'
        )
        return redirect('core:ticket_history')

    return render(request, 'core/purchase_ticket.html', {'user': user, 'route': route})


def ticket_qr_image_view(request, ticket_id):
    """Generiamo l'immagine vera del QR al volo, invece di salvarla
    come file: partiamo dalla stringa qrCodeData e usiamo la libreria
    qrcode per disegnarla come PNG."""
    user = _current_user(request)
    if not user:
        return redirect('core:login')

    ticket = get_object_or_404(Ticket, idTicket=ticket_id, user=user)

    img = qrcode.make(ticket.qrCodeData)
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return HttpResponse(buffer.getvalue(), content_type='image/png')


def valid_tickets_view(request):
    user = _current_user(request)
    if not user:
        return redirect('core:login')

    tickets = user.viewValidTickets()
    return render(request, 'core/ticket_history.html', {
        'user': user, 'tickets': tickets, 'titolo': 'I miei biglietti'
    })


def ticket_history_view(request):
    user = _current_user(request)
    if not user:
        return redirect('core:login')

    tickets = user.viewTicketHistory()
    return render(request, 'core/ticket_history.html', {
        'user': user, 'tickets': tickets, 'titolo': 'Storico biglietti'
    })


def send_report_view(request):
    user = _current_user(request)
    if not user:
        return redirect('core:login')

    if request.method == 'POST':
        user.sendReport(
            title=request.POST['title'],
            message=request.POST['message'],
        )
        messages.success(request, "Segnalazione inviata. Riceverai una risposta dall'amministratore.")
        return redirect('core:home')

    return render(request, 'core/send_report.html', {'user': user})
