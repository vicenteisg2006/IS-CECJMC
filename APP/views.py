from urllib import request
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from . import models
import openpyxl
import pandas as pd
from django.db.models import Q
import string
import random
import csv

# ===========================================================
#                                MEDIDAS DE SEGURIDAD
# ===========================================================

@login_required(login_url='/') 
def student(request):
    post = models.Post.objects.all().order_by('-fecha_publicacion').select_related('usuario')
    return render(request, "2_Estudiante/student.html", 
                  {
                    "posts": post
                  })

@login_required(login_url='/')
def school(request):
    post = models.Post.objects.all().order_by('-fecha_publicacion').select_related('usuario')
    return render(request, "4_Colegio/school.html", 
                  {
                    "posts": post
                  })

@login_required(login_url='/')
def business(request):
    post = models.Post.objects.all().order_by('-fecha_publicacion').select_related('usuario')
    return render(request, "3_Empresa/business.html", 
                  {
                    "posts": post
                  })




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
                tipo = user.tipo_perfil.tipo_perfil.lower() if user.tipo_perfil else ""

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

#






























# ===========================================================
#                              VISTAS ESTUDIANTES
# ===========================================================

def notificaciones_e(request):
    return render(request, "2_Estudiante/notificaciones.html")

def practicas_e(request):
    practicas = models.OfertaLaboral.objects.all()
    context = {'tatata':practicas}
    return render(request, "2_Estudiante/practicas.html", context)

def empresas_e(request):
    return render(request, "2_Estudiante/empresas.html")

def tareas_e(request):
    return render(request, "2_Estudiante/tareas.html")

def conexiones_e(request):
    return render(request, "2_Estudiante/conexiones.html")

#











































# ===========================================================
#                                VISTAS EMPRESAS
# ===========================================================

def dashboard(request):
    return render(request, "3_Empresa/dashboard.html")

#








































# ===========================================================
#                                VISTAS COLEGIOS
# ===========================================================

def administracion(request):
    return render(request, "4_Colegio/administracion.html")

@login_required
def moderacionPerfil(request):
    # 1. Filtro de Seguridad: Verificamos que sea una cuenta de colegio
    tipo_usuario = request.user.tipo_perfil.tipo_perfil.lower() if request.user.tipo_perfil else ''
    if tipo_usuario != 'colegio':
        messages.error(request, 'Acceso denegado. Solo administradores de colegios pueden ver esto.')
        return redirect('ver_perfil')

    # 2. Obtener el colegio del usuario actual
    mi_colegio = request.user.centro_educacional
    
    # 3. Base de la búsqueda: Todos los usuarios de ESTE colegio, excepto a sí mismo
    usuarios_busqueda = models.Usuario.objects.filter(centro_educacional=mi_colegio).exclude(id=request.user.id)
    
    # 4. Procesar la palabra escrita en el buscador (si existe)
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
        'query': query,  # Devolvemos el query para mantenerlo en el input del HTML
    }
    
    # Renderizamos apuntando a la carpeta 4_Colegio
    return render(request, '4_Colegio/moderacionPerfil.html', context)

def cargar_estudiantes_excel(request):
    if request.method == "POST" and request.FILES.get("archivo_excel"):
        archivo = request.FILES["archivo_excel"]
        try:
            df = pd.read_excel(archivo)

            perfil_estudiante = models.TipoPerfil.objects.get(tipo_perfil__iexact='ESTUDIANTE')
            
            for _, row in df.iterrows():

                user = models.Usuario.objects.create_user(
                    username=str(row['USUARIO']),
                    email=row['EMAIL'],
                    password=str(row['CONTRASEÑA']), 
                    first_name=row['NOMBRE'],
                    last_name=row['APELLIDO']
                )

                user.tipo_perfil = perfil_estudiante
                user.curso = row['CURSO']
                user.fecha_nacimiento = row['FECHA_NACIMIENTO']
                

                colegio = models.CentroEducacional.objects.get(nombre=row['CENTRO_EDUCACIONAL'])
                user.centro_educacional = colegio
                
                user.save()
                
            messages.success(request, f"Se cargaron {len(df)} estudiantes correctamente.")
        except Exception as e:
            messages.error(request, f"Error en carga de estudiantes: {str(e)}")
            
    return redirect('moderacionPerfil')

