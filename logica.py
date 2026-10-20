"""
Módulo de Lógica Pura para Procesamiento de Imágenes y Redistribución de Intensidad.
Contiene algoritmos matemáticos y procesamiento de matrices uint8, independiente de la interfaz gráfica.
"""
from PIL import Image

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
# - Recorta los picos que superan el techo y rellena los valles sin que ningún
#   nivel rebase el tope (aplanado total al 100%).
# - Ordena por vecindad local y brillo para mantener la imagen suave y sin ruido.
# ------------------------------------------------------------------------------
def redistribuir_intensidad(matriz, filas, columnas, porcentaje):
    # Al 0% no se modifica ningún píxel (imagen original intacta)
    if porcentaje <= 0:
        nueva_matriz = crear_matriz(filas, columnas)
        for f in range(filas):
            for c in range(columnas):
                nueva_matriz[f][c] = matriz[f][c]
        return nueva_matriz

    factor = porcentaje / 100.0
    total_pixeles = filas * columnas

    # 1. Agrupamos las coordenadas (f, c) por su nivel original (0 a 255)
    # Usamos la suma de los 4 vecinos inmediatos para desempatar píxeles del mismo
    # tono de forma suave, evitando tanto el ruido como las franjas de color
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

    # 2. Histograma original y cuota plana ideal
    hist_original = [len(grupos[i]) for i in range(256)]
    maximo_pico = max(hist_original)
    cuota_ideal = total_pixeles / 256.0

    # 3. Techo de corte según el porcentaje del scrollbar
    techo = maximo_pico - factor * (maximo_pico - cuota_ideal)

    # 4. Recorte de picos que superan el techo
    hist_objetivo = [0.0] * 256
    exceso_total = 0.0

    for i in range(256):
        if hist_original[i] > techo:
            exceso_total += (hist_original[i] - techo)
            hist_objetivo[i] = techo
        else:
            hist_objetivo[i] = float(hist_original[i])

    # 5. Redistribución del exceso en los niveles con déficit (valles)
    # Si un nivel con déficit alcanza el techo, se topa en el techo y el resto
    # del exceso sigue rellenando los niveles más vacíos (aplanado perfecto)
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

    # 6. Cuotas enteras exactas garantizando que la suma sea igual a total_pixeles
    cuotas_enteras = [int(hist_objetivo[i]) for i in range(256)]
    faltante = total_pixeles - sum(cuotas_enteras)
    for i in range(faltante):
        cuotas_enteras[i % 256] += 1

    # 7. Asignación ordenada a la nueva matriz respetando las cuotas exactas
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


# ------------------------------------------------------------------------------
# 4. EXTRACCIÓN Y MUESTREO DE CANALES (BOX AVERAGING)
# ------------------------------------------------------------------------------
def extraer_canales_desde_imagen(img_pil, max_ancho=300, max_alto=165):
    """
    Extrae los canales R, G y B como matrices de bytearray (uint8)
    aplicando Box Averaging y manteniendo la proporción de la imagen.
    """
    img_rgb = img_pil.convert("RGB")
    ancho_original, alto_original = img_rgb.size
    pixeles = img_rgb.load()

    # Reducimos la escala manteniendo la proporción exacta (aspect ratio)
    # y aumentando la resolución a ~300px x 165px para máxima nitidez y definición
    escala = max(1, max(ancho_original // max_ancho, alto_original // max_alto))
    salto_x = escala
    salto_y = escala

    filas_r = []
    filas_g = []
    filas_b = []

    for f in range(0, alto_original, salto_y):
        fila_r = bytearray()
        fila_g = bytearray()
        fila_b = bytearray()

        # Límites del bloque vertical
        f_fin = min(f + salto_y, alto_original)

        for c in range(0, ancho_original, salto_x):
            # Límites del bloque horizontal
            c_fin = min(c + salto_x, ancho_original)

            # Promediamos los píxeles vecinos del bloque (Box Averaging)
            # para eliminar los dientes de sierra y el pixelado sin librerías complejas
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

    return filas_r, filas_g, filas_b, alto, ancho


if __name__ == "__main__":
    from interfaz import iniciar_interfaz
    iniciar_interfaz()
