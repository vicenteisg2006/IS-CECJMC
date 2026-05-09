from django.contrib.auth import authenticate, login as auth_login, logout, update_session_auth_hash
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.db.models import Q, Count, Case, When
from django.template.loader import get_template
from django.contrib.staticfiles import finders
from django.contrib import messages
from django.conf import settings
from functools import wraps
# from urllib import request
from xhtml2pdf import pisa
from datetime import date
import pandas as pd
from . import models
import openpyxl
import json
import random
import string
import csv
import os

# ===========================================================
#                                MEDIDAS DE SEGURIDAD
# ===========================================================


def perfil_requerido(perfil_permitido):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Obtenemos el nombre del perfil desde el modelo TipoPerfil
            rol_actual = request.user.tipo_perfil.lower() if request.user.tipo_perfil else ""
            
            if rol_actual == perfil_permitido.lower():
                return view_func(request, *args, **kwargs)
            
            messages.error(request, f"Acceso denegado. Esta zona es solo para {perfil_permitido}.")
            return redirect('ver_perfil')
        return _wrapped_view
    return decorator



# ===========================================================
#                                 LOGIN Y LOGOUT
# ===========================================================

def login(request):
    if request.method == "POST":
        username = request.POST.get("username").strip()
        password = request.POST.get("password").strip()

        user = authenticate(request, username=username, password=password)

        if user is not None:
            auth_login(request, user)

            try:
                tipo = user.tipo_perfil.lower() if user.tipo_perfil else ""

                if tipo == "alumno" or tipo == "estudiante":
                    return redirect("student")

                elif tipo == "colegio":
                    return redirect("school")
                
                elif tipo == "empresa":
                    return redirect("business")
                
                else:
                    return HttpResponse("Tipo de usuario no reconocido.")
                
            except Exception as e:
                return HttpResponse(f"Error al determinar el tipo de usuario: {str(e)}")
            
        else:
            error_msg = "Credenciales incorrectas. Por favor, inténtalo de nuevo."
            return render(request, "1_Login/login.html", {"error": error_msg})
        
    return render(request, "1_Login/login.html")

def logout_function(request):
    logout(request)
    return redirect('login')
































# ===========================================================
#                              VISTAS ESTUDIANTES
# ===========================================================

@login_required 
@perfil_requerido('estudiante')
def student(request):
    post = models.Post.objects.all().order_by('-fecha_publicacion').select_related('usuario')
    return render(request, "2_Estudiante/student.html", 
                  {
                    "posts": post
                  })

@login_required
@perfil_requerido('estudiante')
def notificaciones_e(request):
    notificaciones = models.Notificacion.objects.filter(
        receptor=request.user
    ).order_by('-fecha_creacion').select_related('actor')
    
    notificaciones_no_leidas = notificaciones.filter(leido=False)
    if notificaciones_no_leidas.exists():
        notificaciones_no_leidas.update(leido=True)
    
    return render(request, "2_Estudiante/notificaciones.html", {"notificaciones": notificaciones})

@login_required
@perfil_requerido('estudiante')
def practicas_e(request):
    alumno = request.user
    
    if request.method == 'POST':
        oferta_id = request.POST.get('oferta_id')
        oferta = get_object_or_404(models.OfertaLaboral, id=oferta_id)
        
        ya_postulo = models.Postulacion.objects.filter(usuario=alumno, oferta_laboral=oferta).exists()
        
        if ya_postulo:
            messages.warning(request, "Ya enviaste una solicitud para esta oferta.")
        else:
            models.Postulacion.objects.create(
                usuario=alumno,
                oferta_laboral=oferta,
                estado_solicitud=models.EstadoSolicitud.PENDIENTE
            )
            messages.success(request, f"¡Postulación enviada exitosamente a {oferta.empresa.first_name}!")
        return redirect('practicas_e')

    ofertas_disponibles = models.OfertaLaboral.objects.filter(
        colegio=alumno.centro_educacional,
        estado_verificacion=models.EstadoVerificacion.APROBADO,
        estado_oferta=models.EstadoOferta.ACTIVA 
    ).order_by('-fecha_publicacion')

    mis_postulaciones = models.Postulacion.objects.filter(usuario=alumno).values_list('oferta_laboral_id', flat=True)

    context = {
        'ofertas': ofertas_disponibles,
        'mis_postulaciones': list(mis_postulaciones)
    }
    
    return render(request, "2_Estudiante/practicas.html", context)

