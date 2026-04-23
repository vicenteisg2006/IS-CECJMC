from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.apps import apps
from .models import Usuario
# from .models import COLEGIO, ENRUTADOR, ESTUDIANTE, EMPRESA, NIVEL

# Register your models here.
# admin.site.register(COLEGIO)
# admin.site.register(ENRUTADOR)
# admin.site.register(ESTUDIANTE)
# admin.site.register(EMPRESA)
# admin.site.register(NIVEL)

class CustomUserAdmin(UserAdmin):
    # Qué campos mostrar al EDITAR un usuario
    fieldsets = UserAdmin.fieldsets + (
        ('Datos REL+', {'fields': ('tipo_perfil', 'centro_educacional', 'curso', 'telefono', 'direccion')}),
    )
    # Qué campos mostrar al CREAR un usuario nuevo
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Datos REL+', {'fields': ('tipo_perfil', 'centro_educacional', 'curso')}),
    )

    list_display = ['__str__']
    list_filter = ['tipo_perfil']

admin.site.register(Usuario, CustomUserAdmin)

app_config = apps.get_app_config(__package__)
for model in app_config.get_models():
    try:
        admin.site.register(model)
    except admin.sites.AlreadyRegistered:
        pass


