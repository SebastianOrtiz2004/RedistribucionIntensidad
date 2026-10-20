"""
Módulo de Interfaz Gráfica para Procesamiento de Imágenes y Redistribución de Intensidad.
Construye los controles interactivos, visualizaciones y llamadas a la lógica de procesamiento.
"""
import tkinter as tk
from tkinter import filedialog
from PIL import Image

from logica import (
    formato_uint8,
    crear_matriz,
    obtener_histograma,
    redistribuir_intensidad,
    extraer_canales_desde_imagen,
)

# Variables principales para guardar el tamaño y los canales de la imagen
ancho = 0
alto = 0

canal_rojo = []
canal_verde = []
canal_azul = []

# Variables para mostrar las imágenes en la ventana
vista_rojo = None
vista_verde = None
vista_azul = None
vista_original = None
vista_resultante = None

# Referencias a widgets dinámicos de la interfaz
ventana = None
cuadro_img_rojo = None
cuadro_img_verde = None
cuadro_img_azul = None
cuadro_img_original = None
cuadro_img_resultante = None
grafica_rojo = None
grafica_verde = None
grafica_azul = None
grafica_espectro = None
barra_rojo = None
barra_verde = None
barra_azul = None


# ------------------------------------------------------------------------------
# FUNCIONES PARA MOSTRAR LAS IMÁGENES Y GRÁFICAS EN LA VENTANA
# ------------------------------------------------------------------------------
def pasar_a_imagen(matriz_r, matriz_g, matriz_b, filas, columnas):
    imagen = tk.PhotoImage(width=columnas, height=filas)
    
    for f in range(filas):
        fila_colores = "{"
        for c in range(columnas):
            r = matriz_r[f][c]
            g = matriz_g[f][c]
            b = matriz_b[f][c]
            fila_colores = fila_colores + f"#{r:02x}{g:02x}{b:02x} "
        fila_colores = fila_colores + "}"
        imagen.put(fila_colores, to=(0, f))
        
    return imagen


def dibujar_histograma(lienzo, histograma, color="#339af0"):
    lienzo.delete("all")

    ancho_grafica = 256
    alto_grafica = 105
    x_inicio = 22
    y_base = 125

    # Buscamos la barra más alta para ajustar la escala del dibujo
    maximo_conteo = 1
    for nivel in range(256):
        if histograma[nivel] > maximo_conteo:
            maximo_conteo = histograma[nivel]

    # Fondo oscuro interno para el área de la gráfica
    lienzo.create_rectangle(x_inicio, 20, x_inicio + ancho_grafica, y_base, fill="#121212", outline="")

    # Líneas de cuadrícula sutiles horizontales (25%, 50%, 75%)
    for f_y in (0.25, 0.50, 0.75):
        pos_y_grid = y_base - f_y * alto_grafica
        lienzo.create_line(x_inicio + 1, pos_y_grid, x_inicio + ancho_grafica - 1, pos_y_grid, fill="#232323")

    # Líneas de cuadrícula sutiles verticales (50, 100, 150, 200)
    for nivel_grid in (50, 100, 150, 200):
        pos_x_grid = x_inicio + nivel_grid
        lienzo.create_line(pos_x_grid, 21, pos_x_grid, y_base - 1, fill="#232323")

    # Dibujamos las 256 barras del histograma (1 píxel exacto por cada nivel uint8)
    for nivel in range(256):
        cantidad = histograma[nivel]
        if cantidad > 0:
            pos_x = x_inicio + nivel
            altura = (cantidad / maximo_conteo) * alto_grafica
            pos_y = y_base - altura
            lienzo.create_line(pos_x, y_base, pos_x, pos_y, fill=color, width=1)

    # Recuadro perimetral nítido sobre las barras
    lienzo.create_rectangle(x_inicio, 20, x_inicio + ancho_grafica, y_base, outline="#555555")

    # Etiqueta superior con el valor pico
    lienzo.create_text(x_inicio, 10, text=f"Máximo: {maximo_conteo}", fill="#d0d0d0", anchor="w", font=("Arial", 8, "bold"))

    # Números y marcas (ticks) del eje X
    for nivel_x in [0, 50, 100, 150, 200, 255]:
        pos_x = x_inicio + nivel_x
        lienzo.create_line(pos_x, y_base, pos_x, y_base + 3, fill="#666666")
        lienzo.create_text(pos_x, y_base + 11, text=str(nivel_x), fill="#aaaaaa", font=("Arial", 8))


