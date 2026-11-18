# Tpose

**Estudio de dibujo de gesto para Windows. Portátil, bilingüe y 100 % local.**

Tpose trabaja solo con **tus carpetas de fotos**. Tú eliges cuántas imágenes
quieres en cada bloque y cuánto tiempo va a durar cada una.

---

## Inicio rápido

1. Haz doble clic en **`Tpose.exe`**.
2. Pulsa **Añadir carpeta** y elige una carpeta con tus referencias.
3. Construye tu plan: por ejemplo, **10 imágenes × 5 min**, **5 × 2 min** y **2 × 10 s**.
4. Pulsa **Empezar a dibujar**.

No hace falta instalar Python ni tener conexión. Si Windows SmartScreen avisa por
ser un ejecutable sin firma, elige **Más información → Ejecutar de todas formas**.

La primera vez se crea una carpeta `datos` junto al programa. Ahí se guardan tus
carpetas, tu plan, tus ajustes y el historial. Para llevarte Tpose a otro equipo,
copia la carpeta completa.

---

## Qué puedes hacer

### Tus carpetas, siempre tuyas
- Añade una o varias carpetas a la vez, con JPG, PNG, WEBP, BMP, GIF o TIFF.
- Si eliges varias carpetas, sus imágenes se mezclan al azar.
- Las imágenes vistas no vuelven a salir durante las **3 sesiones siguientes**, salvo que no queden imágenes suficientes.
- Las rutas se guardan en `datos/config.json`; no hay que volver a elegirlas.
- Activa o desactiva cada carpeta con su marca.
- Elimínalas de la lista cuando quieras. **Las fotos originales no se borran.**

### Un plan de tiempos a tu medida
- Crea tantos bloques como necesites.
- Cada bloque tiene su **número de imágenes** y su **tiempo por imagen**.
- Ejemplo: `10 × 5 min` + `5 × 2 min` + `2 × 10 s`.
- Edita o elimina cualquier bloque en cualquier momento.
- El plan se guarda y se reutiliza en la siguiente sesión.

### Sesión
- **Con tiempo**: cambia de imagen al terminar el tiempo de cada bloque.
- **Sin tiempo**: avanzas tú cuando quieras.
- **Girar 90°**, **invertir horizontal**, **invertir vertical** y **blanco y negro** para la imagen actual desde la barra superior, con `R`, `H`, `V` y `B`.
- El nombre de la carpeta de la imagen actual aparece discretamente en la esquina inferior izquierda.
- **Aviso antes del final**: elige con el desplegable en qué segundo (de 5 en 5 hasta 30) empieza a sonar el timbre. El número del contador parpadea sincronizado con cada aviso.
- **Timbre cada 30 s**: opción para oír un aviso mientras avanza la sesión.
- **Orden de imágenes**: desplegable **Mezclar / Ordenado** para activar o detener la aleatoriedad.
- **Tema día / noche** con botones de sol y luna; el modo noche usa tonos fríos y guarda la preferencia.
- Blanco y negro, sonidos, mostrar/ocultar reloj, pantalla completa.
- Pausa, imagen anterior/siguiente y resumen al terminar.

### Historial
- Tiempo total, sesiones, imágenes y media.
- Gráfico de los últimos 7 días.
- **Borrar todo el historial** cuando quieras.
- **Exportar las estadísticas como imagen PNG** o como **Excel (.xlsx)**.
- Cada sesión muestra también la **lista de carpetas** utilizadas, además del número.
- En los bloques no hay límite de imágenes: si pides más de las disponibles, solo se avisa de que se repetirán.

### Español, English, 中文 y 日本語
Cambia el idioma desde la barra lateral, antes de empezar la sesión. Chino y japonés aparecen debajo de inglés y español respectivamente.

---

## Atajos de sesión

| Tecla | Acción |
|---|---|
| `Espacio` | Pausar / continuar |
| `←` / `→` | Imagen anterior / siguiente |
| `R` | Girar la imagen 90° |
| `H` / `V` | Invertir horizontal / vertical |
| `B` | Blanco y negro |
| `F` o `F11` | Pantalla completa |
| `S` | Silenciar / activar sonido |
| `Esc` | Salir de pantalla completa o terminar |

---

## Ejecutar desde el código

Requisitos: Python 3.10 o posterior con Tkinter y Pillow.

```bat
py -3 -m pip install -r requirements.txt
py -3 tpose.py
```

También puedes usar `Iniciar con Python.bat`. El ejecutable autónomo ya incluye
Python, Tkinter y Pillow.

## Estructura

```text
Tpose.exe               Ejecutable autónomo
tpose.py                Entrada del programa en Python
app/                    Código de interfaz, sesiones, historial y exportación
assets/                 Icono, sonidos y créditos
datos/                  Ajustes, rutas e historial (se crea al usar Tpose)
LEEME.md / LEEME.txt    Este archivo
```

---

## Créditos

Este programa nace de una conversación entre amigos (Pchans y clued), diseñada por dibujantes para todos. Uso libre, código libre. Siéntete libre de donar lo que desees.

---

## English quick guide

**Tpose** is a portable gesture-drawing studio for Windows that works with **your own
photo folders**. Add one or more folders, then build a session plan with as many blocks
as you like — for example `10 × 5 min`, `5 × 2 min` and `2 × 10 s`.

- Folders and plans are saved and can be removed at any time; your photos are never deleted.
- **Timed** or **untimed** sessions, with optional shuffling, grayscale, sounds and fullscreen.
- Rotate the current photo 90°, flip it horizontally/vertically or apply black & white
  with the toolbar buttons (or `R`, `H`, `V`, `B`).
- Choose when the warning bell starts (5–30 seconds, in 5-second steps) and optionally
  hear a bell every 30 seconds.
- History can be cleared, or exported as a **PNG** image or a real **.xlsx** workbook.
- Spanish, English, Chinese and Japanese interface.
- No installation, no account, no uploads.

Run from source with `py -3 tpose.py` (Python 3.10+, Pillow), or double-click
`Tpose.exe`.

Keyboard: `Space` pause, `←`/`→` change image, `R` rotate, `F`/`F11` fullscreen,
`S` mute, `Esc` exit fullscreen/end.

## Credits

This program was born from a conversation between friends (Pchans and clued), designed
by artists for everyone. Free to use, free code. Feel free to donate whatever you wish.
