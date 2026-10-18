import streamlit as st
import cv2
import easyocr
import numpy as np

# Configuración de página móvil
st.set_page_config(page_title="Buscador de Bodega - Vision AI", layout="centered")

st.title("📦 Buscador Visual de Bodega")
st.caption("Apunta con la cámara para encontrar un producto o número de parte.")

# Cargar el motor de OCR en caché para mayor velocidad
@st.cache_resource
def cargar_ocr():
    return easyocr.Reader(['es', 'en'])

reader = cargar_ocr()

# 1. Entrada de texto para el número de parte o SKU a buscar
parte_buscada = st.text_input("Ingrese el SKU o Número de Parte a buscar:", value="13J2237")

# 2. Captura de la cámara del celular / navegador
foto_camara = st.camera_input("Toma una foto de la estantería o pasillo")

if foto_camara and parte_buscada:
    with st.spinner("Escaneando estantería..."):
        # Convertir la foto tomada por la cámara a formato OpenCV
        bytes_data = foto_camara.getvalue()
        imagen_np = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
        
        # Guardar copia temporal para EasyOCR
        cv2.imwrite("temp_frame.jpg", imagen_np)
        
        # Ejecutar la detección
        resultados = reader.readtext("temp_frame.jpg")
        
        # --- NUEVO: Mostrar lista de textos detectados para depurar ---
        lista_leida = [res[1].strip() for res in resultados]
        st.info(f"🔍 Textos leídos por la IA en esta foto: {lista_leida}")
        
        # Dibujar barra superior de estado
        h_img, w_img, _ = imagen_np.shape
        cv2.rectangle(imagen_np, (0, 0), (w_img, 40), (60, 60, 60), -1)
        cv2.putText(imagen_np, "MODO BUSQUEDA ACTIVADO", (15, 26),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        
        encontrado = False
        
        # Procesar textos detectados
        for bbox, texto, probabilidad in resultados:
            pt1 = (int(bbox[0][0]), int(bbox[0][1]))
            pt2 = (int(bbox[2][0]), int(bbox[2][1]))
            
            # Limpieza y normalización flexible (manejo de confusiones comunes)
            texto_limpio = texto.strip().replace(" ", "").upper()
            texto_norm = texto_limpio.replace("0", "D").replace("I", "J")
            busqueda_norm = parte_buscada.strip().replace(" ", "").upper().replace("0", "D").replace("I", "J")
            
            # Coincidencia flexible (si contiene parte del texto buscado)
            if busqueda_norm in texto_norm or any(p in texto_norm for p in busqueda_norm.split('-')):
                encontrado = True
                
                # Resaltado VERDE brillante cuando hace match
                cv2.rectangle(imagen_np, pt1, pt2, (0, 255, 0), 4)
                
                # Etiqueta destacada en negro con texto blanco
                mensaje = f" ENCONTRADO: {texto_limpio}"
                x1_caja, y1_caja = pt1[0], pt2[1] + 5
                x2_caja, y2_caja = x1_caja + 320, y1_caja + 30
                
                cv2.rectangle(imagen_np, (x1_caja, y1_caja), (x2_caja, y2_caja), (15, 15, 15), -1)
                cv2.putText(imagen_np, mensaje, (x1_caja + 8, y1_caja + 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
            else:
                # Recuadro rojo sutil para los demás
                cv2.rectangle(imagen_np, pt1, pt2, (0, 0, 220), 1)
        
        # Convertir a RGB para renderizar en Streamlit
        imagen_rgb = cv2.cvtColor(imagen_np, cv2.COLOR_BGR2RGB)
        
        # Feedback al usuario
        if encontrado:
            st.success(f"¡Producto '{parte_buscada}' localizado exitosamente en la imagen!")
        else:
            st.warning(f"No hubo coincidencia exacta con '{parte_buscada}'. Revisa arriba los textos que leyó la IA.")
            
        # Mostrar la imagen resultante
        st.image(imagen_rgb, use_column_width=True)
