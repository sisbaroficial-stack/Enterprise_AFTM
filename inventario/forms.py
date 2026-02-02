from django import forms
from .models import Producto
from categorias.models import Categoria, Subcategoria
from proveedores.models import Proveedor


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = [
            'codigo', 'codigo_barras', 'nombre', 'descripcion',
            'categoria', 'subcategoria', 'unidad_medida',
            'cantidad_minima', 'precio_compra', 'precio_venta',  # ✅ AGREGADO
            'precio_venta_minimo', 'proveedor',  # ✅ AGREGADO
            'imagen', 'ubicacion'
        ]
        widgets = {
            'codigo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Código único del producto'
            }),
            'codigo_barras': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Código de barras (opcional)'
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del producto'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción detallada'
            }),
            'categoria': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_categoria'
            }),
            'subcategoria': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_subcategoria'
            }),
            'cantidad_minima': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0
            }),
            'unidad_medida': forms.Select(attrs={
                'class': 'form-select'
            }),
            'precio_compra': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': 0
            }),
            'proveedor': forms.Select(attrs={
                'class': 'form-select'
            }),
            'imagen': forms.FileInput(attrs={
                'class': 'form-control'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['codigo_barras'].required = False
        self.fields['descripcion'].required = False
        self.fields['subcategoria'].required = False
        self.fields['proveedor'].required = False
        self.fields['imagen'].required = False

        self.fields['categoria'].queryset = Categoria.objects.filter(activa=True)
        self.fields['proveedor'].queryset = Proveedor.objects.filter(activo=True)

        if 'categoria' in self.data:
            try:
                categoria_id = int(self.data.get('categoria'))
                self.fields['subcategoria'].queryset = Subcategoria.objects.filter(
                    categoria_id=categoria_id,
                    activa=True
                )
            except (ValueError, TypeError):
                pass
        elif self.instance.pk:
            self.fields['subcategoria'].queryset = self.instance.categoria.subcategorias.filter(
                activa=True
            )
