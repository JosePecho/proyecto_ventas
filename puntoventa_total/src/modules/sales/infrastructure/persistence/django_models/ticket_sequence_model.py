from django.db import models


class TicketSequenceModel(models.Model):
    dia = models.DateField(primary_key=True)
    ultimo = models.PositiveBigIntegerField(default=0)

    class Meta:
        db_table = "sales_ticket_sequence"
