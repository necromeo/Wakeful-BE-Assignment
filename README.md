# Prueba Tecnica Backend Wakeful
---
## Proceso de desarrollo

1. Teniendo en cuenta los requerimientos de la tarea, se optó heredar de `AbstractBaseUser` para la creación de un usuario nuevo. Esto permite eliminar por completo el `username`; lo cual traerá un problema más a futuro.
2. El nuevo `CustomUser` sólo necesita de email y contraseña para ser creado. Eventualmente, se pueden añadir los campos de `first_name`, `last_name`, `birthdate` y `phone`. Por defecto, también añadimos `is_staff`, para definir si el usuario puede ingresar al sitio de admin de Django, e `is_active`. En el caso de `phone` se añade un validador que hace uso de la librería `phonenumbers` para validar el número teléfono. La validación de email la hace Django por defecto al especificar el `EmailField`.
3. Antes de poder crear un Superuser es necesario hacer un par de cambios más. Primero, cambiar el `AUTH_USER_MODEL` en `settings.py` para que la aplicación sepa que hay que usar el usuario nuevo. Sin este cambio, no podríamos ni siquiera entrar al Admin Panel.
    ```python
    AUTH_USER_MODEL = "users.CustomUser"
    ```

    Luego, creamos forms para la creación de usuarios nuevos, definiendo que sólo es necesario el email, y para realizar cambios al usuario en sí. En esta última definimos todos los campos que el usuario puede cambiar o añadir una vez que fue creado.