def cargar_empresas_excel(request):
    if request.method == "POST" and request.FILES.get("archivo_excel"):
        archivo = request.FILES["archivo_excel"]
        try:
            df = pd.read_excel(archivo)
            perfil_empresa = models.TipoPerfil.objects.get(tipo_perfil__iexact='EMPRESA')
            
            for _, row in df.iterrows():
                user = models.Usuario.objects.create_user(
                    username=str(row['USUARIO']),
                    email=row['EMAIL'],
                    password=str(row['CONTRASEÑA']),
                    first_name=row['NOMBRE'] # Para empresas solo usamos el primer nombre
                )
                user.tipo_perfil = perfil_empresa
                # Aquí no asignamos curso ni colegio según tu lógica de empresas
                user.save()
                
            messages.success(request, f"Se cargaron {len(df)} empresas correctamente.")
        except Exception as e:
            messages.error(request, f"Error en carga de empresas: {str(e)}")
            
    return redirect('moderacionPerfil')

@login_required
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
def moderacionContenido(request):
    tipo_usuario = request.user.tipo_perfil.tipo_perfil.lower() if request.user.tipo_perfil else ''
    if tipo_usuario != 'colegio':
        messages.error(request, 'Acceso denegado. Solo colegios pueden moderar contenido.')
        return redirect('ver_perfil')

    mi_colegio = request.user.centro_educacional
    
    posts_comunidad = models.Post.objects.filter(
        usuario__centro_educacional=mi_colegio
    ).order_by('-fecha_publicacion')

    context = {
        'posts': posts_comunidad
    }
    
    return render(request, '4_Colegio/moderacionContenido.html', context)

@login_required
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
def gestionarAlumnos(request):
    tipo_usuario = request.user.tipo_perfil.tipo_perfil.lower() if request.user.tipo_perfil else ''
    if tipo_usuario != 'colegio':
        messages.error(request, 'Acceso denegado.')
        return redirect('ver_perfil')

    mi_colegio = request.user.centro_educacional
    
    alumnos = models.Usuario.objects.filter(
        centro_educacional=mi_colegio,
        tipo_perfil__tipo_perfil__iexact='estudiante'
    ).order_by('last_name')

    query = request.GET.get('q', '') # Capturamos lo que el usuario escribió
    if query:
        alumnos = alumnos.filter(
            Q(first_name__icontains=query) | 
            Q(last_name__icontains=query) | 
            Q(email__icontains=query) |
            Q(username__icontains=query)
        )
    cursos_disponibles = models.Curso.objects.filter(centro_educacional=mi_colegio)

    context = {
        'alumnos': alumnos,
        'cursos': cursos_disponibles,
        'query': query 
    }
    return render(request, '4_Colegio/gestionarAlumnos.html', context)

