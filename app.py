import streamlit as st
import cv2
import easyocr
import numpy as np

# Configuración de página en modo ancho
st.set_page_config(page_title="Buscador de Bodega - Vision AI", layout="wide")

st.title("📦 Buscador Visual de Bodega")
st.caption("Optimizado para lectura a distancia y escaneo rápido.")

# Cargar el motor de OCR en caché
@st.cache_resource
def cargar_ocr():
    return easyocr.Reader(['es', 'en'])

reader = cargar_ocr()

col1, col2 = st.columns([1, 1])

with col1:
    parte_buscada = st.text_input("SKU o Número de Parte a buscar:", value="13J2237")
    
    # Pestañas para elegir cómo capturar la foto (permite usar la cámara nativa con zoom si prefieres)
    metodo_captura = st.radio("Método de captura:", ["Cámara Web", "Subir foto (Cámara nativa con Zoom)"])
    
    foto_cargada = None
    if metodo_captura == "Cámara Web":
        foto_cargada = st.camera_input("Apunta a la estantería")
    else:
        foto_cargada = st.file_uploader("Saca una foto con la app de tu celular y súbela aquí:", type=["jpg", "jpeg", "png"])

if foto_cargada and parte_buscada:
    with col2:
        with st.spinner("Procesando y ampliando imagen a distancia..."):
            # Leer imagen
            bytes_data = foto_cargada.getvalue()
            imagen_np = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
            
            # --- MEJORA CLAVE: Ampliar la imagen (Upscaling x2) ---
            # Esto agranda los textos lejanos para que EasyOCR los detecte sin estar muy cerca
            h_orig, w_orig = imagen_np.shape[:2]
            imagen_ampliada = cv2.resize(imagen_np, (w_orig * 2, h_orig * 2), interpolation=cv2.INTER_CUBIC)
            
            cv2.imwrite("temp_frame.jpg", imagen_ampliada)
            resultados = reader.readtext("temp_frame.jpg")
            
            # Escalar las coordenadas de vuelta al tamaño original para dibujar bien el recuadro
            lista_leida = [res[1].strip() for res in resultados]
            st.info(f"🔍 Textos detectados a distancia: {lista_leida}")
            
            # Dibujar barra superior
            cv2.rectangle(imagen_ampliada, (0, 0), (w_orig * 2, 70), (60, 60, 60), -1)
            cv2.putText(imagen_ampliada, "MODO ESCANEO A DISTANCIA ACTIVO", (30, 45),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2, cv2.LINE_AA)
            
            encontrado = False
            
            for bbox, texto, probabilidad in resultados:
                # Ajustar coordenadas por el zoom aplicado (dividir entre 2)
                pt1 = (int(bbox[0][0] / 2), int(bbox[0][1] / 2))
                pt2 = (int(bbox[2][0] / 2), int(bbox[2][1] / 2))
                
                texto_limpio = texto.strip().replace(" ", "").upper()
                texto_norm = texto_limpio.replace("0", "D").replace("I", "J")
                busqueda_norm = parte_buscada.strip().replace(" ", "").upper().replace("0", "D").replace("I", "J")
                
                if busqueda_norm in texto_norm or any(p in texto_norm for p in busqueda_norm.split('-')):
                    encontrado = True
                    # Recuadro verde más grueso para identificarlo fácil
                    cv2.rectangle(imagen_np, pt1, pt2, (0, 255, 0), 6)
                    
                    mensaje = f" ENCONTRADO: {texto_limpio}"
                    x1_caja, y1_caja = pt1[0], pt2[1] + 10
                    x2_caja, y2_caja = x1_caja + 400, y1_caja + 50
                    
                    cv2.rectangle(imagen_np, (x1_caja, y1_caja), (x2_caja, y2_caja), (15, 15, 15), -1)
                    cv2.putText(imagen_np, mensaje, (x1_caja + 12, y1_caja + 35),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
                else:
                    cv2.rectangle(imagen_np, pt1, pt2, (0, 0, 220), 1)
            
            imagen_rgb = cv2.cvtColor(imagen_np, cv2.COLOR_BGR2RGB)
            
            if encontrado:
                st.success(f"¡Código '{parte_buscada}' localizado a distancia con éxito!")
            else:
                st.warning(f"No se halló el código '{parte_buscada}'. Prueba usando la opción de 'Subir foto' usando el zoom de la cámara nativa de tu teléfono.")
                
            st.image(imagen_rgb, use_container_width=True)
