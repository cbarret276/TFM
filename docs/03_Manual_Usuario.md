# 03 - Manual de Usuario

Este manual describe el funcionamiento del dashboard **MalwareBI**, diseñado para el análisis visual de amenazas de malware a partir de datos enriquecidos desde fuentes abiertas. La herramienta permite una exploración interactiva a distintos niveles: general, táctico, geográfico y detallado.

---

## 🧭 Navegación y estructura

El dashboard tiene navegación lateral multipágina y un sistema de filtrado común en la parte superior. La interfaz se adapta automáticamente a escritorio, tablet o móvil.

---

## 🔍 Filtros globales

Ubicados en la parte superior del dashboard, los filtros globales permiten refinar la información visible en todas las secciones. Son persistentes entre páginas.

### Campos disponibles:

- **Rango de fechas**: filtra las muestras según su fecha de detección (`created`).
- **Familias de malware**: permite seleccionar una o varias (`family`).

Y adicionalmente en la página de Análisis:
- **Tipo de fichero**: filtra por extensión o clasificación (`file_type`).
- **País de origen**: basado en geolocalización IP (`origin_country`).
- **Score**: nivel de peligrosidad asignado a la muestra (0–10).

Los filtros se aplican dinámicamente a todas las gráficas y tablas. Al seleccionar un nuevo valor, los datos se recargan automáticamente con los resultados correspondientes.

---

## 📊 Secciones y visualizaciones

### 🧭 Panorámica

#### KPIs
- Muestran el total de muestras, familias, países y técnicas detectadas.

#### Histogramas diarios y horarios
- Evolución de la actividad maliciosa.
- Se pueden usar para detectar picos anómalos o campañas masivas.

#### Top familias
- Gráfico de barras horizontales con porcentaje y frecuencia de aparición.

#### Treemap de tácticas
- Representación jerárquica por táctica MITRE.
- Permite identificar qué tipos de acciones (persistence, discovery, etc.) predominan.

---

### 🧠 MITRE ATT&CK

#### Sankey Táctica → Técnica
- Flujo visual de las tácticas a las técnicas observadas en las muestras.
- Ej: de “Persistence” a “T1547.001”.

#### Sankey Técnica → Familia
- Muestra qué familias usan cada técnica observada.

#### Heatmap MITRE
- Matriz de frecuencia de técnicas por táctica.
- Cuanto más oscuro el color, mayor número de apariciones.

Cada nodo es clicable y puede estar enlazado a descripciones oficiales de MITRE.

---

### 🌍 Geolocalización

#### Mapa coroplético
- Visualiza los países desde los que se ha detectado actividad maliciosa.
- Cuanto más oscuro, mayor número de muestras asociadas.

#### Distintas vistas
- Distribución de malware.
- Distribución de técnicas.
- Distribución de Indicadores de Compromiso (IoC)

---

### 🧩 Indicadores (IOCs)

#### Wordcloud de tags
- Representación visual del conjunto de dominios.
- Tamaño proporcional a frecuencia de aparición.

#### Tablas de IPs
- Listado de IOCs activos observados en los análisis.
- Exportables y con ordenación interactiva.

####  técnicas
- Muestra para las IPs maliciosas su reputación, el uso asociado y su localización en países.


#### Mapa de indicadores
- Muestra distribución geográfica de las IPs maliciosas

---

### 📑 Análisis detallado

#### Tabla interactiva
- Tabla tipo DataTable con scroll horizontal y vertical.
- Ordenable y filtrable desde los encabezados de columna.
- Columnas como:
  - `id`, `score`, `file_size`, `tags`, `ttp`, `origin_country`, `created`, etc.

#### Modal de detalle
- Se abre al hacer clic en una fila.
- Muestra:
  - Todos los campos relevantes con estilo limpio.
  - Enlaces automáticos:
    - ID → `https://tria.ge/<id>`
    - Técnicas → `https://attack.mitre.org/techniques/<TXXXX>`

---

## 💡 Buenas prácticas de uso

- Comienza con filtros por familia y score alto para revisar amenazas críticas.
- Usa la vista MITRE para analizar la cobertura táctica de una campaña.
- Revisa la geolocalización para ver qué países están afectados por cada familia.
- Utiliza la tabla detallada para obtener todos los metadatos e IOCs exportables.

---

## 🎨 Accesibilidad y experiencia de usuario

- **Cambio de tema**: alternancia claro/oscuro con persistencia.
- **Responsive**: optimizado para móvil, tablet y escritorio.
- **Tooltips**: ayuda contextual en todos los gráficos y badges.

---

## 📐 Principios de visualización aplicados

El diseño de MalwareBI sigue las buenas prácticas propuestas por Shneiderman y Wilke:

- **Overview first**: vista panorámica general al entrar.
- **Zoom and filter**: navegación temática con filtros segmentados.
- **Details on demand**: acceso detallado mediante clic en fila o badge.

---

Este manual está dirigido a perfiles analistas, técnicos y gestores de ciberseguridad que necesiten identificar patrones de ataque, campañas, vectores y familias activas.
