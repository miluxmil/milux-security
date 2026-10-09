Milux Security 2.0

Edición Python para Termux en Android · Interfaz cyberpunk negra y verde neón

Reconstrucción del concepto original de Milux Security (2018), desarrollada en Python para Termux, con autenticación por contraseña y mecanismos de recuperación de acceso.

Funciones

- Configuración inicial sin contraseña predeterminada.
- Autenticación mediante contraseña almacenada como registro derivado criptográfico.
- Límite de tres intentos de contraseña antes de iniciar la recuperación.
- Ocho códigos de recuperación aleatorios de un solo uso.
- Recuperación de acceso mediante código de recuperación o SMS, cuando se ha configurado un teléfono verificado.
- Cambio de contraseña y regeneración de códigos de recuperación.
- Archivos de configuración locales con permisos restrictivos.
- Interfaz de terminal con colores y animaciones.

Requisitos

- Android con Termux.
- Python 3.
- OpenSSL y las herramientas que utilice la implementación de autenticación.
- Termux:API y los permisos necesarios para las funciones de SMS.

La disponibilidad del envío de SMS depende del dispositivo, la SIM, los permisos y el entorno de Termux.

Instalación

Actualiza los paquetes e instala Python y OpenSSL:

pkg update
pkg install python openssl

Para las funciones de SMS, instala también Termux:API desde una fuente compatible y configura los permisos necesarios.

Guarda el archivo "milux-security.py" en una carpeta y ejecuta:

mkdir -p ~/milux-security
cd ~/milux-security
chmod 700 milux-security.py
python milux-security.py

En el primer inicio, crea una contraseña y guarda los códigos de recuperación en un lugar seguro. No los compartas ni los publiques.

Configuración

Los archivos de configuración se guardan en:

~/.milux-security/

Incluyen la configuración de la contraseña, los datos de recuperación y los hashes de los códigos, según la implementación actual.

No publiques esos archivos ni compartas sus contenidos.

Seguridad y limitaciones

Milux Security proporciona una barrera de acceso a su propia interfaz de terminal. No cifra archivos ni sustituye el bloqueo de Android, el cifrado del dispositivo o los controles de seguridad del sistema operativo.

Una persona con acceso suficiente a la sesión de Termux o capacidad para modificar el script y sus archivos locales podría eludir esta barrera. La integración con el shell tampoco constituye una protección absoluta del dispositivo.

Los códigos de recuperación deben mantenerse privados. La recuperación por SMS depende de la configuración local y del acceso al teléfono y a la SIM; no debe considerarse un segundo factor independiente si el mismo dispositivo controla ambos lados del proceso.

No reutilices contraseñas de otras cuentas y no confíes en este proyecto como único mecanismo para proteger información sensible.

Créditos y licencia

Creado originalmente por Juan M.R. (miluxmil) en 2018. Esta reconstrucción conserva la atribución al concepto original.

Consulta el archivo "LICENSE" para conocer los términos de uso, modificación y redistribución.

Estado del proyecto

Versión 2.0.0 de la reconstrucción en Python. El proyecto está en desarrollo y debe probarse en el dispositivo y la versión de Termux de destino antes de confiarle cualquier uso importante.

Las contribuciones y mejoras deben respetar la licencia y mantener los créditos correspondientes.
