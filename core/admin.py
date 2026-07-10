from django.contrib import admin

from .models import (
    User, UserReport, Controller, ControllerReport,
    Route, Ticket, TicketInspection, Fine,
    Admin as AdminModel, GlobalNotification,
)

admin.site.register(User)
admin.site.register(UserReport)
admin.site.register(Controller)
admin.site.register(ControllerReport)
admin.site.register(Route)
admin.site.register(Ticket)
admin.site.register(TicketInspection)
admin.site.register(Fine)
admin.site.register(AdminModel)
admin.site.register(GlobalNotification)