@login_required
@perfil_requerido('estudiante')
def empresas_e(request):
    mi_colegio = request.user.centro_educacional
    
    empresas_vinculadas = models.Usuario.objects.filter(
        tipo_perfil=models.TipoPerfil.EMPRESA,
        colegios_vinculados=mi_colegio
    ).distinct()
    
    return render(request, "2_Estudiante/empresas.html", {"empresas": empresas_vinculadas})

@login_required
@perfil_requerido('estudiante')
def tareas_e(request):
    materiales = models.ContenidoEducativo.objects.filter(
        colegio=request.user.centro_educacional
    ).order_by('-fecha_subida').prefetch_related('multimedia')
    
    return render(request, "2_Estudiante/tareas.html", {"materiales": materiales})

@login_required
@perfil_requerido('estudiante')
def conexiones_e(request):
    usuario = request.user
    siguiendo = models.Conexion.objects.filter(
        solicitante=usuario, 
        estado_solicitud=models.EstadoSolicitud.ACEPTADA
    ).select_related('receptor')

    seguidores = models.Conexion.objects.filter(
        receptor=usuario, 
        estado_solicitud=models.EstadoSolicitud.ACEPTADA
    ).select_related('solicitante')

    return render(request, "2_Estudiante/conexiones.html", {
        "siguiendo": siguiendo,
        "seguidores": seguidores
    })

@login_required
@perfil_requerido('estudiante')
def mis_postulaciones_e(request):
    mis_solicitudes = models.Postulacion.objects.filter(
        usuario=request.user
    ).select_related('oferta_laboral', 'oferta_laboral__empresa').order_by('-fecha_postulacion')
    
    return render(request, "2_Estudiante/mis_postulaciones.html", {"postulaciones": mis_solicitudes})

@login_required
@perfil_requerido('estudiante')
def descargar_cv_e(request):
    u = request.user
    
    especialidad = models.CompetenciaEstudiante.objects.filter(
        estudiante=u, 
        estado_verificacion=models.EstadoVerificacion.APROBADO,
        competencia__tipo_competencia=models.TipoCompetencia.ESPECIALIDAD
    ).first()

    experiencias = models.ExperienciaLaboral.objects.filter(
        usuario=u,
        estado_verificacion=models.EstadoVerificacion.APROBADO
    ).order_by('-fecha_inicio')

    habilidades = models.HabilidadUsuario.objects.filter(
        usuario=u,
        estado_verificacion=models.EstadoVerificacion.APROBADO
    )

    context = {
        'u': u,
        'especialidad': especialidad.competencia if especialidad else None,
        'experiencias': experiencias,
        'habilidades': habilidades,
        'hoy': date.today(),
    }
    
    template_path = '2_Estudiante/cv_template.html'
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="CV_{u.first_name}_{u.last_name}.pdf"'
    
    template = get_template(template_path)
    html = template.render(context)
    pisa_status = pisa.CreatePDF(html, dest=response, link_callback=link_callback)
    
    return response

@login_required
@perfil_requerido('estudiante')
def ver_ofertas_empresa(request, empresa_id):
    empresa = get_object_or_404(models.Usuario, id=empresa_id, tipo_perfil='empresa')
    
    ofertas = models.OfertaLaboral.objects.filter(empresa=empresa, estado='activa')
    
    return render(request, '2_Estudiante/detalle_empresa.html', {
        'empresa': empresa,
        'ofertas': ofertas
    })
#











































# ===========================================================
#                                VISTAS EMPRESAS
# ===========================================================

@login_required
@perfil_requerido('empresa')
def business(request):
    post = models.Post.objects.all().order_by('-fecha_publicacion').select_related('usuario')
    return render(request, "3_Empresa/business.html", 
                  {
                    "posts": post
                  })

@login_required
@perfil_requerido('empresa')
def dashboard(request):
    empresa = request.user
    
    colegios_vinculados = empresa.colegios_vinculados.all()
    
    ultimas_ofertas = models.OfertaLaboral.objects.filter(
        empresa=empresa, 
        es_practica=True
    ).order_by('-fecha_publicacion')[:5]

    context = {
        'colegios': colegios_vinculados,
        'ofertas': ultimas_ofertas,
    }
    
    return render(request, "3_Empresa/dashboard.html", context)
