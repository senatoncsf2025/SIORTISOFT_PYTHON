# SIORTISOFT
Sistema de control de acceso institucional desarrollado en **Django**.

Este sistema permite registrar, consultar y gestionar el ingreso y salida de personas dentro de una institución, separando claramente los **flujos administrativos** de los **flujos operativos de vigilancia**.

---

# 1. Arquitectura del sistema

El sistema está dividido en **dos áreas principales**:

## 1.1 Área administrativa
Accedida por usuarios con rol:

admin

Permite:

- CRUD completo de personas
- consulta masiva de registros
- reportes por módulo
- administración de usuarios
- acceso opcional al panel operativo

Panel administrativo:

/index2/

---

## 1.2 Área operativa de vigilancia
Accedida por usuarios con rol:

vigilante

Permite:

- consultar personas por cédula
- registrar ingreso o salida
- registrar nuevas personas
- registrar vehículos
- registrar computadores

Panel operativo:

/dashboard/

---

# 2. Principio de diseño del sistema

Una decisión arquitectónica clave:

**Todas las personas del sistema viven en la misma tabla `Usuario`.**

Esto permite que el administrador pueda realizar:

- consultas globales
- reportes masivos
- filtrado por subcategoría

En lugar de tener tablas separadas para estudiantes, visitantes, etc.

---

# 3. Modelo de datos

## 3.1 Usuario

Modelo principal del sistema.

Contiene tanto:

- usuarios que pueden iniciar sesión
- personas registradas para control de acceso

Campos principales:

nombre  
apellido  
cedula  
email  
telefono  
direccion  
tipo_usuario  
rol  
subrol  
activo  
registrado_por  
created_at  
updated_at  

### Rol

Define el tipo de usuario del sistema.

Valores:

admin  
vigilante  
persona  

Reglas:

| Rol | Puede iniciar sesión |
|----|----|
| admin | Sí |
| vigilante | Sí |
| persona | No |

---

### Subrol

Clasifica las personas registradas dentro del sistema.

Valores actuales:

oficinas  
enfermeria  
parqueadero  
visitantes  
acudientes  
docentes  
estudiantes  
personal  
vigilantes  

Los **subroles representan los módulos del sistema**.

---

## 3.2 Vehiculo

Relación uno a uno con usuario.

Campos:

usuario  
placa  
marca  
modelo  
color  

Se crea solo si el usuario registra que trae vehículo.

---

## 3.3 Computador

Relación uno a uno con usuario.

Campos:

usuario  
serial  

Se crea solo si el usuario registra que trae computador.

---

## 3.4 Movimiento

Registra eventos operativos.

Campos:

usuario  
tipo  
observaciones  
registrado_por  
fecha  

Tipos:

ingreso  
salida  

Cada vez que alguien entra o sale, se crea un movimiento.

---

# 4. Estructura del proyecto

Estructura aproximada del proyecto:

project/
│  
├── manage.py  
│  
├── project/  
│   ├── settings.py  
│   ├── urls.py  
│  
├── myApp/  
│   ├── models.py  
│   ├── views.py  
│   ├── admin.py  
│   ├── urls.py  
│  
├── templates/  
│   │  
│   ├── layouts/  
│   │    └── app.html  
│   │  
│   ├── auth/  
│   │    ├── login.html  
│   │    └── register.html  
│   │  
│   ├── secciones/  
│   │    ├── acudientes.html  
│   │    ├── docentes.html  
│   │    ├── estudiantes.html  
│   │    ├── enfermeria.html  
│   │    ├── oficinas.html  
│   │    ├── parqueadero.html  
│   │    ├── personal.html  
│   │    ├── visitantes.html  
│   │    ├── vigilantes.html  
│   │  
│   │    └── partials/  
│   │         ├── consulta.html  
│   │         └── registro.html  
│   │  
│   ├── crud/  
│   │    ├── acudientes/  
│   │    ├── docentes/  
│   │    ├── estudiantes/  
│   │    ├── enfermeria/  
│   │    ├── oficinas/  
│   │    ├── parqueadero/  
│   │    ├── personal/  
│   │    ├── visitantes/  
│   │    └── vigilantes/  
│   │  
│   ├── dashboard.html  
│   ├── index.html  
│   └── index2.html  
│  
└── static/  
     ├── css/  
     └── js/  

