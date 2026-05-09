from django.db.models.signals import post_save
from django.dispatch import receiver
from . import models

@receiver(post_save, sender=models.OfertaLaboral)
def notificar_nueva_oferta(sender, instance, created, **kwargs):
    if created:
        # Buscamos estudiantes del mismo colegio que la oferta
        estudiantes = models.Usuario.objects.filter(
            tipo_perfil=models.TipoPerfil.ESTUDIANTE,
            centro_educacional=instance.colegio
        )
        
        for estudiante in estudiantes:
            models.Notificacion.objects.create(
                receptor=estudiante,
                actor=instance.empresa,
                tipo_accion=f"ha publicado una nueva oferta de práctica: {instance.puesto_trabajo}",
                leido=False
            )

# Señal para Postulación Aceptada o Rechazada
@receiver(post_save, sender=models.Postulacion)
def notificar_cambio_estado_postulacion(sender, instance, created, **kwargs):
    # Si no es nuevo, pero el estado cambió a aceptada/rechazada
    if not created and instance.estado in [models.EstadoSolicitud.ACEPTADA, models.EstadoSolicitud.RECHAZADA]:
        models.Notificacion.objects.create(
            receptor=instance.estudiante,
            actor=instance.oferta.empresa,
            tipo_accion=f"ha marcado tu postulación como {instance.get_estado_display()}",
            leido=False
        )

# Señal para Especialidad Validada por el Colegio
@receiver(post_save, sender=models.CompetenciaEstudiante)
def notificar_especialidad_aprobada(sender, instance, created, **kwargs):
    if instance.estado_verificacion == models.EstadoVerificacion.APROBADO:
        # El actor es el colegio vinculado al alumno
        colegio_user = models.Usuario.objects.filter(
            centro_educacional=instance.estudiante.centro_educacional,
            tipo_perfil=models.TipoPerfil.COLEGIO
        ).first()

        models.Notificacion.objects.create(
            receptor=instance.estudiante,
            actor=colegio_user if colegio_user else instance.estudiante,
            tipo_accion=f"ha validado tu especialidad técnica en {instance.competencia.competencia}",
            leido=False
        )