4. Con estos cambios en vigor, ya podemos crear un `CustomUserAdmin` para registar el nuevo usuario en el panel de Admin. Dentro sde este mismo `CustomUserAdmin` estarán definidas las forms que creamos previamente.
5. Se definen los 2 endpoints para el usuario. Dado que las operaciones para ambos están intrínsicamente atadas al usuario, optamos por heredar de `ModelSerializer`. Para el caso del PUT method (Update) verificamos los campos que vienen en el payload para actualizar los que correspondan. De las validaciones se encarga DRF (con excepción del teléfono que ya tiene validación a nivel modelo), así que no hace falta implementar nada como para validar la fecha de nacimiento, por ejemplo, o de cualquier otro campo que se pueda enviar que no esté relacionado al modelo.
6. Cuando se envía el payload con email y la contraseña, si está todo en orden, se devuelve un response con el ID del nuevo usuario y el email que quedó registrado. Se podría hacer uso de las signals que ofrece Django para ofrecer un access y refresh token al momento de registro pero se optó no implementarlo de momento.
7. Con todo esto ya estamos listos para pasar a la parte de autenticación (tomar nota del ID al haberse registrado).
8. Acá se tomó un camino un tanto particular, así que procederemos a explicar el porqué de ciertas decisiones.

   A primera vista, viendo los requerimientos de la tarea se optó por buscar librerías para Django que ayudasen a implementar el doble factor de autenticación. Luego de evaluar las opciones, se decidió proceder con [django-trench](https://django-trench.readthedocs.io/en/latest/index.html). A la primera prueba nos dimos cuenta de que los requests fallaban alegando que requerían el campo `username`. Una inspección al código fuente de la librería revelo que django-trench utiliza el `User` por defecto de Django. En la rama develop del proyecto, al momento de la escritura de este README, se realizaron algunos cambios para que pueda usarse con cualquier usuario personalizado que heredamos de `AbstractUser`; que contiene los campos `username` y `password` por defecto. Esto no nos ayuda demasiado a nosotros que heredamos de `AbstractBaseUser`.

   El camino que se decidió tomar es clonar el repositorio y modificarlo de tal forma que pueda aceptar el `CustomUser` que creamos. En efecto, forkear el repositorio. ¿Por qué? Para no tener que reimplementar toda la lógica que ya nos brinda esta librería. El repositorio clonado se lo dejó en un módulo de librerías que luego podemos instalar en la aplicación de Django vía Poetry. De esta forma, no contaminamos la aplicación con el repositorio clonado de django-trench. El único "downside" de este approach es tener que estar atento a nuevos releases de django-trench y mantener actualizado el módulo forkeado[^1].
9. El access y refresh token que se devuelve son Json Web Tokens (JWT). El único claim que contienen, fuera del `exp`, `iat` y `jti`, es el `user_id`. Por último, están firmados por la `SECRET_KEY` del proyecto.
10. Al solicitarse el código de doble factor para app, se devuelve una string `otpauth://...`. Si tuviesemos un front end, esta string se puede convertir en un código QR que cualquiera de las apps de autenticación puede interpretar (Google Authenticator, LastPass Authenticator, etc.). Lo más práctico para nuestro caso es instalar `qrcode` si estamos en Linux o Mac, preferentement usando pipx, `pipx install qrcode`. Luego en la terminal ejecutamos`qr <otpstring>` y obtenemos un código QR. Incluso, podemos tomar el secret que se encuentra en la string obtener el código usando la librería `pyotp` de python de la siguiente forma:
    ```python
    import pyotp

    totp = pyotp.TOTP("<otpstring>")
    totp.now()
    ```
    El código obtenido es el que pasamos en la confirmación del multiple factor de autentificacion. Como respuesta vamos a obtener 5 backup codes para guardar en caso no poder usar la app de autenticación, por la razón que sea, en el futuro.
11. Para verificar que los endpoints respondan de la forma esperada se escribieron tests unitarios utilizando el módulo de `unittest` de la librería estándar de Python; son 20 en total.
12. Herramientas de desarrollo se emplearon varias. Empezando por Docker Compose que era parte de los requerimientos de la tarea. Para mantener el orden de los imports se empleó `isort`. Para el formateo del código, `Black`. Si bien los lineamientos PEP pactan el largo de las líneas en 79 caracteres, se decidió optar por el default de `Black`, que es de 88. A su vez, se usó `ruff` como linter y se lo configuró para que pueda arreglar ciertos issues automáticamente. Incluído agregar "trailing comma" para auxiliar el formateo de `Black` (una preferencia puramente personal). Por último, también se añadió `mypy`, por costumbre, más allá de que para este pequeño proyecto no tuvo mucho uso. Aún así, un static type checker es invaluable en proyectos más grande. Las configuraciones para estas herramientas se encuentra en `pyproject.toml`.

    Para testeo manual se usó Postman. Hay una carpeta con el mismo nombre en la raíz del proyecto que se puede importar y que contiene todos los endpoints del proyecto y dos archivos templates para variables de entorno locales y de producción.

    Hablando de variables de entorno. Se hizo uso de `Pydantic` para crear un objeto que guarde todas las variables. Este approach es cómodo ya que nos permite verificar el tipo de la variable y también tener mensajes de error útiles por si se nos pasó por alto agregar una variable.

## Local

Correr de forma local el proyecto es sencillo. `Poetry` se encarga por completo de las dependencias. Para instalarlas basta con correr `poetry install` o `poetry install --with=dev` para instalar, además, las dependencias de desarrollo. En caso de no tener instalado la versión 3.10 de Python, se puede instalar `pyenv`, que es una suerte de administrador de versiones de Python.

El proyecto está _dockerizado_, por ende, para levantarlo por completo, junto con la base de datos de Postgres. `docker-compose up -d` debería bastar. Tomar nota de que el entrypoint al proyecto es distinto en el archivo compose. Esto es más que nada una ayuda para desarrollo local (corre `collecstatic` y tiene hot reloading). Además, se monta el directorio del proyecto en un volumen así nuestros cambios se ven reflejados inmediatamente. Por último, copiar el archivo `.env.sample`,renombrarlo `.env` y completarlo. En caso de olvidarse de este paso, al levantar el proyecto se recibirá un útil mensaje de error de Pydantic indicando las variables que faltan ser definidas.

Nota para correr los tests. Dado que Django necesita de conexión a la base de datos para los tests, lo más sencillo es correrlos dentro del mismo contenedor de Docker: `docker exec -it wakeful-backend python manage.py test`.
## Live App

#### ⚠️ Por vencimiento de la opción gratuita de railway, la app de demo ya no se encuentra disponible. ⚠️

Esta aplicación se encuentra deployada y accesible [aquí](https://wakeful-be-assignment-production.up.railway.app/) .
Los mails con los códigos de validación salen desde una cuenta de testeo de Gmail[^2].
Como hosting se usó [Railway](https://railway.app/), que permite subir un sitio de forma gratis por 500 horas y, además, ofrece una base de datos de Postgres. Heroku hubiese sido otra opción pero el plan gratis que ofrecían ya no es una opción desde noviembre del 2022.

[^1]: Esto entraría más en _sugerencias_ pero no podemos evitar notar que el ejercicio parece calcado de la documentación de django-trench. En cierta forma, parece que uno estaría casi obligado a usar esta librería sabiendo (el evaluador) que ofrece un desafío particular por tener que deshacerse del `username`.
[^2]: Durante el desarrollo se trabajó con [mailtrap](https://mailtrap.io/) con la idea de usarlo también cuando el sitio estuviese deployado. Lamentablemente, sin pagar no es posible enviar emails usando su API.
