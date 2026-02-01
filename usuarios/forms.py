from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.core.exceptions import ValidationError
from .models import Usuario
from sucursales.models import Sucursal

class RegistroUsuarioForm(UserCreationForm):
    """
    Formulario de registro de nuevos usuarios
    Los usuarios deben ser aprobados por un administrador
    """
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'correo@ejemplo.com'
        })
    )
    
    first_name = forms.CharField(
        required=True,
        label='Nombre',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tu nombre'
        })
    )
    
    last_name = forms.CharField(
        required=True,
        label='Apellido',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tu apellido'
        })
    )
    
    documento = forms.CharField(
        required=True,
        label='Documento de Identidad',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '1234567890'
        })
    )
    
    telefono = forms.CharField(
        required=False,
        label='Teléfono',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '3001234567'
        })
    )
    
    rol = forms.ChoiceField(
        choices=[('EMPLEADO', 'Empleado'), ('AUDITOR', 'Auditor/Contador')],
        label='Rol Solicitado',
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        help_text='El administrador verificará y aprobará tu solicitud'
    )
    
    class Meta:
        model = Usuario
        fields = ['username', 'email', 'first_name', 'last_name', 'documento', 
                  'telefono', 'rol', 'password1', 'password2']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Nombre de usuario'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Contraseña'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirmar contraseña'
        })
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Usuario.objects.filter(email=email).exists():
            raise ValidationError('Este correo electrónico ya está registrado.')
        return email
    
    def clean_documento(self):
        documento = self.cleaned_data.get('documento')
        if Usuario.objects.filter(documento=documento).exists():
            raise ValidationError('Este documento ya está registrado.')
        return documento


class LoginForm(AuthenticationForm):
    """
    Formulario de inicio de sesión personalizado
    """

    # 🔥 AQUÍ EDITAS EL MENSAJE DEL LOGIN INCORRECTO
    error_messages = {
        'invalid_login': '❌ Usuario o contraseña incorrectos. Si tus credenciales son correctas, tu cuenta puede estar inactiva o pendiente de aprobación por un administrador.',
        'inactive': '⚠️ Esta cuenta está desactivada.',
    }

    username = forms.CharField(
        label='Usuario',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre de usuario',
            'autofocus': True
        })
    )

    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contraseña'
        })
    )

    def confirm_login_allowed(self, user):
        """
        Verificar que el usuario esté aprobado y activo
        """
        if not user.is_active:
            raise ValidationError(
                self.error_messages['inactive'],
                code='inactive',
            )

        if not user.aprobado and not user.is_superuser:
            raise ValidationError(
                '⏳ Tu cuenta aún no ha sido aprobada por un administrador.',
                code='not_approved',
            )

class PerfilUsuarioForm(forms.ModelForm):
    """
    Formulario para editar el perfil del usuario
    """
    
    class Meta:
        model = Usuario
        fields = ['first_name', 'last_name', 'email', 'telefono', 'foto_perfil', 'modo_oscuro']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'foto_perfil': forms.FileInput(attrs={'class': 'form-control'}),
            'modo_oscuro': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CambiarPasswordForm(PasswordChangeForm):
    """
    Formulario para cambiar contraseña
    """
    
    old_password = forms.CharField(
        label='Contraseña Actual',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contraseña actual'
        })
    )
    
    new_password1 = forms.CharField(
        label='Nueva Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nueva contraseña'
        })
    )
    
    new_password2 = forms.CharField(
        label='Confirmar Nueva Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirmar nueva contraseña'
        })
    )


class AprobarUsuarioForm(forms.ModelForm):
    """
    Formulario para que administradores aprueben usuarios y asignen sucursal
    """
    class Meta:
        model = Usuario
        fields = ['rol', 'aprobado', 'sucursal']
        widgets = {
            'rol': forms.Select(attrs={'class': 'form-select'}),
            'aprobado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sucursal': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'sucursal': 'Asignar Sucursal *',
            'rol': 'Rol del Usuario',
            'aprobado': 'Aprobar Usuario'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar solo sucursales activas
        self.fields['sucursal'].queryset = Sucursal.objects.filter(activa=True)
        # Hacer sucursal obligatoria
        self.fields['sucursal'].required = True
        self.fields['sucursal'].empty_label = "-- Selecciona una sucursal --"
    
    def clean(self):
        cleaned_data = super().clean()
        aprobado = cleaned_data.get('aprobado')
        sucursal = cleaned_data.get('sucursal')
        
        # Si se aprueba el usuario, DEBE tener sucursal
        if aprobado and not sucursal:
            raise forms.ValidationError(
                'Debes asignar una sucursal antes de aprobar al usuario.'
            )
        
        return cleaned_data
