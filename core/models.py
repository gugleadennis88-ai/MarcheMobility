"""
I Modelli di MarcheMobility.

Qui traduciamo in codice i diagrammi delle classi della nostra tesina
(Capitolo 5.1): ogni classe UML diventa una classe Django, ogni
attributo un campo, ogni metodo una funzione. Usiamo camelCase per
nomi di attributi e metodi (come nella tesina).
"""

import uuid
from datetime import timedelta

from django.contrib.auth.hashers import make_password, check_password
from django.db import models
from django.utils import timezone


# Gli enum del diagramma li implementiamo con TextChoices di Django.

class UserStatus(models.TextChoices):
    NOT_VERIFIED = 'NOT_VERIFIED', 'Non verificato'
    ACTIVE = 'ACTIVE', 'Attivo'
    SUSPENDED = 'SUSPENDED', 'Sospeso'
    DELETED = 'DELETED', 'Eliminato'


class UserReportStatus(models.TextChoices):
    OPEN = 'OPEN', 'Aperto'
    IN_REVIEW = 'IN_REVIEW', 'In lavorazione'
    CLOSED = 'CLOSED', 'Chiuso'


class ControllerReportStatus(models.TextChoices):
    OPEN = 'OPEN', 'Aperto'
    IN_REVIEW = 'IN_REVIEW', 'In lavorazione'
    CLOSED = 'CLOSED', 'Chiuso'


class InspectionResult(models.TextChoices):
    VALID = 'VALID', 'Valido'
    INVALID = 'INVALID', 'Non valido'
    EXPIRED = 'EXPIRED', 'Scaduto'


class TicketStatus(models.TextChoices):
    VALID = 'VALID', 'Valido'
    USED = 'USED', 'Utilizzato'
    EXPIRED = 'EXPIRED', 'Scaduto'


class TicketPaymentMethod(models.TextChoices):
    NEXI = 'NEXI', 'Nexi'
    PAYPAL = 'PAYPAL', 'PayPal'


class NotificationType(models.TextChoices):
    SERVICE_UPDATE = 'SERVICE_UPDATE', 'Aggiornamento servizio'
    MAINTENANCE = 'MAINTENANCE', 'Manutenzione'
    MARKETING = 'MARKETING', 'Marketing'
    GENERAL = 'GENERAL', 'Generale'


class NotificationStatus(models.TextChoices):
    SCHEDULED = 'SCHEDULED', 'Programmata'
    SENT = 'SENT', 'Inviata'
    CANCELED = 'CANCELED', 'Annullata'


# --- Viaggiatore -----------------------------------------------------------
# Questa e' la classe principale lato utente: qui mettiamo sia i dati
# anagrafici sia i metodi legati a registrazione, login e acquisto
# biglietti, esattamente come li avevamo assegnati a User nel
# diagramma delle classi.

