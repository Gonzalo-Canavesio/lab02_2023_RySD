# Informe del laboratorio 2

## Estructuración del servidor

El servidor se estructura en 3 partes:

- **Servidor**: Se inicializa el servidor y se lo mantiene recibiendo pedidos de conexión de los clientes. Para esto, utiliza el puerto 19500 por defecto. Cuando se recibe una petición, se crea un objeto *Connection* y un nuevo hilo de ejecución que se encargará de procesar la conexión. Una vez que el hilo termina su ejecución, es decir, se termina la conexión con ese cliente, el hilo se destruye.
- **Manejador de conexiones**: Es el encargado de recibir las peticiones de los clientes, procesarlas y enviar la respectiva respuesta. Se encarga de manejar los errores que pueden ocurrir durante la conexión servidor-cliente.
- **Constantes**: Es un archivo auxiliar donde se declaran las constantes que se utilizan en la implementación del servidor.

### Decisiones de diseño tomadas

#### Servidor

- Decidimos crear el directorio compartido en caso de que no exista, para evitar que el servidor falle al no encontrar el directorio compartido por olvidarnos de crearlo.
- Se utiliza un hilo por cada conexión con un cliente. Esto se hace para que el servidor pueda atender a múltiples clientes simultáneamente. Al utilizar un hilo por cada conexión, se evita que el servidor se bloquee al atender a un cliente, satisfaciendo el punto estrella del laboratorio. Decidimos usar hilos en vez de procesos hijos ya que los hilos comparten memoria y por lo tanto son más eficientes. Preferimos usar hilos antes que async server ya que los hilos son más simples de implementar y no contabamos con demasiado tiempo, por lo que preferimos ir por lo seguro.
- Decidimos que los errores fatales no cierran el servidor, sino que se cierra la conexión con el cliente que generó el error. Esto se hace para que el servidor pueda seguir atendiendo a otros clientes, ya que la mayoria de los errores fatales que estuvimos experimentando no afectan al resto de los clientes, solo al cliente que generó el error.

#### Constantes

- Se define *MAX_BUFFER_SIZE* en *2\*\*32* para gestionar comandos malintencionados de gran lingitud que puedan disminuir el rendimiento del servidor.
- Se define *NEWLINE* como *\n* para utilizarlo en la zona de código donde debemos detectar el carácter *\n* fuera de un terminador de pedido *\r\n* y poder notifcar al cliente el error *100* (BAD EOL) y cerrar la conexión.

#### Manejador de conexiones

- En el objeto *Connection* se definen varios atributos que se utilizan en el manejo de la conexión con el cliente y facilitan el código.
  - **self.directory**: Directorio compartido. Es importante tener acceso a este atributo para poder acceder a los archivos del directorio compartido, ya que si no no sabremos dónde buscar los archivos.
  - **self.s**: Socket de la conexión. Es importante tener acceso a este atributo para poder enviar y recibir datos del cliente. Tambien se utiliza para cerrar la conexión.
  - **self.connected**: Booleano que indica si la conexión está activa. Es importante tener acceso a este atributo para poder saber si la conexión está inactiva y terminar el hilo de ejecución/dejar de intentar recibir datos.
  - **self.buffer**: Buffer donde se almacenan los datos enviados por el cliente. Es importante tener acceso a este atributo para poder leer los comandos que el cliente envía y tenerlos almacenados para procesarlos en caso de que envie un comando incompleto o varios comandos de una sola vez.