#
@login_required
@perfil_requerido('empresa')
def publicar_practica(request):
    if request.method == 'POST':
        empresa_actual = request.user
        
        puesto = request.POST.get('puesto_trabajo')
        detalle = request.POST.get('detalle')
        modalidad = request.POST.get('modalidad')
        ubicacion = request.POST.get('ubicacion')
        colegio_id = request.POST.get('colegio_destino')
        
        tipo_oferta = request.POST.get('tipo_oferta')
        es_practica_booleano = True if tipo_oferta == 'practica' else False
        
        sueldo_input = request.POST.get('sueldo')
        sueldo_final = sueldo_input if sueldo_input else None 
        
        colegio_destino = get_object_or_404(models.CentroEducacional, id=colegio_id)
        
        if colegio_destino in empresa_actual.colegios_vinculados.all():
            
            models.OfertaLaboral.objects.create(
                puesto_trabajo=puesto,
                empresa=empresa_actual,
                colegio=colegio_destino,
                es_practica=es_practica_booleano, 
                sueldo=sueldo_final,           
                detalle=detalle,
                modalidad=modalidad,
                ubicacion=ubicacion,
                fecha_expiracion=pd.Timestamp.now() + pd.Timedelta(days=30),
                estado_oferta=models.EstadoOferta.ACTIVA,
                estado_verificacion=models.EstadoVerificacion.PENDIENTE 
            )
            
            tipo_texto = "Práctica" if es_practica_booleano else "Oferta Laboral"
            messages.success(request, f'¡{tipo_texto} enviada a {colegio_destino.nombre} para su verificación!')
        else:
            messages.error(request, 'No tienes un convenio activo con este establecimiento.')
            
    return redirect('dashboard')

@login_required
@perfil_requerido('empresa')
def historial_ofertas(request):
    empresa_actual = request.user
    
    ofertas = models.OfertaLaboral.objects.filter(
        empresa=empresa_actual
    ).order_by('-fecha_publicacion')
    
    return render(request, '3_Empresa/historialOfertas.html', {'ofertas': ofertas})

@login_required
@perfil_requerido('empresa')
def revisar_postulantes(request):
    empresa_actual = request.user
    postulaciones = models.Postulacion.objects.filter(
        oferta_laboral__empresa=empresa_actual
    ).select_related('usuario', 'oferta_laboral', 'usuario__centro_educacional').order_by('-fecha_postulacion')
    
    return render(request, '3_Empresa/revisarPostulantes.html', {'postulaciones': postulaciones})

@login_required
@perfil_requerido('empresa')
def mis_colegios(request):
    colegios = request.user.colegios_vinculados.all()
    return render(request, '3_Empresa/misColegios.html', {'colegios': colegios})

@login_required
@perfil_requerido('empresa')
def explorar_instituciones(request):
    mis_vinculos = request.user.colegios_vinculados.all()
    colegios_disponibles = models.CentroEducacional.objects.exclude(id__in=mis_vinculos)
    
    query = request.GET.get('q', '')
    if query:
        colegios_disponibles = colegios_disponibles.filter(
            Q(nombre__icontains=query) | Q(direccion__icontains=query)
        )
        
    return render(request, '3_Empresa/explorarColegios.html', {
        'colegios': colegios_disponibles,
        'query': query
    })

@login_required
@perfil_requerido('empresa')
def entrevistas_agendadas(request):
    entrevistas = models.Postulacion.objects.filter(
        oferta_laboral__empresa=request.user,
        estado_solicitud='aceptada'
    ).select_related('usuario', 'oferta_laboral')
    
    return render(request, '3_Empresa/entrevistas.html', {'entrevistas': entrevistas})

@login_required
@perfil_requerido('empresa')
def cambiar_estado_postulacion(request, postulacion_id, nuevo_estado):
    if request.method == 'POST':
        postulacion = get_object_or_404(models.Postulacion, id=postulacion_id, oferta_laboral__empresa=request.user)
        
        if nuevo_estado in [models.EstadoSolicitud.ACEPTADA, models.EstadoSolicitud.RECHAZADA]:
            postulacion.estado_solicitud = nuevo_estado
            postulacion.save()
            
            nombre_alumno = f"{postulacion.usuario.first_name} {postulacion.usuario.last_name}"
            
            if nuevo_estado == models.EstadoSolicitud.ACEPTADA:
                messages.success(request, f'¡Has aceptado a {nombre_alumno}! Ya puedes contactarlo para la entrevista.')
                mensaje_notificacion = "ha aceptado tu postulación para la práctica."
            else:
                messages.warning(request, f'Has rechazado la solicitud de {nombre_alumno}.')
                mensaje_notificacion = "ha declinado tu postulación en esta ocasión."
            
    return redirect('revisar_postulantes')






























# ===========================================================
#                                VISTAS COLEGIOS
# ===========================================================

@login_required
@perfil_requerido('colegio')
def school(request):
    post = models.Post.objects.all().order_by('-fecha_publicacion').select_related('usuario')
    return render(request, "4_Colegio/school.html", 
                  {
                    "posts": post
                  })

@login_required
@perfil_requerido('colegio')
def administracion(request):
    return render(request, "4_Colegio/administracion.html")