class User(models.Model):
    idUser = models.BigAutoField(primary_key=True)
    firstName = models.CharField(max_length=100)
    lastName = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phoneNumber = models.CharField(max_length=20)
    codiceFiscale = models.CharField(max_length=16)
    password = models.CharField(max_length=255)  # salviamo sempre l'hash, mai la password in chiaro
    status = models.CharField(
        max_length=20, choices=UserStatus.choices, default=UserStatus.NOT_VERIFIED
    )
    dateJoined = models.DateTimeField(auto_now_add=True)
    lastLogin = models.DateTimeField(null=True, blank=True)

    # Usiamo un solo campo token sia per la verifica dell'account sia
    # per il reset password: e' una semplificazione che abbiamo deciso
    # in fase di progettazione, per evitare due campi quasi identici.
    token = models.CharField(max_length=64, null=True, blank=True)
    tokenExpiry = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'users'

    def __str__(self):
        return self.email

    @classmethod
    def register(cls, firstName, lastName, email, phoneNumber, password, codiceFiscale):
        """Creiamo il nuovo utente in stato NOT_VERIFIED e generiamo
        subito il token che servira' per confermare l'email."""
        user = cls.objects.create(
            firstName=firstName, lastName=lastName, email=email,
            phoneNumber=phoneNumber, codiceFiscale=codiceFiscale,
            password=make_password(password), status=UserStatus.NOT_VERIFIED,
        )
        user._generate_token(hours_valid=24)
        return user

    @classmethod
    def login(cls, email, password):
        """Cerchiamo l'utente per email e controlliamo la password
        con check_password, che confronta in modo sicuro senza mai
        decifrare l'hash salvato."""
        try:
            user = cls.objects.get(email=email)
        except cls.DoesNotExist:
            return False
        if not check_password(password, user.password):
            return False
        user.lastLogin = timezone.now()
        user.save(update_fields=['lastLogin'])
        return True

    def logout(self):
        pass  # la sessione viene chiusa lato Django, qui non serve altro

    @classmethod
    def requestPasswordReset(cls, email):
        try:
            user = cls.objects.get(email=email)
        except cls.DoesNotExist:
            return  # non diciamo se l'email esiste o no, per sicurezza
        user._generate_token(hours_valid=1)

    def resetPassword(self, token, newPassword):
        if not self._is_token_valid(token):
            return False
        self.password = make_password(newPassword)
        self.token = None
        self.tokenExpiry = None
        self.save(update_fields=['password', 'token', 'tokenExpiry'])
        return True

    def verifyAccount(self, token):
        if not self._is_token_valid(token):
            return False
        self.status = UserStatus.ACTIVE
        self.token = None
        self.tokenExpiry = None
        self.save(update_fields=['status', 'token', 'tokenExpiry'])
        return True

    def updateProfile(self, firstName=None, lastName=None, email=None,
                       phoneNumber=None, password=None):
        if firstName is not None:
            self.firstName = firstName
        if lastName is not None:
            self.lastName = lastName
        if email is not None:
            self.email = email
        if phoneNumber is not None:
            self.phoneNumber = phoneNumber
        if password is not None:
            self.password = make_password(password)
        self.save()

    def sendReport(self, title, message):
        return UserReport.objects.create(user=self, title=title, message=message)

    def searchRoute(self, origin, destination, date):
        candidates = Route.objects.filter(origin=origin, destination=destination)
        return [r for r in candidates if r.isAvailable(date)]

    def purchaseTicket(self, route, quantitySeats, paymentMethod):
        ticket = Ticket.objects.create(
            route=route, user=self, quantitySeats=quantitySeats,
            paymentMethod=paymentMethod, purchaseDate=timezone.now(),
            expirationDate=route.departureTime, status=TicketStatus.VALID,
        )
        ticket.generateQRCode()
        return ticket

    def viewTicketHistory(self):
        return list(self.tickets.all())

    def viewValidTickets(self):
        return list(self.tickets.filter(status=TicketStatus.VALID))

    def _generate_token(self, hours_valid):
        self.token = uuid.uuid4().hex
        self.tokenExpiry = timezone.now() + timedelta(hours=hours_valid)
        self.save(update_fields=['token', 'tokenExpiry'])

    def _is_token_valid(self, token):
        return bool(self.token) and self.token == token and \
            self.tokenExpiry is not None and self.tokenExpiry > timezone.now()


class UserReport(models.Model):
    idReport = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=200)
    message = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20, choices=UserReportStatus.choices, default=UserReportStatus.OPEN
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='userReports')

    class Meta:
        db_table = 'user_reports'

    def __str__(self):
        return f'{self.title} ({self.user.email})'


# --- Controllore -----------------------------------------------------------
# Notiamo che qui NON c'e un metodo per registrasi: l'account del
# controllore lo crea solo l'Admin (vedi Admin.createControllerAccount
# piu' sotto), il controllore non puo auto-registrarsi.

class Controller(models.Model):
    idController = models.BigAutoField(primary_key=True)
    firstName = models.CharField(max_length=100)
    lastName = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    codiceFiscale = models.CharField(max_length=16)
    phoneNumber = models.CharField(max_length=20)
    isActive = models.BooleanField(default=True)
    dateJoined = models.DateTimeField(auto_now_add=True)
    lastLogin = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'controllers'

    def __str__(self):
        return self.email

    @classmethod
    def login(cls, email, password):
        try:
            controller = cls.objects.get(email=email)
        except cls.DoesNotExist:
            return False
        if not check_password(password, controller.password):
            return False
        controller.lastLogin = timezone.now()
        controller.save(update_fields=['lastLogin'])
        return True

    def logout(self):
        pass

    def verifyTicket(self, qrCodeData):
        """Qui gestiamo la scansione del biglietto: cerchiamo il
        Ticket dal QR, decidiamo l'esito, e se era valido lo
        segniamo come usato cosi' non puo' essere riscansionato."""
        ticket = Ticket.findTicket(qrCodeData)

        if ticket is None:
            result = InspectionResult.INVALID
        elif ticket.isExpired():
            result = InspectionResult.EXPIRED
        elif ticket.isValid():
            result = InspectionResult.VALID
            ticket.markAsUsed()
        else:
            result = InspectionResult.INVALID

        return TicketInspection.objects.create(
            controller=self, ticket=ticket, result=result,
            date=timezone.now(), location='',
        )

    def sendReport(self, title, message):
        return ControllerReport.objects.create(controller=self, title=title, message=message)

    def viewFines(self):
        return list(Fine.objects.filter(inspection__controller=self))