def dibujar_espectro(lienzo, hist_r, hist_g, hist_b):
    lienzo.delete("all")

    ancho_grafica = 256
    alto_grafica = 105
    x_inicio = 22
    y_base = 125

    maximo_total = 1
    for i in range(256):
        if hist_r[i] > maximo_total:
            maximo_total = hist_r[i]
        if hist_g[i] > maximo_total:
            maximo_total = hist_g[i]
        if hist_b[i] > maximo_total:
            maximo_total = hist_b[i]

    # Fondo oscuro interno
    lienzo.create_rectangle(x_inicio, 20, x_inicio + ancho_grafica, y_base, fill="#121212", outline="")

    # Líneas de cuadrícula sutiles
    for f_y in (0.25, 0.50, 0.75):
        pos_y_grid = y_base - f_y * alto_grafica
        lienzo.create_line(x_inicio + 1, pos_y_grid, x_inicio + ancho_grafica - 1, pos_y_grid, fill="#232323")

    for nivel_grid in (50, 100, 150, 200):
        pos_x_grid = x_inicio + nivel_grid
        lienzo.create_line(pos_x_grid, 21, pos_x_grid, y_base - 1, fill="#232323")

    # Curvas continuas del espectro (Azul, Verde y Rojo) con grosor de 2px para mayor nitidez
    for nivel in range(255):
        x1 = x_inicio + (nivel / 255.0) * ancho_grafica
        x2 = x_inicio + ((nivel + 1) / 255.0) * ancho_grafica

        # Azul
        yb1 = y_base - (hist_b[nivel] / maximo_total) * alto_grafica
        yb2 = y_base - (hist_b[nivel + 1] / maximo_total) * alto_grafica
        lienzo.create_line(x1, yb1, x2, yb2, fill="#339af0", width=2)

        # Verde
        yg1 = y_base - (hist_g[nivel] / maximo_total) * alto_grafica
        yg2 = y_base - (hist_g[nivel + 1] / maximo_total) * alto_grafica
        lienzo.create_line(x1, yg1, x2, yg2, fill="#51cf66", width=2)

        # Rojo
        yr1 = y_base - (hist_r[nivel] / maximo_total) * alto_grafica
        yr2 = y_base - (hist_r[nivel + 1] / maximo_total) * alto_grafica
        lienzo.create_line(x1, yr1, x2, yr2, fill="#ff6b6b", width=2)

    # Recuadro perimetral
    lienzo.create_rectangle(x_inicio, 20, x_inicio + ancho_grafica, y_base, outline="#555555")

    # Título superior
    lienzo.create_text(x_inicio, 10, text=f"Espectro RGB (Máx: {maximo_total})", fill="#ffd43b", anchor="w", font=("Arial", 8, "bold"))

    # Etiquetas de longitud de onda con ticks
    lienzo.create_line(x_inicio + 25, y_base, x_inicio + 25, y_base + 3, fill="#666666")
    lienzo.create_text(x_inicio + 25, y_base + 11, text="400nm(B)", fill="#339af0", font=("Arial", 8))

    lienzo.create_line(x_inicio + 128, y_base, x_inicio + 128, y_base + 3, fill="#666666")
    lienzo.create_text(x_inicio + 128, y_base + 11, text="550nm(G)", fill="#51cf66", font=("Arial", 8))

    lienzo.create_line(x_inicio + 230, y_base, x_inicio + 230, y_base + 3, fill="#666666")
    lienzo.create_text(x_inicio + 230, y_base + 11, text="700nm(R)", fill="#ff6b6b", font=("Arial", 8))


# ------------------------------------------------------------------------------
# EVENTOS DEL PROGRAMA (MOVER LAS BARRAS Y ABRIR IMAGEN)
# ------------------------------------------------------------------------------
def al_mover_barras(_=None):
    global vista_rojo, vista_verde, vista_azul, vista_resultante

    if alto == 0 or ancho == 0:
        return

    # Obtenemos el porcentaje individual de cada barra (0 a 100%)
    porcentaje_rojo = float(barra_rojo.get())
    porcentaje_verde = float(barra_verde.get())
    porcentaje_azul = float(barra_azul.get())

    # 1. Redistribuimos los niveles de intensidad en cada canal de forma independiente
    rojo_nuevo = redistribuir_intensidad(canal_rojo, alto, ancho, porcentaje_rojo)
    verde_nuevo = redistribuir_intensidad(canal_verde, alto, ancho, porcentaje_verde)
    azul_nuevo = redistribuir_intensidad(canal_azul, alto, ancho, porcentaje_azul)

    # 2. Creamos las vistas de cada canal en grises (como en MATLAB) y la resultante a color
    vista_rojo = pasar_a_imagen(rojo_nuevo, rojo_nuevo, rojo_nuevo, alto, ancho)
    vista_verde = pasar_a_imagen(verde_nuevo, verde_nuevo, verde_nuevo, alto, ancho)
    vista_azul = pasar_a_imagen(azul_nuevo, azul_nuevo, azul_nuevo, alto, ancho)
    vista_resultante = pasar_a_imagen(rojo_nuevo, verde_nuevo, azul_nuevo, alto, ancho)

    cuadro_img_rojo.config(image=vista_rojo)
    cuadro_img_verde.config(image=vista_verde)
    cuadro_img_azul.config(image=vista_azul)
    cuadro_img_resultante.config(image=vista_resultante)

    # 3. Calculamos los histogramas actualizados para cada canal redistribuido
    hist_r = obtener_histograma(rojo_nuevo, alto, ancho)
    hist_g = obtener_histograma(verde_nuevo, alto, ancho)
    hist_b = obtener_histograma(azul_nuevo, alto, ancho)

    # 4. Dibujamos los 3 histogramas temáticos y el espectro de luz
    dibujar_histograma(grafica_rojo, hist_r, color="#ff6b6b")
    dibujar_histograma(grafica_verde, hist_g, color="#51cf66")
    dibujar_histograma(grafica_azul, hist_b, color="#339af0")
    dibujar_espectro(grafica_espectro, hist_r, hist_g, hist_b)


