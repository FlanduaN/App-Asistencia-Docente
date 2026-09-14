from django import forms
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string
from .models import SolicitudLicencia, Docente

# Función para obtener el siguiente legajo disponible
def obtener_siguiente_legajo():
    """ Busca el número de legajo numérico más alto registrado y sugiere el siguiente """
    docentes = Docente.objects.all()
    legajos_numericos = []
    for d in docentes:
        if d.legajo and d.legajo.isdigit():
            legajos_numericos.append(int(d.legajo))
    
    if legajos_numericos:
        return str(max(legajos_numericos) + 1)
    return "1001"  # Valor inicial por defecto si no hay legajos cargados

class AltaDocenteForm(forms.Form):
    first_name = forms.CharField(label="Nombre", max_length=150, widget=forms.TextInput(attrs={'class': 'w-full p-2.5 border rounded-lg'}))
    last_name = forms.CharField(label="Apellido", max_length=150, widget=forms.TextInput(attrs={'class': 'w-full p-2.5 border rounded-lg'}))
    email = forms.EmailField(label="Correo Electrónico", widget=forms.EmailInput(attrs={'class': 'w-full p-2.5 border rounded-lg', 'placeholder': 'ejemplo@correo.com'}))
    telefono = forms.CharField(label="Teléfono / Celular", max_length=30, required=False, widget=forms.TextInput(attrs={'class': 'w-full p-2.5 border rounded-lg', 'placeholder': 'Ej: 11 2345-6789'}))
    dni = forms.CharField(label="DNI", max_length=20, widget=forms.TextInput(attrs={'class': 'w-full p-2.5 border rounded-lg'}))
    legajo = forms.CharField(label="N° de Legajo", max_length=50, widget=forms.TextInput(attrs={'class': 'w-full p-2.5 border rounded-lg bg-amber-50 font-bold'}))
    
    ROL_CHOICES = [
        ('docente', 'Docente'),
        ('preceptor', 'Preceptor/a'),
        ('regente', 'Regente'),
        ('secretario', 'Secretario/a'),
    ]
    rol = forms.ChoiceField(choices=ROL_CHOICES, label="Cargo / Rol Asignado", widget=forms.Select(attrs={'class': 'w-full p-2.5 border rounded-lg'}))

    # VALIDACIÓN UNICIDAD DE EMAIL Y USERNAME DERIVADO
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("DUPLICADO_MAIL")
        
        username_provisorio = email.split('@')[0]
        if User.objects.filter(username=username_provisorio).exists():
            raise forms.ValidationError(f"El usuario '{username_provisorio}' (derivado del correo) ya existe en el sistema.")
        return email

    # VALIDACIÓN UNICIDAD DE DNI
    def clean_dni(self):
        dni = self.cleaned_data.get('dni')
        if Docente.objects.filter(dni=dni).exists():
            raise forms.ValidationError("Este número de DNI ya pertenece a otro docente registrado.")
        return dni

    # VALIDACIÓN UNICIDAD DE LEGAJO
    def clean_legajo(self):
        legajo = self.cleaned_data.get('legajo')
        if Docente.objects.filter(legajo=legajo).exists():
            raise forms.ValidationError(f"El Legajo N° {legajo} ya está asignado. Por favor ingresa otro número.")
        return legajo

    def save(self):
        email = self.cleaned_data['email']
        # Extraer usuario eliminando lo que esté a partir del '@'
        username = email.split('@')[0]
        
        password_provisoria = get_random_string(length=8)
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password_provisoria,
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name']
        )
        
        docente = Docente.objects.create(
            user=user,
            legajo=self.cleaned_data['legajo'],
            dni=self.cleaned_data['dni'],
            telefono=self.cleaned_data.get('telefono')
        )

        return docente, password_provisoria, username

# Formulario para la creación de una solicitud de licencia
class SolicitudLicenciaForm(forms.ModelForm):
    class Meta:
        model = SolicitudLicencia
        fields = [
            'docente',
            'tipo_licencia',
            'fecha_solicitud',
            'fecha_hasta',
            'tipo_incidencia',
            'minutos_tarde',
            'minutos_retiro',
            'bloques_afectados',
            'comprobante_pdf',
            'observaciones'
        ]
        widgets = {
            'docente': forms.Select(attrs={'class': 'w-full p-2.5 bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 font-medium'}),
            'tipo_licencia': forms.Select(attrs={'class': 'w-full p-2.5 bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 font-medium'}),
            'fecha_solicitud': forms.DateInput(attrs={'type': 'date', 'class': 'w-full p-2.5 bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 font-medium'}),
            'fecha_hasta': forms.DateInput(attrs={'type': 'date', 'class': 'w-full p-2.5 bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 font-medium'}),
            'tipo_incidencia': forms.Select(attrs={'class': 'w-full p-2.5 bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 font-medium'}),
            'minutos_tarde': forms.NumberInput(attrs={'class': 'w-full p-2.5 bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500', 'placeholder': 'Ej: 30'}),
            'minutos_retiro': forms.NumberInput(attrs={'class': 'w-full p-2.5 bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500', 'placeholder': 'Ej: 45'}),
            'bloques_afectados': forms.SelectMultiple(attrs={'class': 'w-full p-2.5 bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500'}),
            'comprobante_pdf': forms.FileInput(attrs={'class': 'w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100'}),
            'observaciones': forms.Textarea(attrs={'rows': 2, 'class': 'w-full p-2.5 bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500'}),
        }

    # Validación de fechas: 'fecha_hasta' no puede ser anterior a 'fecha_solicitud'
    def clean(self):
        cleaned_data = super().clean()
        fecha_solicitud = cleaned_data.get('fecha_solicitud')
        fecha_hasta = cleaned_data.get('fecha_hasta')

        if fecha_solicitud and fecha_hasta:
            if fecha_hasta < fecha_solicitud:
                # Asigna el error directamente al campo 'fecha_hasta'
                self.add_error('fecha_hasta', "La Fecha Hasta no puede ser anterior a la Fecha Desde.")
        elif fecha_solicitud and not fecha_hasta:
            cleaned_data['fecha_hasta'] = fecha_solicitud

        return cleaned_data