class ControllerReport(models.Model):
    idReportController = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=200)
    message = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20, choices=ControllerReportStatus.choices,
        default=ControllerReportStatus.OPEN
    )
    controller = models.ForeignKey(
        Controller, on_delete=models.CASCADE, related_name='controllerReports'
    )

    class Meta:
        db_table = 'controller_reports'

    def __str__(self):
        return f'{self.title} ({self.controller.email})'


#Corse

class Route(models.Model):
    idRoute = models.BigAutoField(primary_key=True)
    origin = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    duration = models.IntegerField(help_text='Durata in minuti')
    departureTime = models.DateTimeField()
    arrivalTime = models.DateTimeField()
    daysOfWeek = models.CharField(max_length=100)  # es. "Lunedi,Mercoledi"
    price = models.DecimalField(max_digits=6, decimal_places=2)

    class Meta:
        db_table = 'routes'

    def __str__(self):
        return f'{self.origin}-{self.destination}'

    def isAvailable(self, date):
        day_name = date.strftime('%A')
        return day_name in self.daysOfWeek and self.departureTime >= date


#Biglietto

class Ticket(models.Model):
    idTicket = models.BigAutoField(primary_key=True)
    purchaseDate = models.DateTimeField()
    expirationDate = models.DateTimeField()
    status = models.CharField(
        max_length=20, choices=TicketStatus.choices, default=TicketStatus.VALID
    )
    quantitySeats = models.IntegerField()
    qrCodeData = models.CharField(max_length=100, unique=True, null=True, blank=True)
    paymentMethod = models.CharField(max_length=20, choices=TicketPaymentMethod.choices)
    route = models.ForeignKey(Route, on_delete=models.PROTECT, related_name='tickets')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tickets')

    class Meta:
        db_table = 'tickets'

    def isValid(self):
        return self.status == TicketStatus.VALID and not self.isExpired()

    def isExpired(self):
        return timezone.now() > self.expirationDate

    def generateQRCode(self):
        """Generiamo un codice univoco per il QR: nella demo usiamo un
        codice esadecimale casuale, mentre la libreria qrcode si occupa
        di trasformarlo davvero in immagine quando serve mostrarlo."""
        self.qrCodeData = uuid.uuid4().hex[:12].upper()
        self.save(update_fields=['qrCodeData'])
        return self.qrCodeData

    def getTotalPrice(self):
        return self.route.price * self.quantitySeats

    def markAsUsed(self):
        self.status = TicketStatus.USED
        self.save(update_fields=['status'])

    @classmethod
    def findTicket(cls, qrCodeData):
        return cls.objects.filter(qrCodeData=qrCodeData).first()


class TicketInspection(models.Model):
    idInspection = models.BigAutoField(primary_key=True)
    date = models.DateTimeField(auto_now_add=True)
    location = models.CharField(max_length=200, blank=True)
    result = models.CharField(max_length=20, choices=InspectionResult.choices)
    # e' 0..1 perche' il biglietto potrebbe essere assente (nessun QR da leggere)
    ticket = models.ForeignKey(
        Ticket, on_delete=models.SET_NULL, null=True, blank=True, related_name='inspections'
    )
    controller = models.ForeignKey(
        Controller, on_delete=models.CASCADE, related_name='inspections'
    )

    class Meta:
        db_table = 'ticket_inspections'

    def issueFine(self, amount, reason, location):
        return Fine.objects.create(
            inspection=self, amount=amount, reason=reason, date=timezone.now()
        )


class Fine(models.Model):
    idFine = models.BigAutoField(primary_key=True)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    date = models.DateTimeField()
    reason = models.CharField(max_length=255)
    inspection = models.OneToOneField(
        TicketInspection, on_delete=models.CASCADE, related_name='fine'
    )

    class Meta:
        db_table = 'fines'

    def __str__(self):
        return f'Multa #{self.idFine} - {self.amount} EUR'


#Amministratore

