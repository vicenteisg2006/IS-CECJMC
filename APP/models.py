from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError


#         #######################################
#       ############# TABLAS MAESTRAS #############
#         #######################################

class TipoPerfil(models.Model):
    tipo_perfil = models.CharField(max_length=50)

    def __str__(self):
        return self.tipo_perfil

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

#

class CentroEducacional(models.Model):
    slep = models.ForeignKey(Slep, on_delete=models.SET_NULL, null=True)
    nombre = models.CharField(max_length=200)
    direccion = models.CharField(max_length=255)

    def __str__(self):
        return self.nombre

class EstadoVerificacion(models.Model):
    estado_verificacion = models.CharField(max_length=50)

class EstadoOferta(models.Model):
    estado = models.CharField(max_length=50)

class EstadoSolicitud(models.Model):
    estado = models.CharField(max_length=50)

class Requisito(models.Model):
    requisito = models.CharField(max_length=255)
    
class Competencia(models.Model):
    tipo_competencia = models.CharField(
        max_length=255,
        choices=[('ESP','Especialidad'),('OFI','Oficio')]
        )
    competencia = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.get_tipo_competencia_display()} - {self.competencia}"


#         #######################################
#       ############## TABLA USUARIO ###############
#         #######################################

class Usuario(AbstractUser):
    fecha_nacimiento = models.DateField(null=True, blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    direccion = models.CharField(max_length=255, blank=True)
    avatar_url = models.URLField(max_length=500, blank=True) # Ideal para Cloudflare
    bio = models.TextField(blank=True)
    curso = models.CharField(max_length=100, blank=True)
    
    # Llaves Foráneas (Foreign Keys)
    tipo_perfil = models.ForeignKey(TipoPerfil, on_delete=models.SET_NULL, null=True)
    region = models.ForeignKey(Region, on_delete=models.SET_NULL, null=True)
    comuna = models.ForeignKey(Comuna, on_delete=models.SET_NULL, null=True)
    centro_educacional = models.ForeignKey(CentroEducacional, on_delete=models.SET_NULL, blank=True, null=True)
    competencias = models.ManyToManyField(Competencia, related_name='usuarios_competencia', blank=True)

    # Vista mas ordenada para el admin
    def __str__(self):
        tipoo = self.tipo_perfil.tipo_perfil.lower() if self.tipo_perfil else "Desconocido"

        if tipoo == "estudiante" or tipoo == "alumno":
            return f"{self.tipo_perfil} - {self.centro_educacional} - {self.first_name} {self.last_name}"
        
        elif tipoo == "colegio":
            return f"{self.tipo_perfil} - {self.centro_educacional}"
        
        elif tipoo == "empresa":
            return f"{self.tipo_perfil} - {self.first_name}"
        
        else:
            return f"Super Admin - {self.username}"
        

# entidades

class Certificado(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='certificados')
    certificacion = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    fecha_obtencion = models.DateField()
    fecha_expiracion = models.DateField(null=True, blank=True)
    entidad_emisora = models.CharField(max_length=200)
    estado_verificacion = models.ForeignKey(EstadoVerificacion, on_delete=models.SET_NULL, null=True)
    url = models.URLField(blank=True)

class ExperienciaLaboral(models.Model):
    usuario = models.ForeignKey(
        Usuario, 
        on_delete=models.CASCADE, 
        related_name='experiencias_como_estudiante' # Django needs this!
    )
    
    empresa_registrada = models.ForeignKey(
        Usuario, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='experiencias_como_empresa' # Django needs this!
    )
    
    institucion_laboral = models.CharField(max_length=200, blank=True)
    
    contacto = models.CharField(max_length=200, blank=True)
    fecha_inicio = models.DateField()
    fecha_termino = models.DateField(null=True, blank=True)
    horas_trabajadas = models.IntegerField(null=True, blank=True)
    estado_verificacion = models.ForeignKey('EstadoVerificacion', on_delete=models.SET_NULL, null=True)

    @property
    def obtener_nombre_empresa(self):
        """
        Smart logic to return the company name.
        If a registered user is linked, it returns their official name.
        If not, it returns the manually typed text.
        """
        if self.empresa_registrada:
            # We assume the Usuario model has 'nombre'
            return self.empresa_registrada.nombre 
        elif self.institucion_laboral:
            return self.institucion_laboral
        else:
            return "Empresa Desconocida"
    
    def clean(self):
        # Check if BOTH fields have data
        if self.empresa_registrada and self.institucion_laboral:
            raise ValidationError("No puedes seleccionar una empresa registrada y escribir un nombre manual al mismo tiempo.")
        
        # Check if NEITHER field has data (assuming they must provide at least one)
        if not self.empresa_registrada and not self.institucion_laboral:
            raise ValidationError("Debes proveer una empresa registrada o escribir el nombre de la institución.")

class OfertaLaboral(models.Model):
    puesto_trabajo = models.CharField(max_length=200)
    empresa = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name = 'ofertas_empresa')
    fecha_publicacion = models.DateTimeField(auto_now_add=True)
    fecha_expiracion = models.DateTimeField()
    detalle = models.TextField()
    sueldo = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True) # Formato para CLP
    modalidad = models.CharField(max_length=100)
    ubicacion = models.CharField(max_length=255)
    estado_oferta = models.ForeignKey(EstadoOferta, on_delete=models.SET_NULL, null=True)
    
    # Magia de Django: Esto crea la tabla intermedia "RequisitoOfertaLaboral" automáticamente
    requisitos = models.ManyToManyField(Requisito, related_name='ofertas')

class Postulacion(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='postulaciones')
    oferta_laboral = models.ForeignKey(OfertaLaboral, on_delete=models.CASCADE, related_name='postulantes')
    fecha_postulacion = models.DateTimeField(auto_now_add=True)
    estado_solicitud = models.ForeignKey(EstadoSolicitud, on_delete=models.SET_NULL, null=True)

class Post(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='posts')
    mensaje = models.TextField()
    fecha_publicacion = models.DateTimeField(auto_now_add=True)
    
    # Magia de Django: Relación de "Likes" usando una tabla intermedia personalizada
    likes = models.ManyToManyField(Usuario, related_name='liked_posts', through='Like')

# Tabla intermedia de Likes explícita (porque tu ERD pedía guardar la fechaCreacion)
# clase que podria o podria no estar, quien sabe
class Like(models.Model): 
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

class Multimedia(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='multimedia')
    url = models.URLField(max_length=500)
    tipo_multimedia = models.CharField(max_length=50) # Ej. 'imagen', 'video'
    fecha_publicacion = models.DateTimeField(auto_now_add=True)

class Comentario(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comentarios')
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    comentario = models.TextField()
    fecha_publicacion = models.DateTimeField(auto_now_add=True)

class Conexion(models.Model):
    solicitante = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='conexiones_enviadas')
    receptor = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='conexiones_recibidas')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    estado_solicitud = models.ForeignKey(EstadoSolicitud, on_delete=models.SET_NULL, null=True)

class Notificacion(models.Model):
    receptor = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='notificaciones_recibidas')
    actor = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='notificaciones_generadas')
    leido = models.BooleanField(default=False)
    tipo_accion = models.CharField(max_length=100)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    class Meta:
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"