@login_required
@perfil_requerido('colegio')
def moderacionPerfil(request):
    mi_colegio = request.user.centro_educacional
    
    usuarios_busqueda = models.Usuario.objects.filter(centro_educacional=mi_colegio).exclude(id=request.user.id)
    
    query = request.GET.get('q', '')
    if query:
        usuarios_busqueda = usuarios_busqueda.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(username__icontains=query)
        )
        
    context = {
        'usuarios_busqueda': usuarios_busqueda,
        'query': query,  
    }
    
    return render(request, '4_Colegio/moderacionPerfil.html', context)

@login_required
@perfil_requerido('colegio')
def cargar_estudiantes_excel(request):
    if request.method == "POST" and request.FILES.get("archivo_excel"):
        archivo = request.FILES["archivo_excel"]
        
        mi_colegio = request.user.centro_educacional
        
        if not mi_colegio:
            messages.error(request, "Tu cuenta no tiene un Centro Educacional asociado para vincular alumnos.")
            return redirect('moderacionPerfil')

        try:
            df = pd.read_excel(archivo)
            estudiantes_creados = 0
            
            for _, row in df.iterrows():
                user = models.Usuario.objects.create_user(
                    username=str(row['USUARIO']),
                    email=row['EMAIL'],
                    password=str(row['CONTRASEÑA']), 
                    first_name=row['NOMBRE'],
                    last_name=row['APELLIDO']
                )
                user.tipo_perfil = models.TipoPerfil.ESTUDIANTE
                user.centro_educacional = mi_colegio
                
                if 'FECHA_NACIMIENTO' in row:
                    user.fecha_nacimiento = row['FECHA_NACIMIENTO']

                nombre_curso = str(row['CURSO'])
                curso_obj = models.Curso.objects.filter(
                    nombre__iexact=nombre_curso, 
                    centro_educacional=mi_colegio
                ).first()
                
                if curso_obj:
                    user.curso = curso_obj

                user.save()
                estudiantes_creados += 1
                
            messages.success(request, f"Se cargaron {estudiantes_creados} estudiantes exitosamente en {mi_colegio.nombre}.")
        except Exception as e:
            messages.error(request, f"Error durante la carga: {str(e)}")
            
    return redirect('moderacionPerfil')

@login_required
@perfil_requerido('colegio')
@login_required
@perfil_requerido('colegio')
def cargar_empresas_excel(request):
    if request.method == "POST" and request.FILES.get("archivo_excel"):
        archivo = request.FILES["archivo_excel"]

        mi_colegio = request.user.centro_educacional
        
        try:
            df = pd.read_excel(archivo)
            empresas_creadas = 0
            
            for _, row in df.iterrows():
                user = models.Usuario.objects.create_user(
                    username=str(row['USUARIO']),
                    email=row['EMAIL'],
                    password=str(row['CONTRASEÑA']),
                    first_name=row['NOMBRE'],
                    tipo_perfil=models.TipoPerfil.EMPRESA 
                )
                
                if mi_colegio:
                    user.colegios_vinculados.add(mi_colegio)
                
                empresas_creadas += 1
                
            messages.success(request, f"Se cargaron {empresas_creadas} empresas y se generaron sus convenios automáticamente.")
        except Exception as e:
            messages.error(request, f"Error en carga de empresas: {str(e)}")
            
    return redirect('moderacionPerfil')

@login_required
@perfil_requerido('colegio')
def suspender_usuario(request, user_id):
    if request.method == 'POST':
        # Buscamos al usuario que intentan suspender
        usuario_objetivo = get_object_or_404(models.Usuario, id=user_id)
        
        # SEGURIDAD CRÍTICA: ¿Pertenece al mismo colegio que quien hace la petición?
        if usuario_objetivo.centro_educacional == request.user.centro_educacional:
            
            # Alternamos el estado activo (Soft Delete o Restore)
            if usuario_objetivo.is_active:
                usuario_objetivo.is_active = False
                messages.warning(request, f'La cuenta de {usuario_objetivo.first_name} ha sido suspendida.')
            else:
                usuario_objetivo.is_active = True
                messages.success(request, f'La cuenta de {usuario_objetivo.first_name} ha sido reactivada.')
            
            usuario_objetivo.save()
        else:
            # Intentó hackear o modificar alguien de otro colegio
            messages.error(request, 'No tienes permisos para modificar a este usuario.')
            
    return redirect('moderacionPerfil')

