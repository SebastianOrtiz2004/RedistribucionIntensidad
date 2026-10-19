import tkinter as tk
from tkinter import filedialog
from PIL import Image

ancho = 0
alto = 0

canal_rojo = []
canal_verde = []
canal_azul = []

vista_rojo = None
vista_verde = None
vista_azul = None
vista_original = None
vista_resultante = None


def formato_uint8(valor):
    numero = int(valor + 0.5)

    if numero < 0:
        numero = 0
    if numero > 255:
        numero = 255

    return numero


def crear_matriz(filas, columnas):
    matriz = []
    for f in range(filas):
        matriz.append(bytearray(columnas))
    return matriz


def obtener_histograma(matriz, filas, columnas):
    histograma = [0] * 256

    for f in range(filas):
        for c in range(columnas):
            intensidad = matriz[f][c]
            histograma[intensidad] = histograma[intensidad] + 1

    return histograma


def redistribuir_intensidad(matriz, filas, columnas, porcentaje):
    if porcentaje <= 0:
        nueva_matriz = crear_matriz(filas, columnas)
        for f in range(filas):
            for c in range(columnas):
                nueva_matriz[f][c] = matriz[f][c]
        return nueva_matriz

    factor = porcentaje / 100.0
    total_pixeles = filas * columnas

    grupos = [[] for _ in range(256)]
    for f in range(filas):
        f_arr = f - 1 if f > 0 else f
        f_aba = f + 1 if f < filas - 1 else f
        fila_act = matriz[f]
        fila_arr = matriz[f_arr]
        fila_aba = matriz[f_aba]
        for c in range(columnas):
            c_izq = c - 1 if c > 0 else c
            c_der = c + 1 if c < columnas - 1 else c
            vecinos = fila_arr[c] + fila_aba[c] + fila_act[c_izq] + fila_act[c_der]
            grupos[fila_act[c]].append((vecinos, f, c))

    for nivel in range(256):
        if len(grupos[nivel]) > 1:
            grupos[nivel].sort()

    hist_original = [len(grupos[i]) for i in range(256)]
    maximo_pico = max(hist_original)
    cuota_ideal = total_pixeles / 256.0

    techo = maximo_pico - factor * (maximo_pico - cuota_ideal)

    hist_objetivo = [0.0] * 256
    exceso_total = 0.0

    for i in range(256):
        if hist_original[i] > techo:
            exceso_total += (hist_original[i] - techo)
            hist_objetivo[i] = techo
        else:
            hist_objetivo[i] = float(hist_original[i])

    while exceso_total > 0.001:
        niveles_deficit = [i for i in range(256) if hist_objetivo[i] < techo - 0.001]
        if not niveles_deficit:
            break
        reparto = exceso_total / len(niveles_deficit)
        exceso_total = 0.0
        for i in niveles_deficit:
            hist_objetivo[i] += reparto
            if hist_objetivo[i] > techo:
                exceso_total += (hist_objetivo[i] - techo)
                hist_objetivo[i] = techo

    cuotas_enteras = [int(hist_objetivo[i]) for i in range(256)]
    faltante = total_pixeles - sum(cuotas_enteras)
    for i in range(faltante):
        cuotas_enteras[i % 256] += 1

    nueva_matriz = crear_matriz(filas, columnas)
    nivel_destino = 0
    puesto_en_nivel = 0

    for nivel_orig in range(256):
        for _, f, c in grupos[nivel_orig]:
            while nivel_destino < 255 and puesto_en_nivel >= cuotas_enteras[nivel_destino]:
                nivel_destino += 1
                puesto_en_nivel = 0

            nueva_matriz[f][c] = nivel_destino
            puesto_en_nivel += 1

    return nueva_matriz

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

    maximo_conteo = 1
    for nivel in range(256):
        if histograma[nivel] > maximo_conteo:
            maximo_conteo = histograma[nivel]

    lienzo.create_rectangle(x_inicio, 20, x_inicio + ancho_grafica, y_base, fill="#121212", outline="")

    for f_y in (0.25, 0.50, 0.75):
        pos_y_grid = y_base - f_y * alto_grafica
        lienzo.create_line(x_inicio + 1, pos_y_grid, x_inicio + ancho_grafica - 1, pos_y_grid, fill="#232323")

    for nivel_grid in (50, 100, 150, 200):
        pos_x_grid = x_inicio + nivel_grid
        lienzo.create_line(pos_x_grid, 21, pos_x_grid, y_base - 1, fill="#232323")

    for nivel in range(256):
        cantidad = histograma[nivel]
        if cantidad > 0:
            pos_x = x_inicio + nivel
            altura = (cantidad / maximo_conteo) * alto_grafica
            pos_y = y_base - altura
            lienzo.create_line(pos_x, y_base, pos_x, pos_y, fill=color, width=1)

    lienzo.create_rectangle(x_inicio, 20, x_inicio + ancho_grafica, y_base, outline="#555555")

    lienzo.create_text(x_inicio, 10, text=f"Máximo: {maximo_conteo}", fill="#d0d0d0", anchor="w", font=("Arial", 8, "bold"))

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

    lienzo.create_rectangle(x_inicio, 20, x_inicio + ancho_grafica, y_base, fill="#121212", outline="")

    for f_y in (0.25, 0.50, 0.75):
        pos_y_grid = y_base - f_y * alto_grafica
        lienzo.create_line(x_inicio + 1, pos_y_grid, x_inicio + ancho_grafica - 1, pos_y_grid, fill="#232323")

    for nivel_grid in (50, 100, 150, 200):
        pos_x_grid = x_inicio + nivel_grid
        lienzo.create_line(pos_x_grid, 21, pos_x_grid, y_base - 1, fill="#232323")

    for nivel in range(255):
        x1 = x_inicio + (nivel / 255.0) * ancho_grafica
        x2 = x_inicio + ((nivel + 1) / 255.0) * ancho_grafica

        yb1 = y_base - (hist_b[nivel] / maximo_total) * alto_grafica
        yb2 = y_base - (hist_b[nivel + 1] / maximo_total) * alto_grafica
        lienzo.create_line(x1, yb1, x2, yb2, fill="#339af0", width=2)

        yg1 = y_base - (hist_g[nivel] / maximo_total) * alto_grafica
        yg2 = y_base - (hist_g[nivel + 1] / maximo_total) * alto_grafica
        lienzo.create_line(x1, yg1, x2, yg2, fill="#51cf66", width=2)

        yr1 = y_base - (hist_r[nivel] / maximo_total) * alto_grafica
        yr2 = y_base - (hist_r[nivel + 1] / maximo_total) * alto_grafica
        lienzo.create_line(x1, yr1, x2, yr2, fill="#ff6b6b", width=2)

    lienzo.create_rectangle(x_inicio, 20, x_inicio + ancho_grafica, y_base, outline="#555555")

    lienzo.create_text(x_inicio, 10, text=f"Espectro RGB (Máx: {maximo_total})", fill="#ffd43b", anchor="w", font=("Arial", 8, "bold"))

    lienzo.create_line(x_inicio + 25, y_base, x_inicio + 25, y_base + 3, fill="#666666")
    lienzo.create_text(x_inicio + 25, y_base + 11, text="400nm(B)", fill="#339af0", font=("Arial", 8))

    lienzo.create_line(x_inicio + 128, y_base, x_inicio + 128, y_base + 3, fill="#666666")
    lienzo.create_text(x_inicio + 128, y_base + 11, text="550nm(G)", fill="#51cf66", font=("Arial", 8))

    lienzo.create_line(x_inicio + 230, y_base, x_inicio + 230, y_base + 3, fill="#666666")
    lienzo.create_text(x_inicio + 230, y_base + 11, text="700nm(R)", fill="#ff6b6b", font=("Arial", 8))


