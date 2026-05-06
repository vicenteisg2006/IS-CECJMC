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