@login_required
@perfil_requerido('colegio')
def moderacionContenido(request):

    mi_colegio = request.user.centro_educacional
    
    posts_comunidad = models.Post.objects.filter(
        usuario__centro_educacional=mi_colegio
    ).order_by('-fecha_publicacion')

    context = {
        'posts': posts_comunidad
    }
    
    return render(request, '4_Colegio/moderacionContenido.html', context)

@login_required
@perfil_requerido('colegio')
def eliminar_post_colegio(request, post_id):
    if request.method == 'POST':
        post = get_object_or_404(models.Post, id=post_id)
        
        if post.usuario.centro_educacional == request.user.centro_educacional:
            post.delete()
            messages.success(request, 'La publicación ha sido eliminada por moderación.')
        else:
            messages.error(request, 'Intento de borrado no autorizado.')
            
    return redirect('moderacionContenido')

@login_required
@perfil_requerido('colegio')
def gestionarAlumnos(request):

    mi_colegio = request.user.centro_educacional
    
    alumnos = models.Usuario.objects.filter(
        centro_educacional=mi_colegio,
        tipo_perfil__iexact='estudiante'
    ).order_by('last_name')

    query = request.GET.get('q', '') 
    if query:
        alumnos = alumnos.filter(
            Q(first_name__icontains=query) | 
            Q(last_name__icontains=query) | 
            Q(email__icontains=query) |
            Q(username__icontains=query)
        )
    cursos_disponibles = models.Curso.objects.filter(centro_educacional=mi_colegio)
    especialidades = request.user.centro_educacional.especialidades.all()

    context = {
        'alumnos': alumnos,
        'cursos': cursos_disponibles,
        'especialidades_del_colegio': especialidades,
        'query': query 
    }
    return render(request, '4_Colegio/gestionarAlumnos.html', context)

@login_required
@perfil_requerido('colegio')
def actualizar_curso_alumno(request, user_id):
    if request.method == 'POST':
        alumno = get_object_or_404(models.Usuario, id=user_id)
        
        if alumno.centro_educacional == request.user.centro_educacional:
            curso_id = request.POST.get('nuevo_curso')
            
            if curso_id:
                nuevo_curso_obj = get_object_or_404(models.Curso, id=curso_id)
                alumno.curso = nuevo_curso_obj
                alumno.save()
                messages.success(request, f'Curso de {alumno.first_name} actualizado a {nuevo_curso_obj.nombre}.')
        else:
            messages.error(request, 'No autorizado.')
            
    return redirect('gestionarAlumnos')

@login_required
@perfil_requerido('colegio')
def crear_curso(request):
    if request.method == 'POST':
        nombre_curso = request.POST.get('nombre_curso')
        mi_colegio = request.user.centro_educacional

        if nombre_curso:
            curso_existe = models.Curso.objects.filter(
                nombre__iexact=nombre_curso, 
                centro_educacional=mi_colegio
            ).exists()
            
            if curso_existe:
                messages.warning(request, f'El curso "{nombre_curso}" ya existe en tu institución.')
            else:
                models.Curso.objects.create(
                    nombre=nombre_curso,
                    centro_educacional=mi_colegio
                )
                messages.success(request, f'Curso "{nombre_curso}" creado exitosamente.')
        else:
            messages.error(request, 'El nombre del curso no puede estar vacío.')

    return redirect('gestionarAlumnos')

@login_required
@perfil_requerido('colegio')
def restablecerClaves(request):
    mi_colegio = request.user.centro_educacional
    alumnos = models.Usuario.objects.filter(
        centro_educacional=mi_colegio,
        tipo_perfil__iexact='estudiante'
    ).order_by('last_name')

    query = request.GET.get('q', '')
    if query:
        alumnos = alumnos.filter(
            Q(first_name__icontains=query) | Q(last_name__icontains=query) | Q(email__icontains=query)
        )

    context = {
        'alumnos': alumnos,
        'query': query
    }
    return render(request, '4_Colegio/restablecerClaves.html', context)

@login_required
@perfil_requerido('colegio')
def generar_clave_temporal(request, user_id):
    if request.method == 'POST':
        alumno = get_object_or_404(models.Usuario, id=user_id)
        
        if alumno.centro_educacional == request.user.centro_educacional:
            caracteres = string.ascii_letters + string.digits
            nueva_clave = ''.join(random.choice(caracteres) for i in range(8))
            
            alumno.set_password(nueva_clave)
            alumno.save()
            
            messages.success(request, f'✅ ¡Éxito! La nueva contraseña temporal para {alumno.first_name} {alumno.last_name} es: {nueva_clave}')
        else:
            messages.error(request, 'No tienes permisos para modificar a este usuario.')
            
    return redirect('restablecerClaves')

