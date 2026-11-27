"""Vista de cierre de sesion."""
from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.views.decorators.http import require_POST


@require_POST
def logout_view(request):
    logout(request)
    messages.info(request, "Sesion finalizada")
    return redirect("identity:login")
