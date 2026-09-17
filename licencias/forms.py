from django import forms
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string
from .models import SolicitudLicencia, Docente, Materia, HorarioDocente, Suplencia

# --- Función para obtener el siguiente legajo disponible ---
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

# --- FORMULARIO DE ALTA DE DOCENTE ---
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

# --- FORMULARIO DE SOLICITUD DE LICENCIA ---
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

# --- FORMULARIO DE ALTA DE MATERIA ---
class MateriaForm(forms.ModelForm):
    class Meta:
        model = Materia
        fields = ['nombre', 'tipo_modalidad']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'w-full p-2.5 border rounded-lg bg-white focus:ring-2 focus:ring-indigo-500'
            }),
            'tipo_modalidad': forms.Select(attrs={
                'class': 'w-full p-2.5 border rounded-lg bg-white focus:ring-2 focus:ring-indigo-500'
            }),
        }

# --- FORMULARIO DE ALTA DE HORARIO DOCENTE ---
class HorarioDocenteForm(forms.ModelForm):
    class Meta:
        model = HorarioDocente
        fields = ['docente', 'materia', 'curso', 'dia_semana', 'bloque', 'rol', 'seccion']
        widgets = {
            'docente': forms.Select(attrs={'class': 'w-full p-2.5 border rounded-lg bg-white'}),
            'materia': forms.Select(attrs={'class': 'w-full p-2.5 border rounded-lg bg-white'}),
            'curso': forms.Select(attrs={'class': 'w-full p-2.5 border rounded-lg bg-white'}),
            'dia_semana': forms.Select(attrs={'class': 'w-full p-2.5 border rounded-lg bg-white'}),
            'bloque': forms.Select(attrs={'class': 'w-full p-2.5 border rounded-lg bg-white'}),
            'rol': forms.Select(attrs={'class': 'w-full p-2.5 border rounded-lg bg-white'}),
            'seccion': forms.TextInput(attrs={
                'class': 'w-full p-2.5 border rounded-lg bg-white',
                'placeholder': 'Ej: Grupo A, Laboratorio 1 (Opcional)'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        docente = cleaned_data.get('docente')
        bloque = cleaned_data.get('bloque')
        dia_semana = cleaned_data.get('dia_semana')

        # Validación: Evitar que el MISMO docente se superponga consigo mismo en dos aulas al mismo tiempo
        if docente and bloque and dia_semana:
            existente = HorarioDocente.objects.filter(
                docente=docente,
                bloque=bloque,
                dia_semana=dia_semana
            )
            if self.instance.pk:
                existente = existente.exclude(pk=self.instance.pk)
            
            if existente.exists():
                self.add_error('bloque', f"El docente {docente} ya tiene asignada otra clase en este mismo bloque y día.")

        return cleaned_data

# --- FORMULARIO DE ALTA DE SUPLENCIA ---
class SuplenciaForm(forms.ModelForm):
    class Meta:
        model = Suplencia
        fields = ['tipo_cobertura', 'docente_suplente', 'observaciones']
        widgets = {
            'tipo_cobertura': forms.Select(attrs={
                'class': 'w-full p-2.5 border rounded-lg bg-white focus:ring-2 focus:ring-indigo-500',
                'id': 'select_tipo_cobertura'
            }),
            'docente_suplente': forms.Select(attrs={
                'class': 'w-full p-2.5 border rounded-lg bg-white focus:ring-2 focus:ring-indigo-500',
                'id': 'select_docente_suplente'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'w-full p-2.5 border rounded-lg bg-white',
                'rows': 2,
                'placeholder': 'Anotaciones opcionales sobre la cobertura...'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        tipo_cobertura = cleaned_data.get('tipo_cobertura')
        docente_suplente = cleaned_data.get('docente_suplente')

        # Si la cobertura es externa, es obligatorio elegir un docente suplente
        if tipo_cobertura == 'EXTERNA' and not docente_suplente:
            self.add_error('docente_suplente', "Debe seleccionar un docente suplente para la cobertura externa.")

        # En caso de absorción o Jefe de Lab, si no seleccionan suplente, no arroja error
        return cleaned_data