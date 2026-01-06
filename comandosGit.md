Guía Básica de Comandos de Git
1. Configuración Inicial

Antes de empezar a trabajar con Git, necesitas configurar tu nombre de usuario y correo electrónico. Esto es importante para que tus commits sean identificados correctamente.

git config --global user.name "Tu Nombre"
git config --global user.email "tu-email@dominio.com"

2. Iniciar un Repositorio

Para iniciar un nuevo repositorio Git en tu proyecto, navega a la carpeta del proyecto y ejecuta:

git init


Esto creará un nuevo repositorio vacío con un subdirectorio .git.

3. Ver el Estado del Repositorio

Puedes ver el estado de tu repositorio para saber qué archivos han cambiado, cuál está listo para el commit, etc.

git status

4. Agregar Archivos al Área de Staging

Si has realizado cambios en archivos y quieres agregarlos al área de staging (para que estén listos para un commit), usa:

git add nombre-del-archivo


Para agregar todos los archivos modificados:

git add .

5. Realizar un Commit

Para guardar los cambios en el historial de Git, necesitas realizar un commit. Asegúrate de haber agregado los archivos antes con git add.

git commit -m "Descripción de los cambios"

6. Ver el Historial de Commits

Para ver todos los commits realizados en el repositorio:

git log


Si deseas ver los commits de manera más resumida:

git log --oneline

7. Trabajar con Ramas (Branches)
Crear una Nueva Rama

Para crear una nueva rama, usa:

git branch nombre-de-la-rama

Cambiar a una Rama

Para cambiar a una rama existente:

git checkout nombre-de-la-rama

Crear y Cambiar a una Nueva Rama

Puedes crear y cambiar a una nueva rama en un solo paso:

git checkout -b nombre-de-la-rama

Ver las Ramas Existentes

Para ver todas las ramas en tu repositorio:

git branch

Fusionar Ramas

Cuando quieras integrar los cambios de una rama en otra (por ejemplo, de feature a main):

Primero cambia a la rama donde quieres fusionar los cambios (por ejemplo, main):

git checkout main


Luego fusiona la rama de características (feature) a main:

git merge feature

8. Trabajar con Repositorios Remotos

Para trabajar con repositorios remotos, como los de GitHub, GitLab, o Bitbucket.

Clonar un Repositorio

Si quieres clonar un repositorio existente (crear una copia local):

git clone https://github.com/usuario/repo.git

Agregar un Repositorio Remoto

Si ya tienes un repositorio local y quieres vincularlo a un repositorio remoto, usa:

git remote add origin https://github.com/usuario/repo.git

Ver los Remotos Configurados

Para ver los repositorios remotos configurados:

git remote -v

Subir Cambios al Repositorio Remoto (Push)

Para enviar tus cambios locales al repositorio remoto:

git push origin nombre-de-la-rama

Obtener Cambios del Repositorio Remoto (Pull)

Para traer los cambios del repositorio remoto a tu repositorio local:

git pull origin nombre-de-la-rama

Actualizar Referencias de los Remotos

Para actualizar las ramas remotas y obtener nuevas referencias sin descargar los cambios:

git fetch

9. Deshacer Cambios

Si cometiste un error o quieres deshacer cambios:

Deshacer Cambios en Archivos No Commited

Para descartar los cambios en un archivo modificado:

git checkout -- nombre-del-archivo

Deshacer el Último Commit

Para deshacer el último commit y mantener los cambios en el área de staging:

git reset --soft HEAD~1


Si deseas descartar el último commit y los cambios:

git reset --hard HEAD~1

10. Otros Comandos Útiles

Ver el estado de los archivos sin hacer un commit:

git diff


Eliminar un archivo del repositorio:

git rm nombre-del-archivo


Ver los cambios entre dos commits:

git diff commit1 commit2