- Decidimos modularizar el código en funciones para que sea más fácil de leer y entender. Tomamos inspiración del archivo *client.py* por recomendación de los profes, por lo que nos centraremos en desarrollar aquellas decisiones de diseño más importantes y que no se encuentran en el archivo *client.py*, ya que las otras son similares.
  - **self.header**: Esta función se encarga de enviar el encabezado de la respuesta al cliente. En caso de que el código sea terminal, finaliza con la conexión. Creamos esta función porque vimos que el código correspondiente a enviar el encabezado de la respuesta al cliente se repetía en varias partes del código.
  - **self.valid_file**: Esta función se encarga de verificar si el archivo que se quiere enviar al cliente existe en el directorio compartido. Creamos la función para evitar repetir código en los comandos *get_metadata* y *get_slice*.
  - **self.command_selector**: Esta función se encarga de seleccionar el comando que se quiere ejecutar y verifica que tanto el comando como los argumentos sean válidos. Acá desarrollamos un manejo de errores mediante try-except para los siguientes casos:
    - **ConnectionResetError o BrokenPipeError**: Esto sucede cuando la conexión del cliente es interrumpida de manera abrupta y sin aviso. En este caso, se cierra la conexión y se termina el hilo de ejecución sin mandar mensaje de respuesta, ya que no lo recibiría el cliente ya que la conexión no exite.
    - **Otras excepciones**: Si el servidor tiene algún fallo interno, aquí se captura, se cierra la conexión y se termina el hilo de ejecución enviando el código de error *199* (INTERNAL ERROR) al cliente.
  - **self._recv**: Aunque esta función es similar a la que se encuentra en *client.py*, le realizamos un par de cambios que merecen ser detallados a continuación:
    - **BAD_REQUEST**: Si el mensaje enviado por el cliente contiene caracteres invalidos o supera el *MAX_BUFFER_SIZE*, se devuelve el código de error *101* (BAD REQUEST) y se cierra la conexión.
    - **ConnectionResetError o BrokenPipeError**: Aqui también como en **self.command_selector** se captura la excepción cuando la conexión del cliente es interrumpida de manera abrupta y sin aviso y se toman las mismas medidas.
  - **self.handle**: Esta función es la principal que se encarga de gestionar la conexión con el cliente y mantener el hilo vivo. Tiene un ciclo que se ejecuta mientras la conexión esté activa. Dentro de este ciclo, se llama a la función **self.read_line** para recibir los datos del cliente y se procesan los datos recibidos. Si la conexión se interrumpe, es decir, el atributo **self.connected** se vuelve falso, se termina bucle y también el hilo de ejecución.
- Nos centramos mucho en que el servidor sea robusto, por lo que hicimos mucho uso de try-except para capturar las excepciones que pudieran ocurrir y tomar las medidas necesarias para que el servidor no se caiga y en caso de ser necesario, cierre la conexión de la manera más limpia posible.

#### Tests

Decidimos agregar nuevos tests para probar el servidor. Los tests que se agregaron son para verificar algunos casos borde extra que sentimos que no se encontraban cubiertos por los tests provistos por la cátedra y también para verificar que el servidor pueda atender a múltiples clientes simultáneamente.

## Dificultades con las que nos encontramos

1. La primera dificultad que nos encontramos fue lograr entender el código del servidor. Al principio, entendíamos cómo funcionaba el protocolo de comunicación entre el servidor y el cliente pero no como implementarlo en el código. Luego de leer el código varias veces y seguir los consejos del profe, logramos entenderlo y poder implementar el servidor. Creemos que fue de gran ayuda guiarnos por el código del cliente para poder entender y luego implementar el servidor.
2. La segunnda dificultad fue encontrar el tiempo y la organización del grupo para poder trabajar en el proyecto. Nos veiamos un poco abrumados por la cantidad de cosas que teníamos que hacer y por la falta de tiempo. Pero con comunicación y utilizando centralmente Telegram para poder organizarnos, logramos avanzar en el proyecto y terminarlo a tiempo.
3. El tercer obstaculo fue poder satisfacer los tests provistos por la cátedra. Luego de implementar el servidor probamos correr los tests y la mayoria de ellos fallaban. Por suerte los errores eran bastante descriptivos y no fue dificil corregirlos, excepto por el test de *test_multiple_commands*:
    - **test_multiple_commands**: Este test nos genero muchos problemas y fue el causante de la mitad de los try-except agregados en el código. Al parecer el test envia los dos comandos en un solo mensaje, luego lee un código de estado y cierra la conexión. El problema es que el servidor todavía debe enviarle información al cliente sobre el estado del segundo comando, pero como la conexión ya fue cerrada, el servidor no puede enviar los datos y genera una excepción de tipo *ConnectionResetError* o *BrokenPipeError*. Para poder solucionar este problema, decidimos agregar un try-except para capturar estas excepciones y terminar el hilo de ejecución sin enviar ningún mensaje de respuesta al cliente. Hasta que logramos alcanzar esa solución, nos costó mucho tiempo entender que era lo que estaba pasando y como solucionarlo porque dependía de la velocidad de la computadora y de la red, a veces el test pasaba sin generar problema y otras veces no. Realizamos una pequeña modificación al test para que no genere este problema, aunque agregamos un test nuevo para verificar que el servidor pueda seguir su ejecución aunque la conexión de un cliente se interrumpa de manera abrupta.
4. El cuarto obstaculo fue implementar el punto estrella del laboratorio, es decir, poder atender multiples clientes en simultaneo. Por suerte en una clase el profe explicó las principales maneras de hacerlo y con eso y un poco de investigación del funcionamiento de los hilos en python pudimos implementarlo.

## Preguntas planteadas

### ¿Qué estrategias existen para poder implementar este mismo servidor pero con capacidad de atender múltiples clientes simultáneamente?

