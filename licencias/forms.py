from django import forms
from .models import SolicitudLicencia

class SolicitudLicenciaForm(forms.ModelForm):
    class Meta:
        model = SolicitudLicencia
        fields = [
            'docente',
            'tipo_licencia',
            'fecha_solicitud',
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
            'tipo_incidencia': forms.Select(attrs={'class': 'w-full p-2.5 bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 font-medium'}),
            'minutos_tarde': forms.NumberInput(attrs={'class': 'w-full p-2.5 bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500', 'placeholder': 'Ej: 30'}),
            'minutos_retiro': forms.NumberInput(attrs={'class': 'w-full p-2.5 bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500', 'placeholder': 'Ej: 45'}),
            'bloques_afectados': forms.SelectMultiple(attrs={'class': 'w-full p-2.5 bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500'}),
            'comprobante_pdf': forms.FileInput(attrs={'class': 'w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100'}),
            'observaciones': forms.Textarea(attrs={'rows': 2, 'class': 'w-full p-2.5 bg-slate-50 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500'}),
        }