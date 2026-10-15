import tkinter as tk
from tkinter import filedialog
from PIL import Image

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


# ------------------------------------------------------------------------------
# 1. FUNCIONES PARA FORMATO uint8 (8 BITS SIN SIGNO: DE 0 A 255)
# ------------------------------------------------------------------------------
def formato_uint8(valor):
    # Redondeamos a número entero
    numero = int(valor + 0.5)
    
    # Aseguramos que esté en el rango de 8 bits (0 a 255)
    if numero < 0:
        numero = 0
    if numero > 255:
        numero = 255
        
    return numero


def crear_matriz(filas, columnas):
    # bytearray guarda números enteros de 8 bits (uint8: 0 a 255)
    matriz = []
    for f in range(filas):
        matriz.append(bytearray(columnas))
    return matriz


# ------------------------------------------------------------------------------
# 2. CÁLCULO DEL HISTOGRAMA (CONTEO DE PÍXELES POR NIVEL DE INTENSIDAD)
# ------------------------------------------------------------------------------
def obtener_histograma(matriz, filas, columnas):
    # Lista con 256 posiciones en cero (niveles del 0 al 255)
    histograma = [0] * 256

    for f in range(filas):
        for c in range(columnas):
            intensidad = matriz[f][c]
            histograma[intensidad] = histograma[intensidad] + 1

    return histograma


# ------------------------------------------------------------------------------
# 3. REDISTRIBUCIÓN DE NIVELES DE INTENSIDAD CON LA BARRA (SCROLLBAR)
# Lógica explicada por el docente:
# - Identificar los niveles de intensidad con mayor número de píxeles (picos).
# - Identificar los niveles que tienen menos píxeles o están vacíos (déficit).
# - Tomar los píxeles excedentes de los niveles más poblados y redistribuirlos
#   hacia los niveles con menor cantidad de píxeles según el porcentaje del scrollbar.
# - No elimina píxeles ni resta valores fijos arbitrarios.
# ------------------------------------------------------------------------------
def redistribuir_intensidad(matriz, filas, columnas, porcentaje):
    # Creamos la nueva matriz con los valores originales
    nueva_matriz = crear_matriz(filas, columnas)
    for f in range(filas):
        for c in range(columnas):
            nueva_matriz[f][c] = matriz[f][c]

    # Al 0% no se modifica ningún píxel (imagen original)
    if porcentaje <= 0:
        return nueva_matriz

    factor = porcentaje / 100.0
    total_pixeles = filas * columnas

    # 1. Agrupamos las coordenadas (fila, columna) por cada nivel de intensidad (0 a 255)
    grupos = []
    for nivel in range(256):
        grupos.append([])

    for f in range(filas):
        for c in range(columnas):
            intensidad = matriz[f][c]
            grupos[intensidad].append((f, c))

    # 2. Capacidad ideal equilibrada por nivel (total de píxeles repartido entre los 256 niveles)
    cuota_base = total_pixeles // 256
    residuo = total_pixeles % 256
    cuota = [cuota_base + (1 if i < residuo else 0) for i in range(256)]

    # 3. IDENTIFICAR NIVELES CON MAYOR NÚMERO DE PÍXELES (picos con exceso)
    # y tomar los píxeles sobrantes en función del porcentaje de la barra
    pixeles_a_mover = []
    for nivel in range(256):
        cantidad_actual = len(grupos[nivel])
        if cantidad_actual > cuota[nivel]:
            exceso = cantidad_actual - cuota[nivel]
            cantidad_mover = int(exceso * factor)
            # Tomamos esos píxeles del nivel saturado
            for i in range(cantidad_mover):
                pixeles_a_mover.append(grupos[nivel][cantidad_actual - 1 - i])

    # 4. IDENTIFICAR NIVELES CON MENOS PÍXELES (déficit / espacio disponible)
    # y preparar los nuevos niveles a los que se transferirán los píxeles
    destinos_disponibles = []
    for nivel in range(256):
        cantidad_actual = len(grupos[nivel])
        if cantidad_actual < cuota[nivel]:
            deficit = cuota[nivel] - cantidad_actual
            cantidad_recibir = int(deficit * factor)
            for _ in range(cantidad_recibir):
                destinos_disponibles.append(nivel)

    # 5. Ajuste fino de redondeo para que coincida exactamente la cantidad de píxeles a transferir
    total_a_mover = len(pixeles_a_mover)
    if len(destinos_disponibles) < total_a_mover:
        while len(destinos_disponibles) < total_a_mover:
            for nivel in range(256):
                if len(grupos[nivel]) < cuota[nivel]:
                    destinos_disponibles.append(nivel)
                    if len(destinos_disponibles) == total_a_mover:
                        break
    elif len(destinos_disponibles) > total_a_mover:
        destinos_disponibles = destinos_disponibles[:total_a_mover]

    # 6. REDISTRIBUIR: a los píxeles tomados de los niveles con mayor concentración
    # se les asigna su nuevo nivel de intensidad en los niveles con menos píxeles
    for i in range(total_a_mover):
        f, c = pixeles_a_mover[i]
        nueva_matriz[f][c] = destinos_disponibles[i]

    return nueva_matriz


