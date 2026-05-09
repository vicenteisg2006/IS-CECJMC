from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError

#         #######################################
#       ############# TABLAS MAESTRAS #############
#         #######################################

# muy estaticas, se añaden acá para mejorar velocidad, sacrificando la
# forma normal, de mantener todo por separado y hacer JOINs
class EstadoOferta(models.TextChoices):
    ACTIVA = 'activa','Activa'
    INACTIVA = 'inactiva','Inactiva'
    EXPIRADA = 'expirada','Expirada'

class EstadoSolicitud(models.TextChoices):
    ACEPTADA = 'aceptada','Aceptada'
    RECHAZADA = 'rechazada','Rechazada'
    PENDIENTE = 'pendiente','Pendiente'

class EstadoVerificacion(models.TextChoices):
    APROBADO = 'aprobado','Aprobado'
    RECHAZADO = 'rechazado','Rechazado'
    PENDIENTE = 'pendiente','Pendiente'

class TipoPerfil(models.TextChoices):
    ADMIN = 'admin','Admin'
    ESTUDIANTE = 'estudiante','Estudiante'
    COLEGIO = 'colegio','Colegio'
    EMPRESA = 'empresa','Empresa'

class Region(models.Model):
    region = models.CharField(max_length=100)

    def __str__(self):
        return self.region

class Comuna(models.Model):
    comuna = models.CharField(max_length=100)

    def __str__(self):
        return self.comuna

class Slep(models.Model):
    nombre = models.CharField(max_length=200)
    direccion = models.CharField(max_length=255)

    def __str__(self):
        return self.nombre

class CentroEducacional(models.Model):
    slep = models.ForeignKey(Slep, on_delete=models.SET_NULL, null=True)
    nombre = models.CharField(max_length=200)
    direccion = models.CharField(max_length=255)

    especialidades = models.ManyToManyField('Competencia', related_name='colegios_que_la_imparten', blank=True)

    def __str__(self):
        return self.nombre

class Requisito(models.Model):
    requisito = models.CharField(max_length=255)
    
class TipoCompetencia(models.TextChoices):
    ESPECIALIDAD = 'especialidad','Especialidad'
    OFICIO = 'oficio','Oficio'

class Competencia(models.Model):
    tipo_competencia = models.CharField(TipoCompetencia, max_length=15, null=True, choices=TipoCompetencia.choices)
    competencia = models.CharField(max_length=255)

    def __str__(self):
        return f"{TipoCompetencia.tipo_competencia} - {self.competencia}"

class TipoHabilidad(models.TextChoices):
    TECNICA = 'tecnica','Técnica'
    INTERPERSONAL = 'interpersonal','Interpersonal'

class Habilidad(models.Model):
    tipo_habilidad = models.CharField(TipoHabilidad, max_length=15, null=True, choices=TipoHabilidad.choices)
    habilidad = models.CharField(max_length=255)

    def __str__(self):
        return self.habilidad

class Curso(models.Model):
    nombre = models.CharField(max_length=50)
    centro_educacional = models.ForeignKey(CentroEducacional, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.nombre} ({self.centro_educacional.nombre})"

#         #######################################
#       ############## TABLA USUARIO ###############
#         #######################################