Existen tres estrategias para poder implementar este mismo servidor pero con capacidad de atender múltiples clientes simultáneamente:

- **Multiples hilos**: En este caso, cada vez que se recibe una petición de un cliente, se crea un nuevo hilo que se encargará de atender la petición. Este hilo se encargará de leer las peticiones del cliente, procesarlas y responderle. Una vez que el hilo termina su ejecución, se destruye.
- **Creación de hijos**: En este caso, cada vez que se recibe una petición de un cliente, se crea un nuevo proceso hijo que se encargará de atender la petición. Este proceso hijo se encargará de leer las peticiones del cliente, procesarlas y responderle. Una vez que el proceso hijo termina su ejecución, se destruye. Esta estrategia es similar a la anterior pero tiene la diferencia de que al generar un nuevo proceso hijo, se genera un nuevo espacio de memoria. Al trabajar con hilos se comparte el mismo espacio de memoria.
- **Async server**: En este caso, se utilizan técnicas de programación asincrónicas para procesar múltiples solicitudes de manera eficiente sin bloquear el hilo de ejecución. En lugar de crear un hilo de ejecución para cada cliente y dentro del hilo esperar a que cada operación se complete, se registra una función de devolución de llamada (callback) que se ejecutará una vez que se complete la operación, por lo que cada hilo puede atender a múltiples clientes. Con esta estrategia, el servidor puede procesar múltiples solicitudes en paralelo sin necesidad de un gran número de hilos de ejecución, lo que lo hace más eficiente y escalable que las estrategias anteriores. Esta estrategia se basa en eventos, a diferencia de las anteriores que se basan en hilos/procesos.

#### ¿Qué cambios serían necesario en el diseño del código para implementar cada una de estas estrategias?

- **Multiples hilos**: Para implementar esta estrategia, sería necesario modificar el código para que cada vez que se reciba una petición de un cliente, se cree un nuevo hilo que se encargue de atenderlo y se destruya una vez que se cierra la conexión. La gestión de los hilos se puede realizar utilizando la librería *threading* y se puede realizar en la función **serve** del archivo *sevrer.py*.
- **Creación de hijos**: Para implementar esta estrategia, sería necesario modificar el código para que cada vez que se reciba una petición de un cliente, se cree un nuevo proceso hijo que se encargue de atenderlo y se destruya una vez que se cierra la conexión. La gestión de los procesos hijos se puede realizar utilizando la librería *multiprocessing* de python y se puede realizar en la función **serve** del archivo *server.py*.
- **Async server**: Para implementar esta estrategia se puede utilizar la librería *asyncio* de python y se debería rehacer gran parte del código del proyecto, ya que se debería utilizar una arquitectura basada en eventos (Se debería crear un *loop* de eventos que se encargue de manejar las conexiones de los clientes y las peticiones que estos realizan).

### ¿Qué diferencia hay si se corre el servidor desde la IP “localhost”, “127.0.0.1” o la ip “0.0.0.0”?

- **localhost**: Al utilizar esta IP el servidor solo puede ser accedido desde la misma máquina en la que se está ejecutando. Es una dirección IP que se utiliza para referirse a la propia máquina, es decir, el servidor solo es accesible desde la misma máquina en la que se está ejecutando. Este es un adaptador de red "falso" que solo puede comunicarse dentro del mismo host, por lo que las peticiones no se envía a Internet a través del router, sino que permanecen en el sistema.
- **127.0.0.1**: Al utilizar esta IP tenemos el mismo comportamiento que con localhost. Investigamos y lo que sucede es que "localhost" y "127.0.0.1" son equivalentes y se refieren a la dirección IP reservada que se usa para comunicarse con la misma máquina a través de la red. A esta dirección se la denomina dirección IP de loopback o bucle reverso.
- **0.0.0.0**: Al utilizar esta IP el servidor puede ser accedido desde cualquier máquina de la red. Es una dirección IP que se utiliza para referirse a cualquier interfaz de red disponible en la máquina. Cuando se le dice a un servidor que escuche 0.0.0.0 eso significa "escuchar en cada interfaz de red disponible".

## Conclusiones

- Aprendimos a implementar un servidor TCP en python y a utilizar sockets para la comunicación entre el servidor y los clientes.
- Investigamos sobre las diferentes estrategias para poder implementar un servidor que pueda atender múltiples clientes simultáneamente.
- Aprendimos sobre unit testing y como utilizarlo para probar nuestro código.
- Reforzamos el uso de git para el control de versiones.
- Mejoramos nuestras habilidades de comunicación y trabajo en equipo.
