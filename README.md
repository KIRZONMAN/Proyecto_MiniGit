Instrucciones:
Deben colocar el script en la carpeta de su preferencia
(recomendada una carpeta para testear el archivo)

Para usarlo, acá está la secuencia (todo será por consola):
1. Para crear archivos mediante consola escriban por ejemplo:

echo Hola Minigit > archivo1.txt
echo Este es otro archivo > archivo2.txt

(sugerido crear más de 2)

En pantalla: no sale nada especial, solo vuelve a la línea de comandos
2. Para el comando init escriban:

python minigit.py init

En pantalla (ejemplo):

Repositorio MiniGit inicializado correctamente.

Si ya estaba inicializado y lo vuelven a ejecutar, puede salir algo como:

MiniGit ya estaba inicializado en este directorio.

3. Para añadir archivos escriban por ejemplo:

python minigit.py add archivo1.txt archivo2.txt

En pantalla (ejemplo):

Agregado al área de preparación: archivo1.txt
Agregado al área de preparación: archivo2.txt

4. Para crear un commit escriban (con un mensaje entre comillas):

python minigit.py commit "Primer commit de prueba"

En pantalla (ejemplo):

Commit 1 creado:
    Mensaje: "Primer commit de prueba"
    Archivos: archivo1.txt, archivo2.txt

Si intentan hacer commit sin haber hecho add antes:

No hay archivos en el área de preparación (index).
Usa primero: python minigit.py add <archivo>

5. Para ver el estado actual del repositorio (status – comando extra):

python minigit.py status

En pantalla (ejemplo):

=== MiniGit status ===
Último commit aplicado (HEAD): 1

Archivos en el área de preparación (staged):
  (ninguno)

Archivos modificados desde el último commit:
  (ninguno)

Archivos eliminados desde el último commit:
  (ninguno)

Archivos no rastreados (untracked):
  (ninguno)

Si luego editan algún archivo y vuelven a ejecutar status, podría ver algo como:

Archivos modificados desde el último commit:
  archivo1.txt

6. Para ver el historial de commits (log – comando extra):

python minigit.py log

En pantalla (ejemplo con dos commits):

Historial de commits:
----------------------------------------
Commit 2
Fecha: 2025-11-23T17:30:10
Mensaje: "Segundo commit de prueba"
Archivos: archivo1.txt
----------------------------------------
Commit 1
Fecha: 2025-11-23T17:25:00
Mensaje: "Primer commit de prueba"
Archivos: archivo1.txt, archivo2.txt
----------------------------------------

Si todavía no hay commits:

No hay commits todavía.

7. Para restaurar a un commit anterior (restore):

Primero miran el log para saber qué ID quieren usar:

python minigit.py log

Luego, para restaurar por ejemplo al commit 1:

python minigit.py restore 1

En pantalla (ejemplo):

Restaurado: archivo1.txt
Restaurado: archivo2.txt
Repositorio restaurado al commit 1.
Mensaje del commit: "Primer commit de prueba"

Si ponen un ID que no existe:

Error: el commit 99 no existe.

Si escriben mal el comando:

Uso: python minigit.py