@login_required
@perfil_requerido('colegio')
def gestionarEmpresas(request):
    mi_colegio = request.user.centro_educacional
    
    empresas = models.Usuario.objects.filter(
        colegios_vinculados=mi_colegio,
        tipo_perfil__iexact='empresa'
    ).order_by('first_name')

    query = request.GET.get('q', '')
    if query:
        empresas = empresas.filter(
            Q(first_name__icontains=query) |
            Q(email__icontains=query) |
            Q(username__icontains=query)
        )

    empresas_disponibles = models.Usuario.objects.filter(
        tipo_perfil__iexact='empresa'
    ).exclude(colegios_vinculados=mi_colegio).order_by('first_name')

    context = {
        'empresas': empresas,
        'empresas_disponibles': empresas_disponibles, # Lo enviamos al HTML
        'query': query
    }
    return render(request, '4_Colegio/gestionarEmpresas.html', context)

@login_required
@perfil_requerido('colegio')
def vincular_empresa(request):
    if request.method == 'POST':

        mi_colegio = request.user.centro_educacional
        empresa_id = request.POST.get('empresa_id') 

        if empresa_id:
            # Buscamos la empresa exacta por su ID
            empresa_seleccionada = get_object_or_404(models.Usuario, id=empresa_id, tipo_perfil__iexact='empresa')
            
            # La vinculamos
            empresa_seleccionada.colegios_vinculados.add(mi_colegio)
            messages.success(request, f'¡Convenio establecido con {empresa_seleccionada.first_name}!')
        else:
            messages.error(request, 'No se seleccionó ninguna empresa.')

    return redirect('gestionarEmpresas')

@login_required
@perfil_requerido('colegio')
def aprobarPracticas(request):
    mi_colegio = request.user.centro_educacional
    ofertas = models.OfertaLaboral.objects.filter(colegio=mi_colegio, es_practica=True).order_by(
        Case(
            When(estado_verificacion=models.EstadoVerificacion.PENDIENTE, then=0),
            When(estado_verificacion=models.EstadoVerificacion.APROBADO, then=1),
            default=2
        ),
        '-fecha_publicacion' 
    )

    return render(request, '4_Colegio/aprobarPracticas.html', {'ofertas': ofertas})

@login_required
@perfil_requerido('colegio')
def cambiar_estado_oferta(request, oferta_id, nuevo_estado):
    if request.method == 'POST':
        oferta = get_object_or_404(models.OfertaLaboral, id=oferta_id, colegio=request.user.centro_educacional)
        
        if nuevo_estado in [models.EstadoVerificacion.APROBADO, models.EstadoVerificacion.RECHAZADO]:
            oferta.estado_verificacion = nuevo_estado 
            oferta.save()
            messages.success(request, f'La oferta "{oferta.puesto_trabajo}" ha sido marcada como {nuevo_estado.lower()}.')
            
    return redirect('aprobarPracticas')

@login_required
@perfil_requerido('colegio')
def metricasEmpresas(request):
    mi_colegio = request.user.centro_educacional
    
    total_empresas = models.Usuario.objects.filter(colegios_vinculados=mi_colegio, tipo_perfil__iexact='empresa').count()
    total_ofertas = models.OfertaLaboral.objects.filter(colegio=mi_colegio).count()
    ofertas_aprobadas = models.OfertaLaboral.objects.filter(colegio=mi_colegio, estado_verificacion=models.EstadoVerificacion.APROBADO).count()

    context = {
        'total_empresas': total_empresas,
        'total_ofertas': total_ofertas,
        'ofertas_aprobadas': ofertas_aprobadas,
    }
    return render(request, '4_Colegio/metricasEmpresas.html', context)

@login_required
@perfil_requerido('colegio')
def seguimientoPracticas(request):
    mi_colegio = request.user.centro_educacional
    practicas = models.ExperienciaLaboral.objects.filter(
        usuario__centro_educacional=mi_colegio
    ).select_related('usuario', 'empresa_registrada').order_by('-fecha_inicio')
    
    return render(request, '4_Colegio/seguimientoPracticas.html', {'practicas': practicas})

@login_required
@perfil_requerido('colegio')
def redEgresados(request):
    mi_colegio = request.user.centro_educacional
    egresados = models.Usuario.objects.filter(
        centro_educacional=mi_colegio,
        tipo_perfil__iexact='estudiante',
        curso__isnull=True
    ).order_by('last_name')
    
    return render(request, '4_Colegio/redEgresados.html', {'egresados': egresados})

