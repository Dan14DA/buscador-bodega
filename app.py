import streamlit as st
import cv2
import easyocr
import numpy as np

# Configuración de página en modo ancho (wide) para aprovechar toda la pantalla
st.set_page_config(page_title="Buscador de Bodega - Vision AI", layout="wide")

st.title("📦 Buscador Visual de Bodega")
st.caption("Modo de captura rápida optimizado para dispositivos móviles.")

# Cargar el motor de OCR en caché
@st.cache_resource
def cargar_ocr():
    return easyocr.Reader(['es', 'en'])

reader = cargar_ocr()

# Usar columnas para organizar mejor la pantalla en celulares y tablets
col1, col2 = st.columns([1, 1])

with col1:
    parte_buscada = st.text_input("SKU o Número de Parte a buscar:", value="13J2237")
    foto_camara = st.camera_input("Apunta y toma la foto de la estantería")

if foto_camara and parte_buscada:
    with col2:
        with st.spinner("Escaneando estantería..."):
            bytes_data = foto_camara.getvalue()
            imagen_np = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
            
            cv2.imwrite("temp_frame.jpg", imagen_np)
            resultados = reader.readtext("temp_frame.jpg")
            
            # Mostrar textos detectados para control
            lista_leida = [res[1].strip() for res in resultados]
            st.info(f"🔍 Textos detectados: {lista_leida}")
            
            h_img, w_img, _ = imagen_np.shape
            cv2.rectangle(imagen_np, (0, 0), (w_img, 40), (60, 60, 60), -1)
            cv2.putText(imagen_np, "MODO ESCANEO ACTIVO", (15, 26),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)
            
            encontrado = False
            
            for bbox, texto, probabilidad in resultados:
                pt1 = (int(bbox[0][0]), int(bbox[0][1]))
                pt2 = (int(bbox[2][0]), int(bbox[2][1]))
                
                texto_limpio = texto.strip().replace(" ", "").upper()
                texto_norm = texto_limpio.replace("0", "D").replace("I", "J")
                busqueda_norm = parte_buscada.strip().replace(" ", "").upper().replace("0", "D").replace("I", "J")
                
                if busqueda_norm in texto_norm or any(p in texto_norm for p in busqueda_norm.split('-')):
                    encontrado = True
                    cv2.rectangle(imagen_np, pt1, pt2, (0, 255, 0), 4)
                    
                    mensaje = f" ENCONTRADO: {texto_limpio}"
                    x1_caja, y1_caja = pt1[0], pt2[1] + 5
                    x2_caja, y2_caja = x1_caja + 350, y1_caja + 35
                    
                    cv2.rectangle(imagen_np, (x1_caja, y1_caja), (x2_caja, y2_caja), (15, 15, 15), -1)
                    cv2.putText(imagen_np, mensaje, (x1_caja + 8, y1_caja + 24),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)
                else:
                    cv2.rectangle(imagen_np, pt1, pt2, (0, 0, 220), 1)
            
            imagen_rgb = cv2.cvtColor(imagen_np, cv2.COLOR_BGR2RGB)
            
            if encontrado:
                st.success(f"¡Código '{parte_buscada}' localizado con éxito!")
            else:
                st.warning(f"No se halló coincidencia exacta para '{parte_buscada}'.")
                
            # Mostrar la imagen ampliada utilizando todo el ancho disponible
            st.image(imagen_rgb, use_container_width=True)