def abrir_imagen():
    global ancho, alto, canal_rojo, canal_verde, canal_azul, vista_original

    ruta = filedialog.askopenfilename(
        title="Seleccionar una imagen (JPG, JPEG, PNG)",
        filetypes=[
            ("Imágenes (JPG, JPEG, PNG, etc.)", "*.jpg *.jpeg *.png *.bmp *.webp *.ppm *.pgm"),
            ("Archivos JPEG", "*.jpg *.jpeg"),
            ("Archivos PNG", "*.png"),
            ("Todos los archivos", "*.*")
        ]
    )
    if ruta == "":
        return

    # Usamos PIL únicamente para abrir cualquier formato (JPG, PNG, etc.) y asegurar modo RGB
    img_pil = Image.open(ruta)
    filas_r, filas_g, filas_b, alto, ancho = extraer_canales_desde_imagen(img_pil)

    canal_rojo = filas_r
    canal_verde = filas_g
    canal_azul = filas_b

    # Mostramos la imagen principal / original de referencia para comparar
    vista_original = pasar_a_imagen(canal_rojo, canal_verde, canal_azul, alto, ancho)
    cuadro_img_original.config(image=vista_original)

    # Reiniciamos las 3 barras individuales a 0%
    barra_rojo.set(0)
    barra_verde.set(0)
    barra_azul.set(0)
    al_mover_barras()


def reiniciar_barras():
    if alto > 0 and ancho > 0:
        barra_rojo.set(0)
        barra_verde.set(0)
        barra_azul.set(0)
        al_mover_barras()


