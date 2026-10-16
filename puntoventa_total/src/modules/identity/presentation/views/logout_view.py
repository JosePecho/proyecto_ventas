"""Vista de cierre de sesion."""
from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import logout
from django.shortcuts import redirect


def logout_view(request):
    logout(request)
    messages.info(request, "Sesion finalizada")
    return redirect("identity:login")