class Usuario(AbstractUser):
    fecha_nacimiento = models.DateField(null=True, blank=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(max_length=255, blank=True, null=True)
    # Reverted avatar ImageField back to avatar_url URLField
    avatar_url = models.URLField(max_length=500, null=True, blank=True)
    bio = models.TextField(blank=True, null=True)

    notif_email = models.BooleanField(default=True)
    notif_mensajes = models.BooleanField(default=True)
    notif_practicas = models.BooleanField(default=True)

    VISIBILIDAD_CHOICES = [
        ('publico', 'Público'),
        ('privado', 'Privado'),
    ]
    visibilidad_perfil = models.CharField(
        max_length=20,
        choices=VISIBILIDAD_CHOICES,
        default='publico'
    )

    @property
    def get_avatar(self):
        if self.avatar_url:
            return self.avatar_url
        return '/static/images/profilepic1.jpg'

    # Llaves Foráneas (Foreign Keys)
    tipo_perfil = models.CharField(TipoPerfil, choices=TipoPerfil.choices, max_length=20, default=TipoPerfil.ADMIN)
    region = models.ForeignKey(Region, on_delete=models.SET_NULL, blank=True, null=True)
    comuna = models.ForeignKey(Comuna, on_delete=models.SET_NULL, blank=True, null=True)
    centro_educacional = models.ForeignKey(CentroEducacional, on_delete=models.SET_NULL, blank=True, null=True)
    colegios_vinculados = models.ManyToManyField('CentroEducacional', related_name='empresas_asociadas', blank=True)
    competencias = models.ManyToManyField(Competencia, related_name='usuarios_competencia', blank=True, through='CompetenciaEstudiante')
    curso = models.ForeignKey(Curso, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        
        tipo = self.tipo_perfil

        if tipo == TipoPerfil.ESTUDIANTE:
            return f"{self.tipo_perfil} - {self.centro_educacional} - {self.first_name} {self.last_name}"
        elif tipo == TipoPerfil.COLEGIO:
            return f"{self.tipo_perfil} - {self.centro_educacional}"
        elif tipo == TipoPerfil.EMPRESA:
            return f"{self.tipo_perfil} - {self.first_name}"
        elif tipo == TipoPerfil.ADMIN:
            return f"Super Admin - {self.username}"

# entidades

class Certificado(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='certificados_creados')
    certificacion = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    entidad_emisora = models.CharField(max_length=200)

class ObtencionCertificado(models.Model):
    estudiante = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='certificados_obtenidos')
    certificado = models.ForeignKey(Certificado, on_delete=models.CASCADE)
    fecha_obtencion = models.DateField()
    fecha_expiracion = models.DateField(null=True, blank=True)
    url = models.URLField(max_length=500, blank=True)
    estado_verificacion = models.CharField(EstadoVerificacion, null=True, choices=EstadoVerificacion.choices, max_length=20)

class HabilidadUsuario(models.Model):
    habilidad = models.ForeignKey(Habilidad, on_delete=models.CASCADE)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    competencia = models.CharField(max_length=100)
    estado_verificacion = models.CharField(EstadoVerificacion, null=True, choices=EstadoVerificacion.choices, max_length=20)

class CompetenciaEstudiante(models.Model):
    competencia = models.ForeignKey(Competencia, on_delete=models.CASCADE)
    estudiante = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    fecha_registro = models.DateField(auto_now_add=True)
    estado_verificacion = models.CharField(EstadoVerificacion, null=True, choices=EstadoVerificacion.choices, max_length=20)

class ExperienciaLaboral(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='experiencias_como_estudiante')
    empresa_registrada = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name='experiencias_como_empresa')
    institucion_laboral = models.CharField(max_length=200, blank=True)
    contacto = models.CharField(max_length=200, blank=True)
    fecha_inicio = models.DateField()
    fecha_termino = models.DateField(null=True, blank=True)
    horas_trabajadas = models.IntegerField(null=True, blank=True)
    es_practica = models.BooleanField(default=False)
    estado_verificacion = models.CharField(EstadoVerificacion, null=True, choices=EstadoVerificacion.choices, max_length=20)

    @property
    def obtener_nombre_empresa(self):
        if self.empresa_registrada:
            return self.empresa_registrada.first_name
        elif self.institucion_laboral:
            return self.institucion_laboral
        else:
            return "Empresa Desconocida"

    def clean(self):
        if self.empresa_registrada and self.institucion_laboral:
            raise ValidationError("No puedes seleccionar una empresa registrada y escribir un nombre manual al mismo tiempo.")
        if not self.empresa_registrada and not self.institucion_laboral:
            raise ValidationError("Debes proveer una empresa registrada o escribir el nombre de la institución.")

