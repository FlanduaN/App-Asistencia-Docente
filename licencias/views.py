from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.contrib import messages
from django.contrib.auth.models import User
from datetime import date, datetime, timedelta
from .models import HorarioDocente, SolicitudLicencia, Docente, BloqueHorario, Suplencia
from .forms import SolicitudLicenciaForm, AltaDocenteForm, SuplenciaForm, obtener_siguiente_legajo


# ------------------------------------------------------------------
# AUTENTICACIÓN Y CONTROL DE ACCESO
# ------------------------------------------------------------------
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard_regencia')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            # Verificar si el docente requiere cambio obligatorio de clave provisoria
            try:
                if hasattr(user, 'docente') and user.docente.debe_cambiar_password:
                    messages.info(request, "Por seguridad, debes cambiar tu clave provisoria en el primer inicio.")
                    return redirect('cambiar_password')
            except Exception:
                pass

            return redirect('dashboard_regencia')
        else:
            messages.error(request, "Usuario o contraseña incorrectos.")
    else:
        form = AuthenticationForm()

    return render(request, 'licencias/login.html', {'form': form})


@login_required
def cambiar_password_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Mantiene la sesión activa
            
            # Desactivar bandera de cambio de clave obligatoria
            try:
                if hasattr(user, 'docente'):
                    docente = user.docente
                    docente.debe_cambiar_password = False
                    docente.save()
            except Exception:
                pass

            messages.success(request, "¡Tu contraseña se ha actualizado exitosamente!")
            return redirect('dashboard_regencia')
    else:
        form = PasswordChangeForm(user=request.user)

    return render(request, 'licencias/cambiar_password.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


# ------------------------------------------------------------------
# CONMUTADOR RÁPIDO DE PERFILES
# ------------------------------------------------------------------
@login_required
def cambiar_perfil(request, perfil):
    perfiles_validos = ['regente', 'preceptor', 'secretario', 'docente']
    if perfil in perfiles_validos:
        request.session['perfil_activo'] = perfil

    if perfil == 'preceptor':
        return redirect('grilla_horaria')
    elif perfil == 'secretario':
        return redirect('dashboard_secretaria')
    elif perfil == 'docente':
        return redirect('dashboard_docente')
    else:
        return redirect('dashboard_regencia')


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
# GESTIÓN DE PERSONAL (SECRETARÍA)
# ------------------------------------------------------------------
@login_required
def gestion_docentes(request):
    ver_inactivos = request.GET.get('inactivos') == '1'
    
    if ver_inactivos:
        docentes = Docente.objects.filter(user__is_active=False).select_related('user')
    else:
        docentes = Docente.objects.filter(user__is_active=True).select_related('user')

    contexto = {
        'docentes': docentes,
        'ver_inactivos': ver_inactivos,
        'total_activos': Docente.objects.filter(user__is_active=True).count(),
        'total_inactivos': Docente.objects.filter(user__is_active=False).count(),
        'perfil_actual': 'secretario'
    }
    return render(request, 'licencias/gestion_docentes.html', contexto)


@login_required
def alta_docente(request):
    if request.method == 'POST':
        form = AltaDocenteForm(request.POST)
        if form.is_valid():
            docente, password_provisoria, username_generado = form.save()
            
            asunto = "Bienvenido/a al Sistema de Asistencia - Datos de Acceso"
            mensaje = (
                f"Hola {docente.user.first_name},\n\n"
                f"Se ha creado tu cuenta en el Sistema de Asistencia Institucional.\n\n"
                f"Tus credenciales de acceso son:\n"
                f"📌 Usuario de ingreso: {username_generado}\n"
                f"🔑 Clave Provisoria: {password_provisoria}\n\n"
                f"Por favor, ingresa al sistema y cambia tu contraseña en el primer inicio.\n"
            )
            
            try:
                send_mail(
                    asunto,
                    mensaje,
                    'no-reply@colegio.edu.ar',
                    [docente.user.email],
                    fail_silently=False,
                )
                messages.success(request, f"Docente {docente.user.get_full_name()} creado. Usuario: '{username_generado}'. Se envió la clave a {docente.user.email}.")
            except Exception:
                messages.warning(request, f"Docente creado pero no se pudo enviar el mail. Usuario: '{username_generado}' | Clave provisoria: {password_provisoria}")

            return redirect('gestion_docentes')
    else:
        form = AltaDocenteForm(initial={
            'legajo': obtener_siguiente_legajo()
        })

    return render(request, 'licencias/alta_docente.html', {'form': form})


@login_required
def dar_de_baja_docente(request, docente_id):
    docente = get_object_or_404(Docente, id=docente_id)
    docente.user.is_active = False
    docente.user.save()
    messages.info(request, f"El docente {docente.user.get_full_name()} ha sido dado de baja (archivado).")
    return redirect('gestion_docentes')


@login_required
def reactivar_docente(request, docente_id):
    docente = get_object_or_404(Docente, id=docente_id)
    docente.user.is_active = True
    docente.user.save()
    messages.success(request, f"El docente {docente.user.get_full_name()} ha sido reactivado exitosamente.")
    return redirect('gestion_docentes')


# ------------------------------------------------------------------
# VISTAS DE PANELES Y DASHBOARDS
# ------------------------------------------------------------------
# ---- vista principal para el perfil de regencia
@login_required
def dashboard_regencia(request):
    fecha_str = request.GET.get('fecha', datetime.now().strftime('%Y-%m-%d'))
    try:
        fecha_seleccionada = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    except ValueError:
        fecha_seleccionada = datetime.now().date()

    # Días de la semana en Django (1=Lunes, 7=Domingo)
    dia_actual_num = fecha_seleccionada.isoweekday()

    licencias_hoy = SolicitudLicencia.objects.filter(
        fecha_solicitud__lte=fecha_seleccionada,
        fecha_hasta__gte=fecha_seleccionada
    ).select_related('docente__user', 'tipo_licencia').prefetch_related('bloques_afectados')

    ausencias_procesadas = []

    for licencia in licencias_hoy:
        horarios_docente = HorarioDocente.objects.filter(
            docente=licencia.docente,
            dia_semana=dia_actual_num
        ).select_related('bloque', 'materia', 'curso').order_by('bloque__numero')

        bloques_evaluados = []
        for h in horarios_docente:
            # Buscar si existen co-docentes en el mismo bloque, materia y curso
            co_docentes = HorarioDocente.objects.filter(
                bloque=h.bloque,
                curso=h.curso,
                materia=h.materia,
                dia_semana=dia_actual_num
            ).exclude(docente=licencia.docente).select_related('docente__user')

            # Buscar si ya se registró una cobertura (suplencia o absorción)
            suplencia = Suplencia.objects.filter(
                licencia=licencia,
                horario=h,
                fecha=fecha_seleccionada
            ).select_related('docente_suplente__user').first()

            bloques_evaluados.append({
                'horario': h,
                'co_docentes': co_docentes,
                'modalidad': h.materia.tipo_modalidad,
                'es_pareja': h.materia.tipo_modalidad == 'PAREJA' and co_docentes.exists(),
                'es_taller': h.materia.tipo_modalidad == 'TALLER',
                'suplencia': suplencia
            })

        ausencias_procesadas.append({
            'licencia': licencia,
            'docente': licencia.docente,
            'bloques_evaluados': bloques_evaluados
        })

    contexto = {
        'ausencias_procesadas': ausencias_procesadas,
        'fecha_seleccionada': fecha_seleccionada,
        'perfil_actual': 'regente'
    }
    return render(request, 'licencias/dashboard.html', contexto)

# ---- vista principal para el perfil de preceptoría (grilla horaria)
@login_required
def grilla_horaria(request):
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

    # (Consulta por Rango de Fechas):
    licencias_hoy = SolicitudLicencia.objects.filter(
        fecha_solicitud__lte=fecha_seleccionada,
        fecha_hasta__gte=fecha_seleccionada
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

# ---- vista principal para el perfil de secretaría
@login_required
def dashboard_secretaria(request):
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

    # (Consulta por Rango de Fechas):
    licencias_hoy = SolicitudLicencia.objects.filter(
        fecha_solicitud__lte=fecha_seleccionada,
        fecha_hasta__gte=fecha_seleccionada
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

        # SE INCLUYE SIEMPRE LA LICENCIA EN EL PANEL (con o sin horarios asignados)
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

# ---- vista principal para el perfil de docente
@login_required
def dashboard_docente(request):
    """ Vista exclusiva para que el docente consulte su horario y gestione sus licencias """
    request.session['perfil_activo'] = 'docente'
    
    # Intentar obtener el perfil de docente vinculado al usuario
    try:
        docente = request.user.docente
    except Exception:
        messages.warning(request, "Tu usuario no tiene un perfil de Docente asociado en la base de datos.")
        return redirect('dashboard_regencia')

    # Días de la semana para mapear el horario
    nombre_dias = {1: 'Lunes', 2: 'Martes', 3: 'Miércoles', 4: 'Jueves', 5: 'Viernes', 6: 'Sábado', 7: 'Domingo'}

    # 1. Obtener Horarios Asignados
    horarios_queryset = HorarioDocente.objects.filter(
        docente=docente
    ).select_related('bloque', 'materia', 'curso').order_by('dia_semana', 'bloque__numero')

    # Agrupar horarios por día de la semana
    horarios_por_dia = {}
    for h in horarios_queryset:
        dia_nombre = nombre_dias.get(h.dia_semana, f'Día {h.dia_semana}')
        if dia_nombre not in horarios_por_dia:
            horarios_por_dia[dia_nombre] = []
        horarios_por_dia[dia_nombre].append(h)

    # 2. Obtener Licencias Solicitadas por el docente
    licencias = SolicitudLicencia.objects.filter(
        docente=docente
    ).select_related('tipo_licencia').prefetch_related('bloques_afectados').order_by('-fecha_solicitud')

    contexto = {
        'docente': docente,
        'horarios_por_dia': horarios_por_dia,
        'tiene_horarios': horarios_queryset.exists(),
        'licencias': licencias,
        'perfil_actual': 'docente'
    }
    return render(request, 'licencias/dashboard_docente.html', contexto)

# ------------------------------------------------------------
# ---- Vistas para registrar, editar y eliminar inasistencias
# ------------------------------------------------------------
@login_required
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


@login_required
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


@login_required
def eliminar_inasistencia(request, licencia_id):
    licencia = get_object_or_404(SolicitudLicencia, id=licencia_id)
    fecha_redireccion = licencia.fecha_solicitud

    if request.method == 'POST':
        licencia.delete()
        return redirect(f"/?fecha={fecha_redireccion}")

    return render(request, 'licencias/confirmar_eliminar.html', {'licencia': licencia})

@login_required
def asignar_cobertura(request, licencia_id, horario_id):
    licencia = get_object_or_404(SolicitudLicencia, id=licencia_id)
    horario = get_object_or_404(HorarioDocente, id=horario_id)
    
    fecha_str = request.GET.get('fecha', str(licencia.fecha_solicitud))
    fecha_cobertura = datetime.strptime(fecha_str, '%Y-%m-%d').date()

    # Buscar co-docentes presentes en ese mismo bloque/materia
    co_docentes = HorarioDocente.objects.filter(
        bloque=horario.bloque,
        curso=horario.curso,
        materia=horario.materia,
        dia_semana=horario.dia_semana
    ).exclude(docente=licencia.docente).select_related('docente__user')

    # Obtener o instanciar la suplencia existente
    suplencia = Suplencia.objects.filter(
        licencia=licencia,
        horario=horario,
        fecha=fecha_cobertura
    ).first()

    if request.method == 'POST':
        form = SuplenciaForm(request.POST, instance=suplencia)
        if form.is_valid():
            cobertura = form.save(commit=False)
            cobertura.licencia = licencia
            cobertura.horario = horario
            cobertura.fecha = fecha_cobertura
            
            # Si eligió absorción por pareja o Jefe de Lab, no requiere docente suplente externo
            if cobertura.tipo_cobertura in ['ABSORCION', 'JEFE_LAB']:
                cobertura.docente_suplente = None
                
            cobertura.save()
            messages.success(request, "Cobertura / Absorción registrada correctamente.")
            return redirect('dashboard_regencia')
    else:
        # Valores por defecto inteligentes
        initial_data = {}
        if horario.materia.tipo_modalidad == 'PAREJA' and co_docentes.exists():
            initial_data['tipo_cobertura'] = 'ABSORCION'
        elif horario.rol == 'TITULAR' and co_docentes.filter(rol='JEFE_LAB').exists():
            initial_data['tipo_cobertura'] = 'JEFE_LAB'
            
        form = SuplenciaForm(instance=suplencia, initial=initial_data)

    contexto = {
        'form': form,
        'licencia': licencia,
        'horario': horario,
        'co_docentes': co_docentes,
        'fecha_cobertura': fecha_cobertura
    }
    return render(request, 'licencias/asignar_cobertura.html', contexto)

# --------------------------------------------------