# ------------------------------------------------------------------------------
# CONSTRUCCIÓN Y LANZAMIENTO DE LA VENTANA PRINCIPAL
# ------------------------------------------------------------------------------
def iniciar_interfaz():
    global ventana, cuadro_img_rojo, grafica_rojo, barra_rojo
    global cuadro_img_verde, grafica_verde, barra_verde
    global cuadro_img_azul, grafica_azul, barra_azul
    global cuadro_img_original, cuadro_img_resultante, grafica_espectro

    ventana = tk.Tk()
    ventana.title("Procesamiento de Imágenes - Histogramas uint8 y Redistribución por Canal")
    ventana.configure(bg="#1e1e1e")
    ventana.geometry("1360x780")

    # Parte superior: Botón para subir la imagen y reiniciar barras
    panel_arriba = tk.Frame(ventana, bg="#2d2d2d", pady=8, padx=10)
    panel_arriba.pack(fill=tk.X)

    boton_abrir = tk.Button(
        panel_arriba, text="Abrir Imagen (JPG / PNG)", command=abrir_imagen,
        bg="#007acc", fg="white", font=("Arial", 10, "bold")
    )
    boton_abrir.pack(side=tk.LEFT, padx=10)

    boton_reset = tk.Button(
        panel_arriba, text="Reiniciar Barras (0%)", command=reiniciar_barras,
        bg="#444444", fg="white", font=("Arial", 9)
    )
    boton_reset.pack(side=tk.LEFT, padx=5)

    tk.Label(
        panel_arriba, text="Formato uint8 (0 a 255) | Control individual de redistribución por canal | Comparativa Original vs Resultante",
        bg="#2d2d2d", fg="#4ec9b0", font=("Arial", 10, "bold")
    ).pack(side=tk.LEFT, padx=15)

    # Parte central optimizada para pantallas estándar
    panel_centro = tk.Frame(ventana, bg="#1e1e1e", pady=2, padx=10)
    panel_centro.pack(fill=tk.BOTH, expand=True)

    # ----------------- FILA SUPERIOR: CANALES R, G, B -----------------
    fila_canales = tk.Frame(panel_centro, bg="#1e1e1e")
    fila_canales.pack(fill=tk.X, pady=1)

    # Columna 1: Canal Rojo
    col_rojo = tk.Frame(fila_canales, bg="#1e1e1e", padx=8)
    col_rojo.pack(side=tk.LEFT, expand=True)
    tk.Label(col_rojo, text="Canal Rojo", bg="#1e1e1e", fg="#ff6b6b", font=("Arial", 9, "bold")).pack()
    cuadro_img_rojo = tk.Label(col_rojo, bg="black")
    cuadro_img_rojo.pack(pady=1)
    grafica_rojo = tk.Canvas(col_rojo, width=300, height=145, bg="#141414")
    grafica_rojo.pack(pady=1)
    barra_rojo = tk.Scale(
        col_rojo, from_=0, to=100, orient=tk.HORIZONTAL,
        bg="#252525", fg="#ff6b6b", highlightthickness=0,
        label="Redistribución Rojo (%):", font=("Arial", 8, "bold"),
        command=al_mover_barras
    )
    barra_rojo.pack(fill=tk.X, pady=1)

    # Columna 2: Canal Verde
    col_verde = tk.Frame(fila_canales, bg="#1e1e1e", padx=8)
    col_verde.pack(side=tk.LEFT, expand=True)
    tk.Label(col_verde, text="Canal Verde", bg="#1e1e1e", fg="#51cf66", font=("Arial", 9, "bold")).pack()
    cuadro_img_verde = tk.Label(col_verde, bg="black")
    cuadro_img_verde.pack(pady=1)
    grafica_verde = tk.Canvas(col_verde, width=300, height=145, bg="#141414")
    grafica_verde.pack(pady=1)
    barra_verde = tk.Scale(
        col_verde, from_=0, to=100, orient=tk.HORIZONTAL,
        bg="#252525", fg="#51cf66", highlightthickness=0,
        label="Redistribución Verde (%):", font=("Arial", 8, "bold"),
        command=al_mover_barras
    )
    barra_verde.pack(fill=tk.X, pady=1)

    # Columna 3: Canal Azul
    col_azul = tk.Frame(fila_canales, bg="#1e1e1e", padx=8)
    col_azul.pack(side=tk.LEFT, expand=True)
    tk.Label(col_azul, text="Canal Azul", bg="#1e1e1e", fg="#339af0", font=("Arial", 9, "bold")).pack()
    cuadro_img_azul = tk.Label(col_azul, bg="black")
    cuadro_img_azul.pack(pady=1)
    grafica_azul = tk.Canvas(col_azul, width=300, height=145, bg="#141414")
    grafica_azul.pack(pady=1)
    barra_azul = tk.Scale(
        col_azul, from_=0, to=100, orient=tk.HORIZONTAL,
        bg="#252525", fg="#339af0", highlightthickness=0,
        label="Redistribución Azul (%):", font=("Arial", 8, "bold"),
        command=al_mover_barras
    )
    barra_azul.pack(fill=tk.X, pady=1)

    # ----------------- FILA INFERIOR: COMPARATIVA Y ESPECTRO -----------------
    fila_inferior = tk.Frame(panel_centro, bg="#252525", pady=3, padx=8)
    fila_inferior.pack(fill=tk.X, pady=3)

    # Sección Original
    sub_original = tk.Frame(fila_inferior, bg="#252525", padx=10)
    sub_original.pack(side=tk.LEFT, expand=True)
    tk.Label(sub_original, text="Imagen Original", bg="#252525", fg="#ffd43b", font=("Arial", 9, "bold")).pack()
    cuadro_img_original = tk.Label(sub_original, bg="black")
    cuadro_img_original.pack(pady=1)

    # Sección Resultante
    sub_resultante = tk.Frame(fila_inferior, bg="#252525", padx=10)
    sub_resultante.pack(side=tk.LEFT, expand=True)
    tk.Label(sub_resultante, text="Imagen Resultante (Redistribuida)", bg="#252525", fg="#00d2ff", font=("Arial", 9, "bold")).pack()
    cuadro_img_resultante = tk.Label(sub_resultante, bg="black")
    cuadro_img_resultante.pack(pady=1)

    # Sección Espectro
    sub_espectro = tk.Frame(fila_inferior, bg="#252525", padx=10)
    sub_espectro.pack(side=tk.LEFT, expand=True)
    grafica_espectro = tk.Canvas(sub_espectro, width=300, height=145, bg="#141414")
    grafica_espectro.pack(pady=1)

    try:
        ventana.state("zoomed")
    except Exception:
        pass

    ventana.mainloop()


if __name__ == "__main__":
    iniciar_interfaz()
