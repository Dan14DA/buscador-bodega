import streamlit as st
import cv2
import easyocr
import numpy as np

# Configuración de página
st.set_page_config(page_title="Buscador de Bodega - Vision AI", layout="wide")

st.title("📦 Buscador Visual de Bodega")
st.caption("Modo optimizado y seguro para evitar caídas por memoria.")

# Cargar el motor de OCR con manejo de errores protegido
@st.cache_resource
def cargar_ocr():
    try:
        return easyocr.Reader(['es', 'en'], gpu=False, model_storage_directory='./modelos')
    except Exception as e:
        return None

reader = cargar_ocr()

col1, col2 = st.columns([1, 1])

with col1:
    parte_buscada = st.text_input("SKU o Número de Parte a buscar:", value="13J2237")
    
    # Usar únicamente subida de archivos (permite usar la cámara nativa del celular con zoom y evita el fallo de memoria de la webcam web)
    foto_cargada = st.file_uploader("Saca una foto con la cámara de tu celular y súbela aquí:", type=["jpg", "jpeg", "png"])

if foto_cargada and parte_buscada:
    with col2:
        if reader is None:
            st.error("Error al cargar el motor de IA. Reinicia la aplicación.")
        else:
            with st.spinner("Analizando imagen de forma segura..."):
                try:
                    # Leer la imagen de manera segura
                    bytes_data = foto_cargada.getvalue()
                    imagen_np = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
                    
                    if imagen_np is None:
                        st.error("No se pudo leer la imagen. Intenta con otra foto.")
                    else:
                        # Redimensionar ligeramente para aligerar el consumo de RAM
                        h_orig, w_orig = imagen_np.shape[:2]
                        if w_orig > 1200:
                            escala = 1200 / w_orig
                            imagen_np = cv2.resize(imagen_np, (1200, int(h_orig * escala)), interpolation=cv2.INTER_AREA)
                        
                        # Guardar temporalmente para procesar
                        cv2.imwrite("temp_frame.jpg", imagen_np)
                        resultados = reader.readtext("temp_frame.jpg")
                        
                        lista_leida = [res[1].strip() for res in resultados]
                        st.info(f"🔍 Textos detectados: {lista_leida}")
                        
                        h_img, w_img, _ = imagen_np.shape
                        cv2.rectangle(imagen_np, (0, 0), (w_img, 40), (60, 60, 60), -1)
                        cv2.putText(imagen_np, "ESCANEO COMPLETADO", (15, 28),
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
                                x2_caja, y2_caja = x1_caja + 300, y1_caja + 30
                                
                                cv2.rectangle(imagen_np, (x1_caja, y1_caja), (x2_caja, y2_caja), (15, 15, 15), -1)
                                cv2.putText(imagen_np, mensaje, (x1_caja + 8, y1_caja + 20),
                                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
                            else:
                                cv2.rectangle(imagen_np, pt1, pt2, (0, 0, 220), 1)
                        
                        imagen_rgb = cv2.cvtColor(imagen_np, cv2.COLOR_BGR2RGB)
                        
                        if encontrado:
                            st.success(f"¡Código '{parte_buscada}' localizado con éxito!")
                        else:
                            st.warning(f"No se halló coincidencia exacta para '{parte_buscada}'.")
                            
                        st.image(imagen_rgb, use_container_width=True)
                        
                except Exception as e:
                    st.error(f"Ocurrió un error al procesar la imagen: {e}")
