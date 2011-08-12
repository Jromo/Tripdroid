example.py corresponde al código del servidor, es un servido de Google App Engine

Tripdroid.rar incluye el proyecto en Eclipse, está configurado para ser utilizado en modo debug, es decir, con el emulador en Eclipse, por lo que el GPS está con el GPS Provider y el mapa de Google con la API Key para Debug. Para utilizarlo en un móvil se requiere cambiar el GPS Provider por Network Provider, y solicitar una API Key de Google Maps para release, de la siguiente forma: 

Primero:

Obtener una Suitable Private key http://developer.android.com/guide/publishing/app-signing.html#cert

Se resume en ejecutar:

$ keytool -genkey -v -keystore my-release-key.keystore 

-alias alias_name -keyalg RSA -keysize 2048 -validity 10000


Y se obtiene una keystore

después, generar una key para google maps con ese keystore  http://code.google.com/intl/es-ES/android/add-ons/google-apis/mapkey.html#getfingerprint


que en resumen es ejecutar lo siguiente:

$ keytool -list -alias alias_name -keystore my-release-key.keystore

luego, registrar el MD5 en google maps http://code.google.com/intl/es-ES/android/maps-api-signup.html y obtener la API key

Finalmente, poner esa API Key en el layout del mapa, y exportar el apk con Eclipse, usando el keystore ya creado al principio

