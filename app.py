import streamlit as st
import easyocr
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Configuración de página móvil
st.set_page_config(page_title="Buscador de Bodega - Vision AI", layout="centered")

st.title("📦 Buscador Visual de Bodega")
st.caption("Apunta con la cámara para encontrar un producto o número de parte.")

# Cargar el motor de OCR en caché
@st.cache_resource
def cargar_ocr():
    return easyocr.Reader(['es', 'en'])

reader = cargar_ocr()

# 1. Entrada de texto para el número de parte o SKU a buscar
parte_buscada = st.text_input("Ingrese el SKU o Número de Parte a buscar:", value="13D2237")

# 2. Captura de la cámara del celular / navegador
foto_camara = st.camera_input("Toma una foto de la estantería o pasillo")

if foto_camara and parte_buscada:
    with st.spinner("Escaneando estantería..."):
        # Cargar la imagen usando PIL (Pillow) en lugar de OpenCV
        imagen_pil = Image.open(foto_camara).convert("RGB")
        imagen_np = np.array(imagen_pil)
        
        # Guardar temporalmente para EasyOCR
        imagen_pil.save("temp_frame.jpg")
        
        # Ejecutar la detección
        resultados = reader.readtext("temp_frame.jpg")
        
        # Preparar herramientas de dibujo con PIL
        draw = ImageDraw.Draw(imagen_pil)
        w_img, h_img = imagen_pil.size
        
        # Dibujar barra superior de estado
        draw.rectangle([0, 0, w_img, 40], fill=(60, 60, 60))
        draw.text((15, 12), "MODO BUSQUEDA ACTIVADO | ESCANEO EN TIEMPO REAL", fill=(255, 255, 255))
        
        encontrado = False
        
        for bbox, texto, probabilidad in resultados:
            pt1 = (int(bbox[0][0]), int(bbox[0][1]))
            pt2 = (int(bbox[2][0]), int(bbox[2][1]))
            
            # Limpieza y normalización de texto
            texto_limpio = texto.strip().replace(" ", "").upper()
            texto_norm = texto_limpio.replace("0", "D")
            busqueda_norm = parte_buscada.strip().replace(" ", "").upper().replace("0", "D")
            
            if busqueda_norm in texto_norm:
                encontrado = True
                # Rectángulo verde brillante alrededor del texto
                draw.rectangle([pt1, pt2], outline=(0, 255, 0), width=4)
                
                # Etiqueta inferior de confirmación
                mensaje = f" ENCONTRADO: {texto_limpio}"
                x1, y1 = pt1[0], pt2[1] + 5
                x2, y2 = x1 + 300, y1 + 25
                draw.rectangle([x1, y1, x2, y2], fill=(15, 15, 15))
                draw.text((x1 + 8, y1 + 5), mensaje, fill=(255, 255, 255))
            else:
                # Rectángulo rojo sutil para los demás
                draw.rectangle([pt1, pt2], outline=(0, 0, 220), width=1)
        
        # Feedback visual
        if encontrado:
            st.success(f"¡Producto '{parte_buscada}' localizado exitosamente!")
        else:
            st.warning(f"No se encontró el código '{parte_buscada}' en la toma. Intenta acercarte un poco más.")
            
        # Mostrar la imagen procesada
        st.image(imagen_pil, use_column_width=True)