class Admin(models.Model):
    idAdmin = models.BigAutoField(primary_key=True)
    firstName = models.CharField(max_length=100)
    lastName = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    dateJoined = models.DateTimeField(auto_now_add=True)
    lastLogin = models.DateTimeField(null=True, blank=True)

    token = models.CharField(max_length=64, null=True, blank=True)
    tokenExpiry = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'admins'

    def __str__(self):
        return self.email

    @classmethod
    def login(cls, email, password):
        try:
            admin = cls.objects.get(email=email)
        except cls.DoesNotExist:
            return False
        if not check_password(password, admin.password):
            return False
        admin.lastLogin = timezone.now()
        admin.save(update_fields=['lastLogin'])
        return True

    def logout(self):
        pass

    @classmethod
    def requestPasswordReset(cls, email):
        try:
            admin = cls.objects.get(email=email)
        except cls.DoesNotExist:
            return
        admin.token = uuid.uuid4().hex
        admin.tokenExpiry = timezone.now() + timedelta(hours=1)
        admin.save(update_fields=['token', 'tokenExpiry'])

    def resetPassword(self, token, newPassword):
        if not (self.token == token and self.tokenExpiry and self.tokenExpiry > timezone.now()):
            return False
        self.password = make_password(newPassword)
        self.token = None
        self.tokenExpiry = None
        self.save(update_fields=['password', 'token', 'tokenExpiry'])
        return True

    def addRoute(self, origin, destination, duration, departureTime, arrivalTime,
                 daysOfWeek, price):
        return Route.objects.create(
            origin=origin, destination=destination, duration=duration,
            departureTime=departureTime, arrivalTime=arrivalTime,
            daysOfWeek=daysOfWeek, price=price,
        )

    def modifyRoute(self, route, **fields):
        for key, value in fields.items():
            setattr(route, key, value)
        route.save()
        return route

    def removeRoute(self, route):
        route.delete()

    def createControllerAccount(self, firstName, lastName, email, phoneNumber,
                                 codiceFiscale, password):
        return Controller.objects.create(
            firstName=firstName, lastName=lastName, email=email,
            phoneNumber=phoneNumber, codiceFiscale=codiceFiscale,
            password=make_password(password),
        )

    def modifyUser(self, user, firstName, lastName, email, phoneNumber, codiceFiscale):
        user.firstName = firstName
        user.lastName = lastName
        user.email = email
        user.phoneNumber = phoneNumber
        user.codiceFiscale = codiceFiscale
        user.save()
        return user

    def suspendUser(self, user):
        user.status = UserStatus.SUSPENDED
        user.save(update_fields=['status'])

    def reactivateUser(self, user):
        user.status = UserStatus.ACTIVE
        user.save(update_fields=['status'])

    def deleteUser(self, user):
        user.status = UserStatus.DELETED
        user.save(update_fields=['status'])

    def modifyController(self, controller, firstName, lastName, email, phoneNumber,
                          codiceFiscale, password):
        """Il parametro password e' facoltativo: quando l'admin lo
        valorizza, sta reimpostando la password del controllore (e'
        cosi' che gestiamo il recupero credenziali per i controllori,
        senza un link via email come per gli utenti)."""
        controller.firstName = firstName
        controller.lastName = lastName
        controller.email = email
        controller.phoneNumber = phoneNumber
        controller.codiceFiscale = codiceFiscale
        if password:
            controller.password = make_password(password)
        controller.save()
        return controller

    def suspendController(self, controller):
        controller.isActive = False
        controller.save(update_fields=['isActive'])

    def reactivateController(self, controller):
        controller.isActive = True
        controller.save(update_fields=['isActive'])

    def deleteController(self, controller):
        controller.delete()

    def respondToUserReport(self, report, response):
        report.status = UserReportStatus.CLOSED
        report.save(update_fields=['status'])
        return response

    def respondToControllerReport(self, report, response):
        report.status = ControllerReportStatus.CLOSED
        report.save(update_fields=['status'])
        return response

    def sendGlobalNotification(self, title, message, type):
        return GlobalNotification.objects.create(
            admin=self, title=title, message=message, type=type,
            status=NotificationStatus.SCHEDULED,
        )

    def cancelGlobalNotification(self, notification):
        notification.status = NotificationStatus.CANCELED
        notification.save(update_fields=['status'])


class GlobalNotification(models.Model):
    idNotification = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=200)
    message = models.TextField()
    dateSent = models.DateTimeField(null=True, blank=True)
    type = models.CharField(max_length=20, choices=NotificationType.choices)
    status = models.CharField(
        max_length=20, choices=NotificationStatus.choices,
        default=NotificationStatus.SCHEDULED
    )
    admin = models.ForeignKey(Admin, on_delete=models.CASCADE, related_name='notifications')

    userRecipients = models.ManyToManyField(User, related_name='notifications', blank=True)
    controllerRecipients = models.ManyToManyField(
        Controller, related_name='notifications', blank=True
    )

    class Meta:
        db_table = 'global_notifications'

    def __str__(self):
        return f'{self.title} [{self.status}]'

    def deliver(self, users, controllers):
        if self.status != NotificationStatus.SCHEDULED:
            return
        self.userRecipients.set(users)
        self.controllerRecipients.set(controllers)
        self.status = NotificationStatus.SENT
        self.dateSent = timezone.now()
        self.save(update_fields=['status', 'dateSent'])