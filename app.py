import streamlit as st
import cv2
import easyocr
import numpy as np

# Configuración de página móvil
st.set_page_config(page_title="Buscador de Bodega - Vision AI", layout="centered")

st.title("📦 Buscador Visual de Bodega")
st.caption("Apunta con la cámara para encontrar un producto o número de parte.")

# Cargar el motor de OCR en caché para que la app sea rápida
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
        # Convertir la foto tomada por la cámara a un formato manipulable por OpenCV
        bytes_data = foto_camara.getvalue()
        imagen_np = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
        
        # Guardar una copia temporal para EasyOCR
        cv2.imwrite("temp_frame.jpg", imagen_np)
        
        # Ejecutar la detección sobre la foto capturada
        resultados = reader.readtext("temp_frame.jpg")
        
        # Dibujar la barra de estado superior
        h_img, w_img, _ = imagen_np.shape
        cv2.rectangle(imagen_np, (0, 0), (w_img, 40), (60, 60, 60), -1)
        cv2.putText(imagen_np, "MODO BUSQUEDA ACTIVADO | ESCANEO EN TIEMPO REAL", (15, 26),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        
        encontrado = False
        
        # Procesar textos detectados
        for bbox, texto, probabilidad in resultados:
            pt1 = (int(bbox[0][0]), int(bbox[0][1]))
            pt2 = (int(bbox[2][0]), int(bbox[2][1]))
            
            # Limpieza y normalización para corregir la confusión común '0' / 'D'
            texto_limpio = texto.strip().replace(" ", "").upper()
            texto_norm = texto_limpio.replace("0", "D")
            busqueda_norm = parte_buscada.strip().replace(" ", "").upper().replace("0", "D")
            
            if busqueda_norm in texto_norm:
                encontrado = True
                
                # Resaltado verde intenso alrededor de la celda / producto
                cv2.rectangle(imagen_np, pt1, pt2, (0, 255, 0), 4)
                
                # Etiqueta destacada en negro con texto blanco
                mensaje = f" ENCONTRADO: {texto_limpio}"
                ancho_caja = max(280, int(len(mensaje) * 11))
                alto_caja = 30
                
                x1_caja, y1_caja = pt1[0], pt2[1] + 5
                x2_caja, y2_caja = x1_caja + ancho_caja, y1_caja + alto_caja
                
                cv2.rectangle(imagen_np, (x1_caja, y1_caja), (x2_caja, y2_caja), (15, 15, 15), -1)
                cv2.putText(imagen_np, mensaje, (x1_caja + 8, y1_caja + 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
            else:
                # Recuadro sutil rojo para los demás códigos detectados
                cv2.rectangle(imagen_np, pt1, pt2, (0, 0, 220), 1)
        
        # Convertir a RGB para renderizar en la web
        imagen_rgb = cv2.cvtColor(imagen_np, cv2.COLOR_BGR2RGB)
        
        # Feedback al usuario
        if encontrado:
            st.success(f"¡Producto '{parte_buscada}' localizado exitosamente!")
        else:
            st.warning(f"No se encontró el código '{parte_buscada}' en la toma. Intenta acercarte un poco más.")
            
        # Mostrar la imagen resultante con los recuadros de colores dibujados
        st.image(imagen_rgb, use_column_width=True)