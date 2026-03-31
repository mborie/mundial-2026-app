# 🏆 Mundial 2026 — Sistema de Pronósticos

Aplicación web interna para que un equipo de ~30 personas haga pronósticos/apuestas sobre los partidos del Mundial de Fútbol 2026.

## Arquitectura

### Stack elegido: Flask + SQLite3 puro

**¿Por qué Flask?** Es el balance perfecto entre simplicidad y capacidad real. Streamlit es demasiado limitado para multi-usuario con auth y admin. FastAPI requeriría un frontend separado. Flask con Jinja2 templates da una solución full-stack en un solo proceso.

**¿Por qué NO Google Colab?** Colab es para notebooks, no web apps. No ofrece servidor persistente, no tiene URL pública estable, no soporta multi-usuario real, y se desconecta después de inactividad.

**¿Por qué SQLite3 puro (sin ORM)?** Para ~30 usuarios, SQLite es más que suficiente. Sin ORM se eliminan dependencias externas, la app funciona con solo Flask instalado. Migrar a PostgreSQL es cambiar una línea de conexión.

### Dependencias mínimas
- **Flask** — framework web
- **Werkzeug** — hashing de contraseñas (incluido con Flask)
- **requests** — llamadas a API de fútbol (solo si se usa sincronización automática)
- **python-dotenv** — variables de entorno
- **gunicorn** — servidor de producción

## Estructura del Proyecto

```
mundial-2026/
├── app.py              # App principal con todas las rutas
├── database.py         # Capa de datos (SQLite3 puro)
├── api_service.py      # Abstracción de API de fútbol
├── seed.py             # Datos de ejemplo
├── config.py           # (opcional, todo está en app.py)
├── requirements.txt
├── .env.example
├── Procfile            # Para deploy en Render/Railway
├── mundial2026.db      # Base de datos (se crea automática)
├── static/
│   └── css/
│       └── style.css   # Tema dark corporate
└── templates/
    ├── base.html
    ├── dashboard.html
    ├── matches.html
    ├── ranking.html
    ├── user_detail.html
    ├── special_predictions.html
    ├── auth/
    │   ├── login.html
    │   └── register.html
    └── admin/
        ├── dashboard.html
        ├── users.html
        ├── bets.html
        ├── sync.html
        ├── manual_results.html
        └── config.html
```

## Instalación y Ejecución Local

```bash
# 1. Clonar o copiar el proyecto
cd mundial-2026

# 2. Crear entorno virtual (recomendado)
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus valores (especialmente SECRET_KEY)

# 5. Ejecutar la app (crea BD y admin automáticamente)
python app.py

# 6. Cargar datos de prueba (elige uno):

# Opción A: Champions League 2025/26 (RECOMENDADO para probar)
# Incluye partidos reales: octavos finalizados + cuartos próximos
# Usuarios con apuestas simuladas y ranking con puntos
python seed_champions.py

# Opción B: Mundial 2026 (datos ficticios para fase de grupos)
python seed.py

# 7. Abrir en el navegador
# http://localhost:5000
# Admin: admin / admin2026!
```

## Base de Datos

### Esquema

| Tabla | Descripción |
|-------|-------------|
| `users` | Usuarios con roles (user/admin), aprobación, contraseña hasheada |
| `teams` | Selecciones del mundial |
| `matches` | Partidos con fecha, equipos, marcador, estado |
| `bets` | Apuestas: 1 por usuario por partido |
| `special_predictions` | Campeón, subcampeón, goleador por usuario |
| `tournament_config` | Configuración dinámica (clave-valor) |
| `audit_log` | Log de acciones admin |

### Migración a PostgreSQL

Cambiar en `.env`:
```
DATABASE_URL=postgresql://user:pass@host:5432/mundial2026
```
Y adaptar `database.py` para usar `psycopg2` en lugar de `sqlite3`. La estructura de queries es compatible.

## Reglas del Juego

### Puntuación por partidos
- Acertar **local** (1) o **visita** (2): **1 punto**
- Acertar **empate** (X): **2 puntos** (más difícil de predecir)