class OfertaLaboral(models.Model):
    puesto_trabajo = models.CharField(max_length=200)
    empresa = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='ofertas_empresa')
    colegio = models.ForeignKey(CentroEducacional, on_delete=models.CASCADE, related_name='practicas_recibidas', null=True)
    competencia = models.ForeignKey(Competencia, on_delete=models.SET_NULL, null=True, blank=True)
    es_practica = models.BooleanField(default=False)
    fecha_publicacion = models.DateTimeField(auto_now_add=True)
    fecha_expiracion = models.DateTimeField()
    detalle = models.TextField()
    sueldo = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True)
    modalidad = models.CharField(max_length=100)
    ubicacion = models.CharField(max_length=255)
    estado_oferta = models.CharField(EstadoOferta, null=True, choices=EstadoOferta.choices, max_length=20)
    estado_verificacion = models.CharField(EstadoVerificacion, null=True, choices=EstadoVerificacion.choices, max_length=20, default=EstadoVerificacion.PENDIENTE)

    requisitos_habilidad = models.ManyToManyField(Habilidad, related_name='ofertas', blank=True)
    requisitos_competencia = models.ManyToManyField(Competencia, related_name='ofertas_relacionadas', blank=True)

class Postulacion(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='postulaciones')
    oferta_laboral = models.ForeignKey(OfertaLaboral, on_delete=models.CASCADE, related_name='postulantes')
    fecha_postulacion = models.DateTimeField(auto_now_add=True)
    estado_solicitud = models.CharField(EstadoSolicitud, null=True, choices=EstadoSolicitud.choices, max_length=20)

class Post(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='posts')
    mensaje = models.TextField(max_length=4000)
    fecha_publicacion = models.DateTimeField(auto_now_add=True)
    likes = models.ManyToManyField(Usuario, related_name='liked_posts', through='Like')

class Like(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

class ContenidoEducativo(models.Model):
    colegio = models.ForeignKey(CentroEducacional, on_delete=models.CASCADE, related_name='material_educativo')
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    url_video = models.URLField(blank=True, null=True, help_text="Enlace de YouTube o Vimeo")
    # Reverted archivo FileField to archivo_url URLField for resources
    archivo_url = models.URLField(max_length=500, blank=True, null=True)
    fecha_subida = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.titulo} - {self.colegio.nombre}"

class Multimedia(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('ready', 'Ready'),
        ('error', 'Error'),
    ]
    # Make post nullable since not all multimedia belongs to a Post
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, 
        related_name='multimedia',
        null=True, blank=True
    )
    # Add ContenidoEducativo link
    contenido_educativo = models.ForeignKey(
        ContenidoEducativo, on_delete=models.CASCADE,
        related_name='multimedia',
        null=True, blank=True
    )
    url = models.URLField(max_length=500)
    tipo_multimedia = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    fecha_publicacion = models.DateTimeField(auto_now_add=True)

class Comentario(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comentarios')
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    mensaje = models.TextField(max_length=255, default='')
    fecha_publicacion = models.DateTimeField(auto_now_add=True)
    likes = models.ManyToManyField(Usuario, related_name='liked_comments', through='UsuarioComentarioLike')

class UsuarioComentarioLike(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    comentario = models.ForeignKey(Comentario, on_delete=models.CASCADE)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

class Conexion(models.Model):
    solicitante = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='conexiones_enviadas')
    receptor = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='conexiones_recibidas')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    estado_solicitud = models.CharField(EstadoSolicitud, null=True, choices=EstadoSolicitud.choices, max_length=20)

class Notificacion(models.Model):
    receptor = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='notificaciones_recibidas')
    actor = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='notificaciones_generadas')
    leido = models.BooleanField(default=False)
    tipo_accion = models.CharField(max_length=100)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    class Meta:
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"

