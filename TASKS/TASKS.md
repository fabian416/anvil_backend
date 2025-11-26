# MVP de autenticación Privy - Instrucciones de desarrollo

## CONTEXTO
Tengo un proyecto frontend que requiere la integración de la autenticación de usuarios con el sistema Anvil. Hemos elegido a Privy como nuestro proveedor de autenticación para gestionar el inicio de sesión de los usuarios, la conexión a la billetera y la gestión de sesiones.

## TAREA
Diseñar e implementar un MVP (Producto Mínimo Viable) completo para la autenticación de usuarios utilizando Privy en la aplicación frontend. Esto debe incluir:

2. **Componentes de la interfaz de usuario de autenticación**
- Interfaz de inicio de sesión/registro
- Sección de perfil/cuenta de usuario
- Funcionalidad de cierre de sesión
- Estados de carga y error
- Diseño adaptable para dispositivos móviles y de escritorio

3. **Flujo de autenticación**
- Rutas protegidas que requieren autenticación
- Lógica de redirección (usuarios desconectados → inicio de sesión, usuarios conectados → panel de control)
- Persistencia de la sesión tras las actualizaciones de página
- Gestión adecuada de errores en intentos fallidos de autenticación

4. **Gestión de estados**
- Estado de autenticación del usuario
- Acceso a los datos del perfil del usuario
- Comprobaciones del estado de autenticación en toda la aplicación

## FORMATO
Estructure la implementación de la siguiente manera:

2. **Estructura de componentes**
- Componentes de autenticación (inicio de sesión, perfil, etc.)
- Envoltorio/componente de ruta protegida
- Componentes de diseño con renderizado condicional basado en el estado de autenticación

3. **Puntos de integración**
- Mostrar dónde y cómo integrar la autenticación en la estructura de la aplicación existente
- Patrones de integración de API para Solicitudes autenticadas (si corresponde)

4. **Documentación**
- Breves instrucciones de configuración
- Cómo usar los componentes de autenticación
- Explicación de las variables de entorno

## RESTRICCIONES
- Usar patrones modernos de React (ganchos, componentes funcionales, ARQUITECTURA CON HEXAGONAL)
- Seguir el estilo y la estructura del código del proyecto existente
- Mantener la implementación simple y centrada en el alcance del MVP
- Garantizar la compatibilidad con dispositivos móviles
- Incluir los tipos de TypeScript adecuados si el proyecto utiliza TypeScript
- Priorizar las mejores prácticas de seguridad (almacenamiento seguro de tokens, gestión adecuada de sesiones)
- Hacer que el flujo de autenticación sea intuitivo y fácil de usar
- Asegurarse de que el código esté listo para producción y bien comentado

## REQUISITOS TÉCNICOS
- Framework: [Especificar: React, Next.js, Vite, etc.]
- Estilo: [Especificar: Tailwind CSS, componentes con estilo, módulos CSS, etc.]
- TypeScript: [Sí/No]
- Gestión de estado: [Si corresponde: Redux, Zustand, Context API, etc.]

## ENTREGABLES
1. Todos los archivos de componentes necesarios
2. Código de configuración e instalación
3. Ejemplos de integración
4. Documentación básica/README
5. Plantilla de variables de entorno