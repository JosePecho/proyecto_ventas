from django import forms

from src.modules.promotions.domain.enums.tipo_promocion import TipoPromocion


class PromocionForm(forms.Form):
    aplica_clientes_frecuentes = forms.BooleanField(required=False, label="Habilitar fidelización automática")
    componentes = forms.JSONField(required=False, widget=forms.HiddenInput())
    nombre = forms.CharField(max_length=120, widget=forms.TextInput(attrs={"class": "form-control"}))
    tipo = forms.ChoiceField(choices=TipoPromocion.opciones(), widget=forms.Select(attrs={"class": "form-select"}))
    descuento_valor = forms.DecimalField(
        min_value=0, max_digits=12, decimal_places=2,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
    )
    producto_id = forms.UUIDField(required=False, widget=forms.Select())
    cantidad_requerida = forms.IntegerField(required=False, min_value=0, widget=forms.NumberInput(attrs={"class": "form-control"}))
    cantidad_gratuita = forms.IntegerField(required=False, min_value=0, widget=forms.NumberInput(attrs={"class": "form-control"}))
    vigencia_desde = forms.DateTimeField(required=False, widget=forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}))
    vigencia_hasta = forms.DateTimeField(required=False, widget=forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}))

    def __init__(self, *args, **kwargs):
        if args and args[0] and hasattr(args[0], "getlist") and args[0].getlist("combo_producto"):
            import json
            datos = args[0].copy()
            productos, cantidades = datos.getlist("combo_producto"), datos.getlist("combo_cantidad")
            if len(productos) != len(cantidades):
                datos["componentes"] = "null"
            else:
                componentes = []
                for producto, cantidad in zip(productos, cantidades):
                    try:
                        numero = int(cantidad)
                    except (ValueError, TypeError):
                        numero = 0
                    componentes.append({"producto_id": producto, "cantidad": numero})
                datos["componentes"] = json.dumps(componentes)
            args = (datos, *args[1:])
        super().__init__(*args, **kwargs)
        from src.modules.catalog.infrastructure.persistence.django_models.producto_model import ProductoModel
        self.fields["producto_id"].widget.choices = [("", "Todos los productos")] + [
            (str(p.id), p.nombre) for p in ProductoModel.objects.filter(activo=True)]
        self.productos_combo = [{"id": valor, "nombre": nombre} for valor, nombre in self.fields["producto_id"].widget.choices if valor]

    def clean(self):
        datos = super().clean()
        desde, hasta = datos.get("vigencia_desde"), datos.get("vigencia_hasta")
        if bool(desde) != bool(hasta):
            raise forms.ValidationError("Indica ambas fechas de vigencia")
        if desde and hasta and hasta <= desde:
            self.add_error("vigencia_hasta", "La fecha de fin debe ser posterior al inicio")
        if datos.get("tipo") == TipoPromocion.NX1.value and not datos.get("producto_id"):
            self.add_error("tipo", "NX1 requiere un producto especifico")
        tipo, valor = datos.get("tipo"), datos.get("descuento_valor")
        if valor is not None and (valor < 0 or tipo == "PORCENTAJE" and not 0 < valor <= 100):
            self.add_error("descuento_valor", "Porcentaje entre 0 y 100, mayor a cero")
        if tipo == "NX1":
            datos["cantidad_requerida"] = datos.get("cantidad_requerida") or 2
            datos["cantidad_gratuita"] = datos.get("cantidad_gratuita") or 1
        if tipo == "COMBO":
            from src.modules.promotions.domain.entities.promocion import Promocion
            from src.shared.domain.exceptions.domain_exception import DomainException
            try:
                Promocion(nombre=datos.get("nombre") or "Combo", tipo="COMBO", componentes=datos.get("componentes") or [])
            except DomainException as exc:
                self.add_error("componentes", str(exc))
        datos["componentes"] = datos.get("componentes") or []
        datos["cantidad_requerida"] = datos.get("cantidad_requerida") or 0
        datos["cantidad_gratuita"] = datos.get("cantidad_gratuita") or 0
        from src.modules.catalog.infrastructure.persistence.django_models.producto_model import ProductoModel
        if datos.get("producto_id") and not ProductoModel.objects.filter(pk=datos["producto_id"], activo=True).exists():
            self.add_error("producto_id", "Producto no disponible")
        if tipo == "COMBO" and "componentes" not in self.errors:
            ids = [str(c["producto_id"]) for c in datos["componentes"]]
            if ProductoModel.objects.filter(pk__in=ids, activo=True).count() != len(ids):
                self.add_error("componentes", "Todos los productos del combo deben existir y estar activos")
        return datos