# ------------------------------------------------------------------------------
# 4. FUNCIONES PARA MOSTRAR LAS IMÁGENES Y GRÁFICAS EN LA VENTANA
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


def dibujar_histograma(lienzo, histograma):
    lienzo.delete("all")

    ancho_grafica = 220
    alto_grafica = 150
    x_inicio = 38
    y_base = 175

    # Buscamos la barra más alta para ajustar la escala del dibujo
    maximo_conteo = 1
    for nivel in range(256):
        if histograma[nivel] > maximo_conteo:
            maximo_conteo = histograma[nivel]

    # Recuadro blanco estilo MATLAB
    lienzo.create_rectangle(x_inicio, 25, x_inicio + ancho_grafica, y_base, outline="white")
    lienzo.create_text(x_inicio, 12, text=f"Máximo: {maximo_conteo}", fill="white", anchor="w", font=("Arial", 8))

    # Números del eje X (niveles de intensidad de 0 a 250)
    for nivel_x in [0, 50, 100, 150, 200, 250]:
        pos_x = x_inicio + (nivel_x / 255.0) * ancho_grafica
        lienzo.create_text(pos_x, y_base + 12, text=str(nivel_x), fill="white", font=("Arial", 8))

    # Dibujamos las 256 barras del histograma
    for nivel in range(256):
        cantidad = histograma[nivel]
        if cantidad > 0:
            pos_x = x_inicio + (nivel / 255.0) * ancho_grafica
            altura = (cantidad / maximo_conteo) * alto_grafica
            pos_y = y_base - altura
            lienzo.create_line(pos_x, y_base, pos_x, pos_y, fill="#2b7bba", width=2)


def dibujar_espectro(lienzo, hist_r, hist_g, hist_b):
    lienzo.delete("all")

    ancho_grafica = 220
    alto_grafica = 140
    x_inicio = 38
    y_base = 165

    lienzo.create_text(x_inicio, 12, text="Espectro RGB (400nm - 700nm)", fill="yellow", anchor="w", font=("Arial", 8))
    lienzo.create_rectangle(x_inicio, 25, x_inicio + ancho_grafica, y_base, outline="white")

    maximo_total = 1
    for i in range(256):
        if hist_r[i] > maximo_total:
            maximo_total = hist_r[i]
        if hist_g[i] > maximo_total:
            maximo_total = hist_g[i]
        if hist_b[i] > maximo_total:
            maximo_total = hist_b[i]

    # Líneas del espectro para Azul (450nm), Verde (550nm) y Rojo (650nm)
    for nivel in range(255):
        x1 = x_inicio + (nivel / 255.0) * ancho_grafica
        x2 = x_inicio + ((nivel + 1) / 255.0) * ancho_grafica

        # Azul
        yb1 = y_base - (hist_b[nivel] / maximo_total) * alto_grafica
        yb2 = y_base - (hist_b[nivel + 1] / maximo_total) * alto_grafica
        lienzo.create_line(x1, yb1, x2, yb2, fill="#339af0")

        # Verde
        yg1 = y_base - (hist_g[nivel] / maximo_total) * alto_grafica
        yg2 = y_base - (hist_g[nivel + 1] / maximo_total) * alto_grafica
        lienzo.create_line(x1, yg1, x2, yg2, fill="#51cf66")

        # Rojo
        yr1 = y_base - (hist_r[nivel] / maximo_total) * alto_grafica
        yr2 = y_base - (hist_r[nivel + 1] / maximo_total) * alto_grafica
        lienzo.create_line(x1, yr1, x2, yr2, fill="#ff6b6b")

    lienzo.create_text(x_inicio + 15, y_base + 15, text="400nm(B)", fill="#339af0", font=("Arial", 7))
    lienzo.create_text(x_inicio + 110, y_base + 15, text="550nm(G)", fill="#51cf66", font=("Arial", 7))
    lienzo.create_text(x_inicio + 200, y_base + 15, text="700nm(R)", fill="#ff6b6b", font=("Arial", 7))


