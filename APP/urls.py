from django.conf.urls.static import static
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

    path('administracion/moderacion-perfil/', views.moderacionPerfil, name='moderacionPerfil'), #moderacionPerfil
    path('administracion/moderacion-perfil/cargar-excel-estudiantes/', views.cargar_estudiantes_excel, name='cargarPerfilesEstudiantes_excel'), #cargar perfiles con excel
    path('administracion/moderacion-perfil/cargar-excel-empresas/', views.cargar_empresas_excel, name='cargarPerfilesEmpresas_excel'), #cargar perfiles con excel
    path('administracion/moderacion-perfil/suspender-usuario/<int:user_id>/', views.suspender_usuario, name='suspender_usuario'),
    path('administracion/moderacion-contenido/', views.moderacionContenido, name='moderacionContenido'),
    path('administracion/moderacion-contenido/eliminar-post/<int:post_id>/', views.eliminar_post_colegio, name='eliminar_post_colegio'),
    
    #Vistas Empresa
    path('business/', views.business, name='business'), #business
    path('dashboard/', views.dashboard, name='dashboard'), #dashboard

    #Funciones generales
    path('post/', views.crear_post, name='crear_post'),
    path('like/<int:post_id>/', views.toggle_like, name='toggle_like'),
    path('mi-perfil/', views.ver_perfil, name='ver_perfil'),
    path('mi-perfil/actualizar/', views.actualizar_perfil, name='actualizar_perfil'),
    path('mi-perfil/cambiar-password/', views.cambiar_password, name='cambiar_password'),
    path('mi-perfil/configurar-notificaciones/', views.configurar_notificaciones, name='configurar_notificaciones'),
    path('mi-perfil/configurar-privacidad/', views.configurar_privacidad, name='configurar_privacidad'),
path('mi-perfil/descargar-datos/', views.descargar_datos_json, name='descargar_datos_json'),


    path('testalert/', views.testalert, name='testalert')
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path("__debug__/", include(debug_toolbar.urls)),
    ] + urlpatterns

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)