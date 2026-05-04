from urllib import request

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from . import models
import openpyxl
import pandas as pd

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











































# ===========================================================
#                                VISTAS EMPRESAS
# ===========================================================

def dashboard(request):
    return render(request, "3_Empresa/dashboard.html")










































# ===========================================================
#                                VISTAS COLEGIOS
# ===========================================================

def administracion(request):
    return render(request, "4_Colegio/administracion.html")

def moderacionPerfil(request):
    return render(request, "4_Colegio/moderacionPerfil.html")

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