# ------------------------------------------------------------------------------
# 5. EVENTOS DEL PROGRAMA (MOVER LAS BARRAS Y ABRIR IMAGEN)
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

    # 4. Dibujamos los 3 histogramas y el espectro de luz
    dibujar_histograma(grafica_rojo, hist_r)
    dibujar_histograma(grafica_verde, hist_g)
    dibujar_histograma(grafica_azul, hist_b)
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
    img_pil = Image.open(ruta).convert("RGB")
    ancho_original, alto_original = img_pil.size
    pixeles = img_pil.load()

    # Reducimos la escala si la foto es muy grande para que procese rápido al mover las barras
    salto_x = max(1, ancho_original // 200)
    salto_y = max(1, alto_original // 150)

    filas_r = []
    filas_g = []
    filas_b = []

    for f in range(0, alto_original, salto_y):
        fila_r = bytearray()
        fila_g = bytearray()
        fila_b = bytearray()
        for c in range(0, ancho_original, salto_x):
            r, g, b = pixeles[c, f][:3]

            fila_r.append(formato_uint8(r))
            fila_g.append(formato_uint8(g))
            fila_b.append(formato_uint8(b))

        filas_r.append(fila_r)
        filas_g.append(fila_g)
        filas_b.append(fila_b)

    alto = len(filas_r)
    ancho = len(filas_r[0])

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


# ------------------------------------------------------------------------------
# 6. DISEÑO DE LA VENTANA
# ------------------------------------------------------------------------------
ventana = tk.Tk()
ventana.title("Procesamiento de Imágenes - Histogramas uint8 y Redistribución por Canal")
ventana.configure(bg="#1e1e1e")
ventana.geometry("1400x780")

# Parte superior: Botón para subir la imagen y reiniciar barras
panel_arriba = tk.Frame(ventana, bg="#2d2d2d", pady=8, padx=10)
panel_arriba.pack(fill=tk.X)

boton_abrir = tk.Button(
    panel_arriba, text="Abrir Imagen (JPG / PNG)", command=abrir_imagen,
    bg="#007acc", fg="white", font=("Arial", 10, "bold")
)
boton_abrir.pack(side=tk.LEFT, padx=10)

def reiniciar_barras():
    if alto > 0 and ancho > 0:
        barra_rojo.set(0)
        barra_verde.set(0)
        barra_azul.set(0)
        al_mover_barras()

boton_reset = tk.Button(
    panel_arriba, text="Reiniciar Barras (0%)", command=reiniciar_barras,
    bg="#444444", fg="white", font=("Arial", 9)
)
boton_reset.pack(side=tk.LEFT, padx=5)

tk.Label(
    panel_arriba, text="Formato uint8 (0 a 255) | Control individual de redistribución por canal | Comparativa Original vs Resultante",
    bg="#2d2d2d", fg="#4ec9b0", font=("Arial", 10, "bold")
).pack(side=tk.LEFT, padx=15)

# Parte central: Las 4 columnas
panel_centro = tk.Frame(ventana, bg="#1e1e1e", pady=8)
panel_centro.pack(fill=tk.BOTH, expand=True)

# Columna 1: Canal Rojo (Imagen + Histograma + Barra individual)
col_rojo = tk.Frame(panel_centro, bg="#1e1e1e", padx=6)
col_rojo.grid(row=0, column=0, sticky="n")
tk.Label(col_rojo, text="Canal Rojo", bg="#1e1e1e", fg="#ff6b6b", font=("Arial", 11, "bold")).pack()
cuadro_img_rojo = tk.Label(col_rojo, bg="black", width=200, height=150)
cuadro_img_rojo.pack(pady=4)
grafica_rojo = tk.Canvas(col_rojo, width=270, height=180, bg="#141414")
grafica_rojo.pack(pady=4)
barra_rojo = tk.Scale(
    col_rojo, from_=0, to=100, orient=tk.HORIZONTAL,
    bg="#252525", fg="#ff6b6b", highlightthickness=0,
    label="Redistribución Rojo (%):", font=("Arial", 8, "bold"),
    command=al_mover_barras
)
barra_rojo.pack(fill=tk.X, pady=4)

# Columna 2: Canal Verde (Imagen + Histograma + Barra individual)
col_verde = tk.Frame(panel_centro, bg="#1e1e1e", padx=6)
col_verde.grid(row=0, column=1, sticky="n")
tk.Label(col_verde, text="Canal Verde", bg="#1e1e1e", fg="#51cf66", font=("Arial", 11, "bold")).pack()
cuadro_img_verde = tk.Label(col_verde, bg="black", width=200, height=150)
cuadro_img_verde.pack(pady=4)
grafica_verde = tk.Canvas(col_verde, width=270, height=180, bg="#141414")
grafica_verde.pack(pady=4)
barra_verde = tk.Scale(
    col_verde, from_=0, to=100, orient=tk.HORIZONTAL,
    bg="#252525", fg="#51cf66", highlightthickness=0,
    label="Redistribución Verde (%):", font=("Arial", 8, "bold"),
    command=al_mover_barras
)
barra_verde.pack(fill=tk.X, pady=4)

# Columna 3: Canal Azul (Imagen + Histograma + Barra individual)
col_azul = tk.Frame(panel_centro, bg="#1e1e1e", padx=6)
col_azul.grid(row=0, column=2, sticky="n")
tk.Label(col_azul, text="Canal Azul", bg="#1e1e1e", fg="#339af0", font=("Arial", 11, "bold")).pack()
cuadro_img_azul = tk.Label(col_azul, bg="black", width=200, height=150)
cuadro_img_azul.pack(pady=4)
grafica_azul = tk.Canvas(col_azul, width=270, height=180, bg="#141414")
grafica_azul.pack(pady=4)
barra_azul = tk.Scale(
    col_azul, from_=0, to=100, orient=tk.HORIZONTAL,
    bg="#252525", fg="#339af0", highlightthickness=0,
    label="Redistribución Azul (%):", font=("Arial", 8, "bold"),
    command=al_mover_barras
)
barra_azul.pack(fill=tk.X, pady=4)

# Columna 4: Comparativa de Imagen (Original vs Resultante) + Espectro
col_color = tk.Frame(panel_centro, bg="#1e1e1e", padx=6)
col_color.grid(row=0, column=3, sticky="n")
tk.Label(col_color, text="Comparativa RGB y Espectro", bg="#1e1e1e", fg="#ffd43b", font=("Arial", 11, "bold")).pack()

# Panel horizontal para mostrar Imagen Original y Resultante lado a lado
panel_comparativa = tk.Frame(col_color, bg="#1e1e1e")
panel_comparativa.pack(pady=4)

sub_original = tk.Frame(panel_comparativa, bg="#1e1e1e", padx=4)
sub_original.pack(side=tk.LEFT)
tk.Label(sub_original, text="Original", bg="#1e1e1e", fg="#aaaaaa", font=("Arial", 9, "bold")).pack()
cuadro_img_original = tk.Label(sub_original, bg="black", width=140, height=140)
cuadro_img_original.pack()

sub_resultante = tk.Frame(panel_comparativa, bg="#1e1e1e", padx=4)
sub_resultante.pack(side=tk.LEFT)
tk.Label(sub_resultante, text="Resultante", bg="#1e1e1e", fg="#00d2ff", font=("Arial", 9, "bold")).pack()
cuadro_img_resultante = tk.Label(sub_resultante, bg="black", width=140, height=140)
cuadro_img_resultante.pack()

# Gráfica del Espectro
grafica_espectro = tk.Canvas(col_color, width=280, height=180, bg="#141414")
grafica_espectro.pack(pady=4)

tk.Label(
    col_color, text="Comparación en tiempo real:\nOriginal (izquierda) vs Redistribuida (derecha)",
    bg="#1e1e1e", fg="#cccccc", font=("Arial", 8), justify=tk.CENTER
).pack(pady=2)

ventana.mainloop()