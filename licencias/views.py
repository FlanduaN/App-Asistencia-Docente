from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from datetime import date, datetime, timedelta
from .models import HorarioDocente, SolicitudLicencia, Docente, BloqueHorario, Suplencia
from .forms import SolicitudLicenciaForm


# ------------------------------------------------------------------
# CONMUTADOR RÁPIDO DE PERFILES DE PRUEBA
# ------------------------------------------------------------------
def cambiar_perfil(request, perfil):
    """
    Guarda el perfil activo en la sesión y redirige a la vista correspondiente.
    """
    perfiles_validos = ['regente', 'preceptor', 'secretario']
    if perfil in perfiles_validos:
        request.session['perfil_activo'] = perfil

    if perfil == 'preceptor':
        return redirect('grilla_horaria')
    elif perfil == 'secretario':
        return redirect('dashboard_secretaria')
    else:
        return redirect('dashboard_regencia')


# ------------------------------------------------------------------
# PANTALLA DE LOGIN (Deshabilitada obligatoriedad por ahora)
# ------------------------------------------------------------------
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard_regencia')
    else:
        form = AuthenticationForm()
    return render(request, 'licencias/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


# ------------------------------------------------------------------
# FUNCIONES AUXILIARES
# ------------------------------------------------------------------
def es_bloque_afectado(bloque, licencia, todos_bloques_docente):
    if licencia.tipo_incidencia == 'BLOQUES':
        return licencia.bloques_afectados.filter(id=bloque.id).exists()

    if licencia.tipo_incidencia == 'TARDE' and licencia.minutos_tarde:
        primer_bloque = todos_bloques_docente.order_by('bloque__hora_inicio').first()
        if primer_bloque:
            hora_inicio_jornada = datetime.combine(date.today(), primer_bloque.bloque.hora_inicio)
            hora_llegada_real = (hora_inicio_jornada + timedelta(minutes=licencia.minutos_tarde)).time()
            return bloque.hora_inicio < hora_llegada_real
        return True

    if licencia.tipo_incidencia == 'RETIRO' and licencia.minutos_retiro:
        ultimo_bloque = todos_bloques_docente.order_by('bloque__hora_fin').last()
        if ultimo_bloque:
            hora_fin_jornada = datetime.combine(date.today(), ultimo_bloque.bloque.hora_fin)
            hora_salida_real = (hora_fin_jornada - timedelta(minutes=licencia.minutos_retiro)).time()
            return bloque.hora_fin > hora_salida_real
        return True

    return True


# ------------------------------------------------------------------
# VISTAS DE PANELES Y DASHBOARDS
# ------------------------------------------------------------------
def dashboard_regencia(request):
    request.session['perfil_activo'] = request.session.get('perfil_activo', 'regente')
    fecha_param = request.GET.get('fecha')
    
    if fecha_param:
        try:
            fecha_seleccionada = datetime.strptime(fecha_param, '%Y-%m-%d').date()
        except ValueError:
            fecha_seleccionada = date.today()
    else:
        fecha_seleccionada = date.today()

    dia_actual_num = fecha_seleccionada.isoweekday()
    nombre_dias = {1: 'Lunes', 2: 'Martes', 3: 'Miércoles', 4: 'Jueves', 5: 'Viernes', 6: 'Sábado', 7: 'Domingo'}
    dia_actual_nombre = nombre_dias.get(dia_actual_num, 'Lunes')

    licencias_hoy = SolicitudLicencia.objects.filter(
        fecha_solicitud=fecha_seleccionada
    ).select_related('docente__user', 'tipo_licencia').prefetch_related('bloques_afectados')

    ausencias_procesadas = []
    for licencia in licencias_hoy:
        horarios_docente = HorarioDocente.objects.filter(
            docente=licencia.docente,
            dia_semana=dia_actual_num
        ).select_related('bloque', 'materia', 'curso').order_by('bloque__numero')

        bloques_evaluados = []
        for h in horarios_docente:
            if es_bloque_afectado(h.bloque, licencia, horarios_docente):
                suplencia = Suplencia.objects.filter(
                    licencia=licencia,
                    horario=h,
                    fecha=fecha_seleccionada
                ).select_related('docente_suplente__user').first()

                bloques_evaluados.append({
                    'horario': h,
                    'afectado': True,
                    'suplencia': suplencia
                })

        if bloques_evaluados:
            ausencias_procesadas.append({
                'licencia': licencia,
                'docente': licencia.docente,
                'bloques_evaluados': bloques_evaluados
            })

    contexto = {
        'dia_nombre': dia_actual_nombre,
        'fecha_seleccionada': fecha_seleccionada,
        'ausencias_procesadas': ausencias_procesadas,
        'total_ausentes': len(ausencias_procesadas),
        'es_fin_de_semana': dia_actual_num > 5,
        'perfil_actual': request.session.get('perfil_activo', 'regente'),
    }
    
    return render(request, 'licencias/dashboard.html', contexto)


def grilla_horaria(request):
    """ VISTA UTILIZADA POR PRECEPTOR/A Y REGENTE """
    fecha_param = request.GET.get('fecha')
    if fecha_param:
        try:
            fecha_seleccionada = datetime.strptime(fecha_param, '%Y-%m-%d').date()
        except ValueError:
            fecha_seleccionada = date.today()
    else:
        fecha_seleccionada = date.today()

    dia_actual_num = fecha_seleccionada.isoweekday()
    nombre_dias = {1: 'Lunes', 2: 'Martes', 3: 'Miércoles', 4: 'Jueves', 5: 'Viernes', 6: 'Sábado', 7: 'Domingo'}
    dia_actual_nombre = nombre_dias.get(dia_actual_num, 'Lunes')

    bloques = BloqueHorario.objects.all().order_by('numero')
    licencias_hoy = SolicitudLicencia.objects.filter(
        fecha_solicitud=fecha_seleccionada
    ).select_related('docente__user', 'tipo_licencia').prefetch_related('bloques_afectados')

    grilla_bloques = []
    for bloque in bloques:
        incidencias_bloque = []
        for licencia in licencias_hoy:
            horarios_docente = HorarioDocente.objects.filter(
                docente=licencia.docente,
                dia_semana=dia_actual_num,
                bloque=bloque
            ).select_related('materia', 'curso')

            for h in horarios_docente:
                todos_horarios = HorarioDocente.objects.filter(docente=licencia.docente, dia_semana=dia_actual_num)
                if es_bloque_afectado(bloque, licencia, todos_horarios):
                    suplencia = Suplencia.objects.filter(
                        licencia=licencia,
                        horario=h,
                        fecha=fecha_seleccionada
                    ).select_related('docente_suplente__user').first()

                    incidencias_bloque.append({
                        'curso': h.curso,
                        'materia': h.materia,
                        'docente': licencia.docente,
                        'suplencia': suplencia,
                        'licencia': licencia,
                        'horario': h
                    })

        grilla_bloques.append({
            'bloque': bloque,
            'incidencias': incidencias_bloque
        })

    contexto = {
        'fecha_seleccionada': fecha_seleccionada,
        'dia_nombre': dia_actual_nombre,
        'grilla_bloques': grilla_bloques,
        'es_fin_de_semana': dia_actual_num > 5,
        'perfil_actual': request.session.get('perfil_activo', 'preceptor'),
    }
    return render(request, 'licencias/grilla_horaria.html', contexto)


def dashboard_secretaria(request):
    """ VISTA SECRETARIO/A (Basada en Regente con módulo administrativo) """
    request.session['perfil_activo'] = 'secretario'
    fecha_param = request.GET.get('fecha')
    
    if fecha_param:
        try:
            fecha_seleccionada = datetime.strptime(fecha_param, '%Y-%m-%d').date()
        except ValueError:
            fecha_seleccionada = date.today()
    else:
        fecha_seleccionada = date.today()

    dia_actual_num = fecha_seleccionada.isoweekday()
    nombre_dias = {1: 'Lunes', 2: 'Martes', 3: 'Miércoles', 4: 'Jueves', 5: 'Viernes', 6: 'Sábado', 7: 'Domingo'}
    dia_actual_nombre = nombre_dias.get(dia_actual_num, 'Lunes')

    licencias_hoy = SolicitudLicencia.objects.filter(
        fecha_solicitud=fecha_seleccionada
    ).select_related('docente__user', 'tipo_licencia').prefetch_related('bloques_afectados')

    ausencias_procesadas = []
    for licencia in licencias_hoy:
        horarios_docente = HorarioDocente.objects.filter(
            docente=licencia.docente,
            dia_semana=dia_actual_num
        ).select_related('bloque', 'materia', 'curso').order_by('bloque__numero')

        bloques_evaluados = []
        for h in horarios_docente:
            if es_bloque_afectado(h.bloque, licencia, horarios_docente):
                suplencia = Suplencia.objects.filter(
                    licencia=licencia,
                    horario=h,
                    fecha=fecha_seleccionada
                ).select_related('docente_suplente__user').first()

                bloques_evaluados.append({
                    'horario': h,
                    'afectado': True,
                    'suplencia': suplencia
                })

        if bloques_evaluados:
            ausencias_procesadas.append({
                'licencia': licencia,
                'docente': licencia.docente,
                'bloques_evaluados': bloques_evaluados
            })

    contexto = {
        'dia_nombre': dia_actual_nombre,
        'fecha_seleccionada': fecha_seleccionada,
        'ausencias_procesadas': ausencias_procesadas,
        'total_ausentes': len(ausencias_procesadas),
        'es_fin_de_semana': dia_actual_num > 5,
        'perfil_actual': 'secretario',
    }
    
    return render(request, 'licencias/dashboard_secretaria.html', contexto)


def registrar_inasistencia(request):
    docente_id = request.GET.get('docente_id')
    fecha_param = request.GET.get('fecha')
    
    docente_inicial = None
    if docente_id:
        docente_inicial = get_object_or_404(Docente, id=docente_id)

    fecha_inicial = date.today()
    if fecha_param:
        try:
            fecha_inicial = datetime.strptime(fecha_param, '%Y-%m-%d').date()
        except ValueError:
            pass

    if request.method == 'POST':
        form = SolicitudLicenciaForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect(f"/?fecha={form.cleaned_data['fecha_solicitud']}")
    else:
        form = SolicitudLicenciaForm(initial={
            'docente': docente_inicial,
            'fecha_solicitud': fecha_inicial
        })

    return render(request, 'licencias/registrar_inasistencia.html', {'form': form, 'docente': docente_inicial})


def editar_inasistencia(request, licencia_id):
    licencia = get_object_or_404(SolicitudLicencia, id=licencia_id)
    
    if request.method == 'POST':
        form = SolicitudLicenciaForm(request.POST, request.FILES, instance=licencia)
        if form.is_valid():
            form.save()
            return redirect(f"/?fecha={licencia.fecha_solicitud}")
    else:
        form = SolicitudLicenciaForm(instance=licencia)

    return render(request, 'licencias/editar_inasistencia.html', {'form': form, 'licencia': licencia})


def eliminar_inasistencia(request, licencia_id):
    licencia = get_object_or_404(SolicitudLicencia, id=licencia_id)
    fecha_redireccion = licencia.fecha_solicitud

    if request.method == 'POST':
        licencia.delete()
        return redirect(f"/?fecha={fecha_redireccion}")

    return render(request, 'licencias/confirmar_eliminar.html', {'licencia': licencia})