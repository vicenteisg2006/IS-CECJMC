# Proyecto Ingenieria de Software  UDD 
### Centro Educacional Cardenal José María Caro

Integrantes:
- Alessandro Lavezzi Crovetto
- Juan Pablo Molina Peñaloza
- Vicente Ignacio Sepúlveda Guajardo

&nbsp;
## Requisitos 
* Git
* Pip

&nbsp;
## Configuración inicial
Para levantar el proyecto desde tu dispositivo debes:

1) Clonar el repositorio:

    > git clone https://github.com/vicenteisg2006/Proyecto_IS_CECJMC.git

&nbsp;

2) Crear un ambiente virtual:

    > python -m venv [nombre ambiente, ideal usar venv o env ]

&nbsp;

3) Activar el entorno:

    > [nombre ambiente]\Scripts\activate (Windows)


    >source [nombre ambiente]/bin/activate (mac/linux)

&nbsp;

4) Preparar la base de datos inicial

    >python manage.py migrate

&nbsp;
## Rules
1) No trabajar sobre MAIN:

    Se debe crear una rama para cada tarea:
    
    >git checkout -b feature/[nombre]

    Agregar los cambios trabajados a la nueva rama:

    > git add .

    Guardar los cambios:

    >git commit -m "[una nota o comentario sobre el trabajo realizado]"

    Subir esa rama a GitHub:

    >git push -u origin feature/[nombre]

    Analizar e integrar la nueva rama (desde la web)

    Volver a la rama principal de nuestro pc:

   > git checkout main

   Sincronizar nuestra rama principal del PC con la de GIT:

   >git pull origin main

   &nbsp;

2) Risas y diversión :D


