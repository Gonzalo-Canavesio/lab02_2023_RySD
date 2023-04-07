# Informe del laboratorio 2

## Estructuración del servidor

COMPLETAR

## Decisiones de diseño tomadas

COMPLETAR

## Dificultades con las que nos encontramos

COMPLETAR

## Preguntas planteadas

### ¿Qué estrategias existen para poder implementar este mismo servidor pero con capacidad de atender múltiples clientes simultáneamente?

Existen tres estrategias para poder implementar este mismo servidor pero con capacidad de atender múltiples clientes simultáneamente:

- **Multiples hilos**: En este caso, cada vez que se recibe una petición de un cliente, se crea un nuevo hilo que se encargará de atender la petición. Este hilo se encargará de leer las peticiones del cliente, procesarlas y responderle. Una vez que el hilo termina su ejecución, se destruye.
- **Creación de hijos**: En este caso, cada vez que se recibe una petición de un cliente, se crea un nuevo proceso hijo que se encargará de atender la petición. Este proceso hijo se encargará de leer las peticiones del cliente, procesarlas y responderle. Una vez que el proceso hijo termina su ejecución, se destruye. Esta estrategia es similar a la anterior pero tiene la diferencia de que al generar un nuevo proceso hijo, se genera un nuevo espacio de memoria. Al trabajar con hilos se comparte el mismo espacio de memoria.
- **Async server**: En este caso, se utilizan técnicas de programación asincrónicas para procesar múltiples solicitudes de manera eficiente sin bloquear el hilo de ejecución. En lugar de crear un hilo de ejecución para cada cliente y dentro del hilo esperar a que cada operación se complete, se registra una función de devolución de llamada (callback) que se ejecutará una vez que se complete la operación, por lo que cada hilo puede atender a múltiples clientes. Con esta estrategia, el servidor puede procesar múltiples solicitudes en paralelo sin necesidad de un gran número de hilos de ejecución, lo que lo hace más eficiente y escalable que las estrategias anteriores. Esta estrategia se basa en eventos, a diferencia de las anteriores que se basan en hilos/procesos.

#### ¿Qué cambios serían necesario en el diseño del código para implementar cada una de estas estrategias?

COMPLETAR
INFORMACIÓN EXTRA PARA COMPLETAR ESTO:

- <https://eclipse-ee4j.github.io/jersey.github.io/documentation/latest/async.html>
- <https://medium.com/swlh/synchronous-and-asynchronous-servers-with-python-d5900e215483>

### ¿Qué diferencia hay si se corre el servidor desde la IP “localhost”, “127.0.0.1” o la ip “0.0.0.0”?

- **localhost**: Al utilizar esta IP el servidor solo puede ser accedido desde la misma máquina en la que se está ejecutando. Es una dirección IP que se utiliza para referirse a la propia máquina, es decir, el servidor solo es accesible desde la misma máquina en la que se está ejecutando. Este es un adaptador de red "falso" que solo puede comunicarse dentro del mismo host, por lo que las peticiones no se envía a Internet a través del router, sino que permanecen en el sistema.
- **127.0.0.1**: Al utilizar esta IP tenemos el mismo comportamiento que con localhost. Investigamos y lo que sucede es que "localhost" y "127.0.0.1" son equivalentes y se refieren a la dirección IP reservada que se usa para comunicarse con la misma máquina a través de la red. A esta dirección se la denomina dirección IP de loopback o bucle reverso.
- **0.0.0.0**: Al utilizar esta IP el servidor puede ser accedido desde cualquier máquina de la red. Es una dirección IP que se utiliza para referirse a cualquier interfaz de red disponible en la máquina. Cuando se le dice a un servidor que escuche 0.0.0.0 eso significa "escuchar en cada interfaz de red disponible".

## Conclusiones

COMPLETAR