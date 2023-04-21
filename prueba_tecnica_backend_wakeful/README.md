# Prueba Tecnica Backend Wakeful
---
## Proceso de desarrollo

1. Teniendo en cuenta los requerimientos de la tarea, se optó heredar de `AbstractBaseUser` para la creación de un usuario nuevo. Esto permite eliminar por completo el `username`; lo cual traerá un problema más a futuro.
2. El nuevo `CustomUser` sólo necesita de email y contraseña para ser creado. Eventualmente, se pueden añadir los campos de `first_name`, `last_name`, `birthdate` y `phone`. Por defecto, también añadimos `is_staff`, para definir si el usuario puede ingresar al sitio de admin de Django, e `is_active`. En el caso de `phone` se añade un validador que hace uso de la librería `phonenumbers` para validar el número teléfono. La validación de email la hace Django por defecto al especificar el `EmailField`.
3. Antes de poder crear un Superuser es necesario hacer un par de cambios más. Primero, cambiar el `AUTH_USER_MODEL` en `settings.py` para que la aplicación sepa que hay que usar el usuario nuevo. Sin este cambio, no podríamos ni siquiera entrar al Admin Panel.
    ```python
    AUTH_USER_MODEL = "users.CustomUser"
    ```

    Luego, creamos forms para la creación de usuarios nuevos, definiendo que sólo es necesario el email, y realizar cambios al usuario en sí. En esta última definimos todos los campos que el usuario puede cambiar o añadir una vez que fue creado.

4. Con estos cambios hechos, ya podemos crear un `CustomUserAdmin` para registar el nuevo usuario en el panel de Admin. Dentro sde este mismo `CustomUserAdmin` estarán definidas las forms que creamos previamente.
5. Se definen los 2 endpoints para el usuario. Dado que las operaciones para ambos están intrínsicamente atadas al usuario, optamos por heredar de `ModelSerializer`. Para el caso del PUT method (Update) verificamos los campos que vienen en el payload para actualizar los que correspondan. De las validaciones se encarga DRF (con excepción del teléfono que ya tiene validación a nivel modelo), así que no hace falta implementar nada como para validar la fecha de nacimiento, por ejemplo, o de cualquier otro campo que se pueda enviar que no esté relacionado al modelo.
6. Con esto ya estamos listos para pasar a la parte de autenticación.
7. Acá se tomó un camino un tanto particular, así que procederemos a explicar el porqué de ciertas decisiones.

   A primera vista, viendo los requerimientos de la tarea se optó por buscar librerías para Django que ayudasen a implementar el doble factor de autenticación. Luego de evaluar las opciones, se decidió proceder con [django-trench](https://django-trench.readthedocs.io/en/latest/index.html). A la primera prueba nos dimos cuenta de que los requests fallaban alegando que requerían el campo `username`. Una inspección al código fuente de la librería revelo que django-trench utiliza el `User` por defecto de Django. En la rama develop del proyecto, al momento de la escritura de este README, se realizaron algunos cambios para que pueda usarse con cualquier usuario personalizado que herede de `AbstractUser`; que contiene los campos `username` y `password` por defecto. Esto no nos ayuda demasiado a nosotros que heredamos de `AbstractBaseUser`.

   El camino que se decidió tomar es clonar el repositorio y modificarlo de tal forma que pueda aceptar el `CustomUser` que creamos. En efecto, forkear el repositorio. ¿Por qué? Para no tener que reimplementar toda la lógica que ya nos brinda esta librería. El repositorio clonado se lo dejó en un módulo de librerías que luego podemos instalar en la aplicación de Django vía Poetry. De esta forma, no contaminamos la aplicación con el repositorio clonado de django-trench. El único "downside" de este approach es tener que estar atento a nuevos releases de django-trench y mantener actualizado el módulo forkeado.
8. Para verificar que los endpoints respondan de la forma esperada se escribieron tests unitarios utilizando el módulo de `unittest` de la librería estándar de Python.
9. TODO Mencionar herramientas de desarrollo utilizadas.. ruff, black, isort, etc.