---

# 5. Navegación del sistema

## 5.1 Página principal

Ruta:

/

Template:

index.html

Muestra:

- botones de login
- botones de registro

---

## 5.2 Login

Ruta:

/login/

Vista:

login_view

Autentica con:

email  
password  

Redirección automática:

| Rol | Redirección |
|----|----|
| admin | /index2/ |
| vigilante | /dashboard/ |

---

## 5.3 Registro

Ruta:

/register/

Solo permite crear:

admin  
vigilante  

No registra estudiantes ni visitantes.

---

# 6. Paneles del sistema

## 6.1 Panel Admin

Ruta:

/index2/

Vista:

index2

Acceso:

solo admin

Desde aquí se accede a:

/crud/*

---

## 6.2 Dashboard Vigilante

Ruta:

/dashboard/

Vista:

dashboard_view

Acceso:

vigilante  
admin  

Contiene tarjetas que redirigen a cada módulo.

---

# 7. Secciones operativas

Rutas:

/secciones/acudientes/  
/secciones/docentes/  
/secciones/estudiantes/  
/secciones/enfermeria/  
/secciones/oficinas/  
/secciones/parqueadero/  
/secciones/personal/  
/secciones/visitantes/  
/secciones/vigilantes/  

Vista usada:

seccion_view

Cada sección tiene:

consulta  
registro  

---

# 8. CRUD administrativo

Rutas:

/crud/<modulo>/  
/crud/<modulo>/create/  
/crud/<modulo>/<id>/edit/  
/crud/<modulo>/reporte/  

Ejemplo:

/crud/acudientes/  
/crud/acudientes/create/  
/crud/acudientes/12/edit/  
/crud/acudientes/reporte/  

Acceso:

solo admin

---

# 9. Formularios de sección

Cada sección reutiliza dos parciales.

## Consulta

Campos:

cedula  
tipo_movimiento  
observaciones  

Permite:

- registrar ingreso
- registrar salida

---

## Registro

Campos:

nombre  
apellido  
cedula  
telefono  
email  
direccion  

Opcionales:

Vehículo

placa  
marca  
modelo  
color  

Computador

serial  

---

# 10. Flujo operativo típico

Ejemplo:

1. vigilante abre dashboard  
2. entra a sección visitantes  
3. busca cédula  

Si existe:

registrar ingreso

Si no existe:

registrar persona

Luego:

crear movimiento

---

# 11. Seguridad

La seguridad se implementa en las vistas.

Ejemplo:

if request.user.rol != "admin":

Esto evita que vigilantes accedan al CRUD.

---

# 12. Reglas de desarrollo

Para continuar el proyecto:

### No crear tablas separadas para personas

Todo debe seguir dentro de:

Usuario

---

### No reintroducir modelo Registro

El sistema usa:

Movimiento

---

### No permitir login a personas

Solo:

admin  
vigilante  

---

# 13. Próximos pasos recomendados

1. Implementar guardado real en seccion_view  
2. Conectar formularios a Movimiento  
3. Implementar CRUD completo  
4. Crear reportes  
5. Añadir filtros avanzados  
6. Agregar auditoría de accesos  
7. Implementar control de horarios  

---

# 14. Stack tecnológico

Backend:

Django  
Python  

Frontend:

HTML  
Bootstrap  
Javascript  

Base de datos:

SQLite (desarrollo)  
PostgreSQL recomendado para producción  

---

# 15. Objetivo final del sistema

SIORTISOFT busca centralizar el control de acceso institucional permitiendo:

- registro de personas
- registro de entradas y salidas
- administración masiva
- reportes
- trazabilidad de movimientos

Todo dentro de una arquitectura centralizada basada en Django.