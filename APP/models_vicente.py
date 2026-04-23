# from django.db import models
# from django.contrib.auth.models import User


# #                  ====================
# #            ======= Tabla COLEGIO ========
# #                  ====================

# class COLEGIO(models.Model):
#     nombre = models.CharField(max_length=100)
#     direccion = models.CharField(max_length=200)

#     def __str__(self):
#         return self.nombre
    

# class NIVEL(models.Model):
#     colegio = models.ForeignKey(COLEGIO, on_delete=models.CASCADE)

#     nombre = models.CharField(max_length=50)
#     año = models.IntegerField()

#     def __str__(self):
#         return f"{self.colegio.nombre} - {self.nombre} - Año: {self.año}"
















































# #                  ====================
# #             ======= Tabla ENRUTADOR =======
# #                  ====================

# class ENRUTADOR(models.Model):
#     tipo_usuario = (
#         ('alumno', 'Alumno'),
#         ('colegio', 'Colegio'),
#         ('empresa', 'Empresa'),
#     )

#     #Sistema de autenticación DJANGO
#     usuario = models.OneToOneField(User, on_delete=models.CASCADE)

#     #Definición
#     tipo = models.CharField(max_length=20, choices=tipo_usuario, default='alumno')


#     def __str__(self):
#         return f"{self.usuario.username} - {self.tipo.upper()}"
    


    

# #                  ====================
# #             ======= Tabla Estudiante =======
# #                  ====================

# class ESTUDIANTE(models.Model):
#     enrutador = models.OneToOneField(ENRUTADOR, on_delete=models.CASCADE)
#     colegio = models.ForeignKey(COLEGIO, on_delete=models.CASCADE)
#     nivel = models.ForeignKey(NIVEL, on_delete=models.CASCADE, null= True, blank=True)


#     rut = models.CharField(max_length=12, unique=True)

#     def __str__(self):
#         nombre = self.enrutador.usuario.first_name
#         apellido = self.enrutador.usuario.last_name

#         return f"Alumno: {nombre} {apellido}, Colegio: {self.colegio.nombre}"
    




# #                  ====================
# #             ======= Tabla Empresa =======
# #                  ====================

# class EMPRESA(models.Model):
#     enrutador = models.OneToOneField(ENRUTADOR, on_delete=models.CASCADE)

#     nombre = models.CharField(max_length=100)
#     direccion = models.CharField(max_length=200)

#     rut_empresa = models.CharField(max_length=15, unique=True)

#     def __str__(self):
#         return f"Empresa: {self.nombre}"