### Puntuación especial
- **Campeón correcto**: 10 puntos
- **Subcampeón correcto**: 5 puntos (desafiante pero menos que campeón)
- **Goleador correcto**: 7 puntos (acertar 1 jugador entre cientos)

### Bloqueo de apuestas
- Se pueden modificar hasta **10 minutos** antes del inicio del partido
- Después quedan bloqueadas automáticamente
- Pronósticos especiales se cierran antes del inicio del Mundial (configurable)

### Desempates (en orden)
1. Mayor cantidad de **empates acertados** (más difícil de predecir)
2. Mayor cantidad de **aciertos totales**
3. Mejor **porcentaje de acierto**
4. **Registro más antiguo** (quien apostó primero)

## Integración con API de Fútbol

### Proveedor: football-data.org
- Free tier: 10 requests/minuto
- Registro gratuito: https://www.football-data.org/client/register

### Configuración
```env
FOOTBALL_API_KEY=tu_api_key
```

### Capa de abstracción
`api_service.py` define una interfaz con `NormalizedTeam` y `NormalizedMatch`. Para cambiar de proveedor:

1. Crear nueva clase (ej: `APIFootballProvider`)
2. Implementar `fetch_teams()`, `fetch_matches()`, `fetch_match_results()`
3. Registrar en `get_provider()`

### Modo manual
Sin API key, todo funciona con carga manual desde el panel admin. Esto es útil si:
- La API del Mundial 2026 aún no tiene datos
- Prefieres control total
- No quieres depender de un servicio externo

## Seguridad

- **Contraseñas**: Hash con Werkzeug (`pbkdf2:sha256`). NUNCA se almacenan en texto plano.
- **Reset de contraseña**: El admin puede resetear desde el panel → Admin → Usuarios → 🔑
- **Sesiones**: Flask sessions con cookie firmada (SECRET_KEY)
- **Validación**: Inputs validados en servidor
- **CSRF**: Protegido implícitamente por Flask sessions
- **Admin**: Decorador `@admin_required` en todas las rutas sensibles

## Guía de Despliegue

### Opción 1: Render.com (Recomendada)
**Pros**: Free tier, deploy automático desde Git, HTTPS incluido.
**Contras**: Se duerme tras 15 min de inactividad en free tier.

```bash
# 1. Subir a GitHub
git init && git add . && git commit -m "init"
git remote add origin <tu-repo>
git push origin main

# 2. En render.com:
# - New > Web Service > Connect repo
# - Build: pip install -r requirements.txt
# - Start: gunicorn app:app
# - Agregar variables de entorno desde .env
```

### Opción 2: Railway.app
**Pros**: Free tier generoso, auto-deploy, fácil.
**Contras**: Límite de horas mensuales en free.

### Opción 3: VPS (DigitalOcean, Linode)
**Pros**: Control total, siempre encendido, $5/mes.
**Contras**: Requiere configurar servidor.

```bash
# En el VPS:
sudo apt update && sudo apt install python3-pip python3-venv nginx
cd /opt/mundial-2026
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
gunicorn app:app --bind 127.0.0.1:5000 --workers 2 --daemon
# Configurar nginx como reverse proxy
```

### Opción 4: Servidor interno de la empresa
Si tienen un servidor Linux interno, es la opción más simple y privada.

## Mejoras Futuras (v2)

- **Notificaciones**: Email/Slack cuando se publican resultados
- **Marcador exacto**: Predecir score exacto para puntos bonus
- **Ranking por jornada**: Ver quién fue el mejor de cada ronda
- **Exportar a Excel**: Descargar ranking y apuestas en .xlsx
- **Cron automático**: Sincronizar resultados cada 15 minutos durante partidos
- **Recuperación de contraseña**: Email de reset (requiere SMTP)
- **Login con Google Workspace**: OAuth2 para SSO corporativo
- **Modo oscuro/claro**: Toggle de tema
- **Estadísticas avanzadas**: Gráficos de rendimiento por grupo/fase
- **Pool de dinero**: Gestión de pot real con montos