def al_mover_barras(_=None):
    global vista_rojo, vista_verde, vista_azul, vista_resultante

    if alto == 0 or ancho == 0:
        return

    porcentaje_rojo = float(barra_rojo.get())
    porcentaje_verde = float(barra_verde.get())
    porcentaje_azul = float(barra_azul.get())

    rojo_nuevo = redistribuir_intensidad(canal_rojo, alto, ancho, porcentaje_rojo)
    verde_nuevo = redistribuir_intensidad(canal_verde, alto, ancho, porcentaje_verde)
    azul_nuevo = redistribuir_intensidad(canal_azul, alto, ancho, porcentaje_azul)

    vista_rojo = pasar_a_imagen(rojo_nuevo, rojo_nuevo, rojo_nuevo, alto, ancho)
    vista_verde = pasar_a_imagen(verde_nuevo, verde_nuevo, verde_nuevo, alto, ancho)
    vista_azul = pasar_a_imagen(azul_nuevo, azul_nuevo, azul_nuevo, alto, ancho)
    vista_resultante = pasar_a_imagen(rojo_nuevo, verde_nuevo, azul_nuevo, alto, ancho)

    cuadro_img_rojo.config(image=vista_rojo)
    cuadro_img_verde.config(image=vista_verde)
    cuadro_img_azul.config(image=vista_azul)
    cuadro_img_resultante.config(image=vista_resultante)

    hist_r = obtener_histograma(rojo_nuevo, alto, ancho)
    hist_g = obtener_histograma(verde_nuevo, alto, ancho)
    hist_b = obtener_histograma(azul_nuevo, alto, ancho)

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

    img_pil = Image.open(ruta).convert("RGB")
    ancho_original, alto_original = img_pil.size
    pixeles = img_pil.load()

    escala = max(1, max(ancho_original // 300, alto_original // 165))
    salto_x = escala
    salto_y = escala

    filas_r = []
    filas_g = []
    filas_b = []

    for f in range(0, alto_original, salto_y):
        fila_r = bytearray()
        fila_g = bytearray()
        fila_b = bytearray()

        f_fin = min(f + salto_y, alto_original)

        for c in range(0, ancho_original, salto_x):
            c_fin = min(c + salto_x, ancho_original)

            suma_r = 0
            suma_g = 0
            suma_b = 0
            total_vecinos = (f_fin - f) * (c_fin - c)

            for bf in range(f, f_fin):
                for bc in range(c, c_fin):
                    pr, pg, pb = pixeles[bc, bf][:3]
                    suma_r += pr
                    suma_g += pg
                    suma_b += pb

            fila_r.append(formato_uint8(suma_r / total_vecinos))
            fila_g.append(formato_uint8(suma_g / total_vecinos))
            fila_b.append(formato_uint8(suma_b / total_vecinos))

        filas_r.append(fila_r)
        filas_g.append(fila_g)
        filas_b.append(fila_b)

    alto = len(filas_r)
    ancho = len(filas_r[0])

    canal_rojo = filas_r
    canal_verde = filas_g
    canal_azul = filas_b

    vista_original = pasar_a_imagen(canal_rojo, canal_verde, canal_azul, alto, ancho)
    cuadro_img_original.config(image=vista_original)

    barra_rojo.set(0)
    barra_verde.set(0)
    barra_azul.set(0)
    al_mover_barras()


ventana = tk.Tk()
ventana.title("Procesamiento de Imágenes - Histogramas uint8 y Redistribución por Canal")
ventana.configure(bg="#1e1e1e")
ventana.geometry("1360x780")

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

panel_centro = tk.Frame(ventana, bg="#1e1e1e", pady=2, padx=10)
panel_centro.pack(fill=tk.BOTH, expand=True)

fila_canales = tk.Frame(panel_centro, bg="#1e1e1e")
fila_canales.pack(fill=tk.X, pady=1)

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

fila_inferior = tk.Frame(panel_centro, bg="#252525", pady=3, padx=8)
fila_inferior.pack(fill=tk.X, pady=3)

sub_original = tk.Frame(fila_inferior, bg="#252525", padx=10)
sub_original.pack(side=tk.LEFT, expand=True)
tk.Label(sub_original, text="Imagen Original", bg="#252525", fg="#ffd43b", font=("Arial", 9, "bold")).pack()
cuadro_img_original = tk.Label(sub_original, bg="black")
cuadro_img_original.pack(pady=1)

sub_resultante = tk.Frame(fila_inferior, bg="#252525", padx=10)
sub_resultante.pack(side=tk.LEFT, expand=True)
tk.Label(sub_resultante, text="Imagen Resultante (Redistribuida)", bg="#252525", fg="#00d2ff", font=("Arial", 9, "bold")).pack()
cuadro_img_resultante = tk.Label(sub_resultante, bg="black")
cuadro_img_resultante.pack(pady=1)

sub_espectro = tk.Frame(fila_inferior, bg="#252525", padx=10)
sub_espectro.pack(side=tk.LEFT, expand=True)
grafica_espectro = tk.Canvas(sub_espectro, width=300, height=145, bg="#141414")
grafica_espectro.pack(pady=1)

try:
    ventana.state("zoomed")
except Exception:
    pass

ventana.mainloop()