@login_required
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
def crear_curso(request):
    if request.method == 'POST':
        tipo_usuario = request.user.tipo_perfil.tipo_perfil.lower() if request.user.tipo_perfil else ''
        if tipo_usuario != 'colegio':
            messages.error(request, 'Acceso denegado.')
            return redirect('ver_perfil')

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
def restablecerClaves(request):
    tipo_usuario = request.user.tipo_perfil.tipo_perfil.lower() if request.user.tipo_perfil else ''
    if tipo_usuario != 'colegio':
        messages.error(request, 'Acceso denegado.')
        return redirect('ver_perfil')

    mi_colegio = request.user.centro_educacional
    alumnos = models.Usuario.objects.filter(
        centro_educacional=mi_colegio,
        tipo_perfil__tipo_perfil__iexact='estudiante'
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
def gestionarEmpresas(request):
    tipo_usuario = request.user.tipo_perfil.tipo_perfil.lower() if request.user.tipo_perfil else ''
    if tipo_usuario != 'colegio':
        messages.error(request, 'Acceso denegado.')
        return redirect('ver_perfil')

    mi_colegio = request.user.centro_educacional
    
    empresas = models.Usuario.objects.filter(
        colegios_vinculados=mi_colegio,
        tipo_perfil__tipo_perfil__iexact='empresa'
    ).order_by('first_name')

    query = request.GET.get('q', '')
    if query:
        empresas = empresas.filter(
            Q(first_name__icontains=query) |
            Q(email__icontains=query) |
            Q(username__icontains=query)
        )

    empresas_disponibles = models.Usuario.objects.filter(
        tipo_perfil__tipo_perfil__iexact='empresa'
    ).exclude(colegios_vinculados=mi_colegio).order_by('first_name')

    context = {
        'empresas': empresas,
        'empresas_disponibles': empresas_disponibles, # Lo enviamos al HTML
        'query': query
    }
    return render(request, '4_Colegio/gestionarEmpresas.html', context)

@login_required
def vincular_empresa(request):
    if request.method == 'POST':
        tipo_usuario = request.user.tipo_perfil.tipo_perfil.lower() if request.user.tipo_perfil else ''
        if tipo_usuario != 'colegio':
            return redirect('ver_perfil')

        mi_colegio = request.user.centro_educacional
        empresa_id = request.POST.get('empresa_id') 

        if empresa_id:
            # Buscamos la empresa exacta por su ID
            empresa_seleccionada = get_object_or_404(models.Usuario, id=empresa_id, tipo_perfil__tipo_perfil__iexact='empresa')
            
            # La vinculamos
            empresa_seleccionada.colegios_vinculados.add(mi_colegio)
            messages.success(request, f'¡Convenio establecido con {empresa_seleccionada.first_name}!')
        else:
            messages.error(request, 'No se seleccionó ninguna empresa.')

    return redirect('gestionarEmpresas')

@login_required
def aprobarPracticas(request):
    tipo_usuario = request.user.tipo_perfil.tipo_perfil.lower() if request.user.tipo_perfil else ''
    if tipo_usuario != 'colegio':
        return redirect('ver_perfil')

    mi_colegio = request.user.centro_educacional
    
    # Traemos las ofertas enviadas a este colegio, ordenando las pendientes primero
    ofertas = models.OfertaPractica.objects.filter(colegio=mi_colegio).order_by(
        models.Case(
            models.When(estado='Pendiente', then=0),
            models.When(estado='Aprobada', then=1),
            default=2
        ),
        '-fecha_creacion'
    )

    return render(request, '4_Colegio/aprobarPracticas.html', {'ofertas': ofertas})

@login_required
def cambiar_estado_oferta(request, oferta_id, nuevo_estado):
    if request.method == 'POST':
        oferta = get_object_or_404(models.OfertaPractica, id=oferta_id, colegio=request.user.centro_educacional)
        if nuevo_estado in ['Aprobada', 'Rechazada']:
            oferta.estado = nuevo_estado
            oferta.save()
            messages.success(request, f'La oferta "{oferta.titulo}" ha sido {nuevo_estado.lower()}.')
    return redirect('aprobarPracticas')

@login_required
def metricasEmpresas(request):
    tipo_usuario = request.user.tipo_perfil.tipo_perfil.lower() if request.user.tipo_perfil else ''
    if tipo_usuario != 'colegio':
        return redirect('ver_perfil')

    mi_colegio = request.user.centro_educacional
    
    # Cálculos para el Dashboard
    total_empresas = models.Usuario.objects.filter(colegios_vinculados=mi_colegio, tipo_perfil__tipo_perfil__iexact='empresa').count()
    total_ofertas = models.OfertaPractica.objects.filter(colegio=mi_colegio).count()
    ofertas_aprobadas = models.OfertaPractica.objects.filter(colegio=mi_colegio, estado='Aprobada').count()
    cupos_totales = sum(oferta.cupos for oferta in models.OfertaPractica.objects.filter(colegio=mi_colegio, estado='Aprobada'))

    context = {
        'total_empresas': total_empresas,
        'total_ofertas': total_ofertas,
        'ofertas_aprobadas': ofertas_aprobadas,
        'cupos_totales': cupos_totales,
    }
    return render(request, '4_Colegio/metricasEmpresas.html', context)


@login_required
def seguimientoPracticas(request):
    mi_colegio = request.user.centro_educacional
    practicas = models.ExperienciaLaboral.objects.filter(
        usuario__centro_educacional=mi_colegio
    ).select_related('usuario', 'empresa_registrada').order_by('-fecha_inicio')
    
    return render(request, '4_Colegio/seguimientoPracticas.html', {'practicas': practicas})

@login_required
def redEgresados(request):
    mi_colegio = request.user.centro_educacional
    egresados = models.Usuario.objects.filter(
        centro_educacional=mi_colegio,
        tipo_perfil__tipo_perfil__iexact='estudiante',
        curso__isnull=True
    ).order_by('last_name')
    
    return render(request, '4_Colegio/redEgresados.html', {'egresados': egresados})

@login_required
def gestionarEspecialidades(request):
    mi_colegio = request.user.centro_educacional
    if request.method == 'POST':
        especialidades_ids = request.POST.getlist('especialidades')
        mi_colegio.especialidades.set(especialidades_ids)
        messages.success(request, "Especialidades actualizadas correctamente.")
        return redirect('gestionarEspecialidades')
    
    todas_especialidades = models.Competencia.objects.filter(tipo_competencia='ESP')
    mis_especialidades = mi_colegio.especialidades.all()
    
    return render(request, '4_Colegio/gestionarEspecialidades.html', {
        'todas': todas_especialidades,
        'mias': mis_especialidades
    })

@login_required
def gestionarContenidoEducativo(request):
    mi_colegio = request.user.centro_educacional
    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        descripcion = request.POST.get('descripcion')
        url = request.POST.get('url_video')
        models.ContenidoEducativo.objects.create(
            colegio=mi_colegio,
            titulo=titulo,
            descripcion=descripcion,
            url_video=url
        )
        messages.success(request, "Recurso educativo publicado para tus alumnos.")
        
    contenidos = models.ContenidoEducativo.objects.filter(colegio=mi_colegio).order_by('-fecha_subida')
    return render(request, '4_Colegio/gestionarContenido.html', {'contenidos': contenidos})

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
def reporteEmpleabilidad(request):
    tipo_usuario = request.user.tipo_perfil.tipo_perfil.lower() if request.user.tipo_perfil else ''
    if tipo_usuario != 'colegio':
        return redirect('ver_perfil')

    mi_colegio = request.user.centro_educacional
    
    egresados = models.Usuario.objects.filter(
        centro_educacional=mi_colegio,
        tipo_perfil__tipo_perfil__iexact='estudiante',
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







































# ===========================================================
#                             VISTAS DE PRUEBAS
# ===========================================================



def testalert(request):
    return render(request, "5_Alessandro/home.html")




















# ===========================================================
#                             FUNCIONES GENERALES
# ===========================================================


@login_required(login_url='/')
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
        "tipo_perfil": user.tipo_perfil.tipo_perfil if user.tipo_perfil else "No especificado",
        "centro_educacional": user.centro_educacional.nombre if user.centro_educacional else "No especificado",
        "fecha_registro": user.date_joined.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    response = JsonResponse(datos, json_dumps_params={'ensure_ascii': False, 'indent': 4})
    
    response['Content-Disposition'] = f'attachment; filename="mis_datos_relplus_{user.username}.json"'
    
    return response

#