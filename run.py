import os
import sys
from datetime import datetime, timedelta

# Script di avvio: prepara il database e fa partire il server, cosi
# non dobbiamo lanciare manage.py con piu' comandi separati durante
# la presentazione.

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'marchemobility.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import django
django.setup()

from django.core.management import call_command
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User as AuthUser
from core.models import Route, User, UserStatus, Admin, Controller

call_command('makemigrations', 'core', verbosity=0)
call_command('migrate', verbosity=0)

# superuser per il pannello /admin/ di Django (comodo per ispezionare
# rapidamente i dati, in aggiunta alle pagine che abbiamo scritto noi)
if not AuthUser.objects.filter(username='admin').exists():
    AuthUser.objects.create_superuser('admin', 'admin@marchemobility.it', 'admin123')

# un po' di corse di prova, cosi la ricerca da subito qualche risultato
if not Route.objects.exists():
    now = datetime.now()
    Route.objects.create(
        origin='Ancona', destination='Pesaro', duration=60,
        departureTime=now + timedelta(days=1, hours=9),
        arrivalTime=now + timedelta(days=1, hours=10),
        daysOfWeek='Lunedi,Mercoledi,Venerdi', price=5.50,
    )
    Route.objects.create(
        origin='Ancona', destination='Macerata', duration=45,
        departureTime=now + timedelta(days=1, hours=14),
        arrivalTime=now + timedelta(days=1, hours=14, minutes=45),
        daysOfWeek='Martedi,Giovedi', price=4.00,
    )

# un account per ciascuno dei tre ruoli, cosi possiamo mostrare
# subito tutte e tre le aree senza doverli creare a mano
if not User.objects.exists():
    User.objects.create(
        firstName='Mario', lastName='Rossi',
        email='mario.rossi@email.com',
        phoneNumber='3331234567',
        codiceFiscale='RSSMRA80A01D612Y',
        password=make_password('password123'),
        status=UserStatus.ACTIVE,
    )

if not Admin.objects.exists():
    Admin.objects.create(
        firstName='Admin', lastName='MarcheMobility',
        email='admin@marchemobility.it',
        password=make_password('admin123'),
    )

if not Controller.objects.exists():
    Controller.objects.create(
        firstName='Luca', lastName='Bianchi',
        email='luca.bianchi@marchemobility.it',
        phoneNumber='3339876543',
        codiceFiscale='BNCLCU85A01D612Y',
        password=make_password('controller123'),
    )

print("--- Account demo ---")
print("Viaggiatore : mario.rossi@email.com / password123")
print("Controllore : luca.bianchi@marchemobility.it / controller123")
print("Admin       : admin@marchemobility.it / admin123")
print("Pannello Django (/admin/): admin / admin123")
print()
print("Sito su http://127.0.0.1:8000/\n")

call_command('runserver', '0.0.0.0:8000', use_reloader=False)