@login_required
@perfil_requerido('colegio')
def gestionarEspecialidades(request):
    colegio = request.user.centro_educacional
    todas_especialidades = models.Competencia.objects.filter(
        tipo_competencia=models.TipoCompetencia.ESPECIALIDAD
    ).order_by('competencia')
    
    mias = colegio.especialidades.all()

    if request.method == 'POST':
        # ACCIÓN A: Crear una nueva especialidad
        if 'nueva_especialidad' in request.POST:
            nombre = request.POST.get('nueva_especialidad').strip()
            if nombre:
                especialidad, created = models.Competencia.objects.get_or_create(
                    competencia__iexact=nombre,
                    defaults={
                        'competencia': nombre, 
                        'tipo_competencia': models.TipoCompetencia.ESPECIALIDAD
                    }
                )
                
                colegio.especialidades.add(especialidad)
                messages.success(request, f"Especialidad '{nombre}' añadida correctamente.")
            return redirect('gestionarEspecialidades')

        ids_seleccionadas = request.POST.getlist('especialidades')
        colegio.especialidades.set(ids_seleccionadas)
        messages.success(request, "Lista de especialidades actualizada.")
        return redirect('gestionarEspecialidades')

    return render(request, '4_Colegio/gestionarEspecialidades.html', {
        'todas': todas_especialidades,
        'mias': mias
    })

@login_required
@perfil_requerido('colegio')
def gestionarContenidoEducativo(request):
    mi_colegio = request.user.centro_educacional
    
    if request.method == 'POST':
        # Handle JSON (from new s3direct flow)
        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, Exception):
            data = request.POST

        titulo = data.get('titulo')
        descripcion = data.get('descripcion')

        if not titulo or not descripcion:
            return JsonResponse({'ok': False, 'error': 'Faltan campos requeridos'}, status=400)

        contenido = models.ContenidoEducativo.objects.create(
            colegio=mi_colegio,
            titulo=titulo,
            descripcion=descripcion,
            # url_video removed — multimedia handled separately via S3
        )
        return JsonResponse({'ok': True, 'contenido_id': contenido.id})  # was post_id

    # GET
    contenidos = models.ContenidoEducativo.objects.filter(
        colegio=mi_colegio
    ).order_by('-fecha_subida').prefetch_related('multimedia')
    
    return render(request, '4_Colegio/gestionarContenido.html', {'contenidos': contenidos})

