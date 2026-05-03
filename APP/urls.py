from django.urls import path, include
from django.conf import settings
from . import views

urlpatterns = [

    #Login y Logout
    path('', views.login, name='login'), 
    path('logout/', views.logout_function, name='logout'),

    #Vistas Estudiante
    path('student/', views.student, name='student'), #student
    path('notificaciones/', views.notificaciones_e, name='notificaciones_e'),
    path('practicas/', views.practicas_e, name='practicas_e'),
    path('empresas/', views.empresas_e, name='empresas_e'),
    path('tareas/', views.tareas_e, name='tareas_e'),
    path('conexiones/', views.conexiones_e, name='conexiones_e'),


    #Vistas Colegio
    path('school/', views.school, name='school'), #school
    path('administracion/', views.administracion, name='administracion'), #administracion
    path('moderacion-perfil/', views.moderacionPerfil, name='moderacionPerfil'), #moderacionPerfil
    path('cargar-excel/', views.cargarPerfiles_excel, name='cargarPerfiles_excel'), #cargar perfiles con excel

    #Vistas Empresa
    path('business/', views.business, name='business'), #business
    path('dashboard/', views.dashboard, name='dashboard'), #dashboard

    #Funciones generales
    path('post/', views.crear_post, name='crear_post'),


    path('testalert/', views.testalert, name='testalert')
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path("__debug__/", include(debug_toolbar.urls)),
    ] + urlpatterns