@login_required
@perfil_requerido('colegio')
def exportarDatosExcel(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="alumnos_rel_plus.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Nombre', 'Apellido', 'Email', 'Curso', 'Telefono'])
    
    alumnos = models.Usuario.objects.filter(centro_educacional=request.user.centro_educacional)
    for a in alumnos:
        writer.writerow([a.first_name, a.last_name, a.email, a.curso, a.telefono])
    
    return response

@login_required
@perfil_requerido('colegio')
def reporteEmpleabilidad(request):
    mi_colegio = request.user.centro_educacional
    
    egresados = models.Usuario.objects.filter(
        centro_educacional=mi_colegio,
        tipo_perfil__iexact='estudiante',
        curso__isnull=True
    )
    total_egresados = egresados.count()
    
    egresados_trabajando = egresados.filter(experiencias_como_estudiante__isnull=False).distinct().count()
    
    porcentaje = (egresados_trabajando * 100 // total_egresados) if total_egresados > 0 else 0

    context = {
        'total_egresados': total_egresados,
        'egresados_trabajando': egresados_trabajando,
        'porcentaje': porcentaje
    }
    return render(request, '4_Colegio/reporteEmpleabilidad.html', context)

@login_required
@perfil_requerido('colegio')
def asignar_especialidad_alumno(request, estudiante_id):
    estudiante = get_object_or_404(
        models.Usuario, 
        id=estudiante_id, 
        centro_educacional=request.user.centro_educacional,
        tipo_perfil=models.TipoPerfil.ESTUDIANTE
    )

    especialidades_disponibles = request.user.centro_educacional.especialidades.all()

    if request.method == 'POST':
        competencia_id = request.POST.get('especialidad_id')
        especialidad_seleccionada = get_object_or_404(models.Competencia, id=competencia_id)

        models.CompetenciaEstudiante.objects.update_or_create(
            estudiante=estudiante,
            competencia=especialidad_seleccionada,
            defaults={
                'estado_verificacion': models.EstadoVerificacion.APROBADO 
            }
        )

        messages.success(request, f'Se asignó la especialidad {especialidad_seleccionada.competencia} a {estudiante.first_name}.')
        return redirect('gestionarAlumnos') 

    return render(request, '3_Colegio/asignar_especialidad.html', {
        'estudiante': estudiante,
        'especialidades': especialidades_disponibles
    })





























# ===========================================================
#                             FUNCIONES GENERALES
# ===========================================================


@login_required
def crear_post(request):
    if request.method == "POST":
        texto = request.POST.get("contenido_post", "").strip()

        if texto:
            models.Post.objects.create(
                usuario=request.user, 
                mensaje=texto
                )
            messages.success(request, "Post creado exitosamente.")

        else:
            messages.error(request, "El contenido del post no puede estar vacío.")
    
    url_anterior = request.META.get('HTTP_REFERER', '/')
    return redirect(url_anterior)

@login_required
def toggle_like(request, post_id):
    post = get_object_or_404(models.Post, id=post_id)
    # Buscamos si ya existe el Like
    like_qs = models.Like.objects.filter(usuario=request.user, post=post)
    
    if like_qs.exists():
        like_qs.delete()
        liked = False
    else:
        models.Like.objects.create(usuario=request.user, post=post)
        liked = True    
    
    # Devolvemos el nuevo conteo de likes para actualizar el HTML
    return JsonResponse({
        'liked': liked,
        'count': post.likes.count()
    })

@login_required
def ver_perfil(request):
    return render(request, '0_Bases/miPerfil.html')

@login_required
def actualizar_perfil(request):
    if request.method == 'POST':
        user = request.user
        
        user.first_name = request.POST.get('first_name')
        user.telefono = request.POST.get('telefono')
        user.direccion = request.POST.get('direccion')

        nueva_foto = request.FILES.get('nueva_foto')
        if nueva_foto:
            user.avatar = nueva_foto 

        nuevo_apellido = request.POST.get('last_name')
        if nuevo_apellido is not None:
            user.last_name = nuevo_apellido
        
        user.bio = request.POST.get('bio')

        user.save()
        messages.success(request, "Perfil actualizado.")
    return redirect('ver_perfil')

@login_required
def cambiar_password(request):
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if not request.user.check_password(old_password):
            messages.error(request, 'La contraseña actual es incorrecta. Inténtalo de nuevo.')
            return redirect('ver_perfil')

        if new_password != confirm_password:
            messages.error(request, 'Las contraseñas nuevas no coinciden. Revisa bien.')
            return redirect('ver_perfil')

        request.user.set_password(new_password)
        request.user.save()

        update_session_auth_hash(request, request.user)
        
        messages.success(request, '¡Tu contraseña de REL+ ha sido actualizada con éxito!')
        
    return redirect('ver_perfil')

@login_required
def configurar_notificaciones(request):
    if request.method == 'POST':
        user = request.user
        
        user.notif_email = request.POST.get('notifEmail') == 'on'
        user.notif_mensajes = request.POST.get('notifMensajes') == 'on'
        user.notif_practicas = request.POST.get('notifPracticas') == 'on'
        
        user.save()
        messages.success(request, 'Tus preferencias de notificaciones han sido actualizadas.')
        
    return redirect('ver_perfil')

@login_required
def configurar_privacidad(request):
    if request.method == 'POST':
        request.user.visibilidad_perfil = request.POST.get('visibilidad')
        request.user.save()
        messages.success(request, 'Tu configuración de privacidad ha sido actualizada.')
    return redirect('ver_perfil')

@login_required
def descargar_datos_json(request):
    user = request.user
    
    datos = {
        "nombre": user.first_name,
        "apellido": user.last_name,
        "email": user.email,
        "telefono": user.telefono,
        "direccion": user.direccion,
        "tipo_perfil": user.get_tipo_perfil_display() if user.tipo_perfil else "No especificado",
        "centro_educacional": user.centro_educacional.nombre if user.centro_educacional else "No especificado",
        "fecha_registro": user.date_joined.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    response = JsonResponse(datos, json_dumps_params={'ensure_ascii': False, 'indent': 4})
    
    response['Content-Disposition'] = f'attachment; filename="mis_datos_relplus_{user.username}.json"'
    
    return response

@login_required
def link_callback(uri, rel):
    result = finders.find(uri)
    if result:
        if not isinstance(result, (list, tuple)):
            result = [result]
        result = list(os.path.realpath(path) for path in result)
        path = result[0]
    else:
        s_url = settings.STATIC_URL
        s_root = settings.STATIC_ROOT
        m_url = settings.MEDIA_URL
        m_root = settings.MEDIA_ROOT

        if uri.startswith(m_url):
            path = os.path.join(m_root, uri.replace(m_url, ""))
        elif uri.startswith(s_url):
            path = os.path.join(s_root, uri.replace(s_url, ""))
        else:
            return uri

    if not os.path.isfile(path):
        raise Exception('media URI must exist on disk')
    return path
    
#