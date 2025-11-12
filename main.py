from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import PyPDF2
import io
import google.generativeai as genai
import os
import json

app = FastAPI(title="Profesor Ayuni - Sistema Autónomo")

# ==================== CONFIGURACIÓN ====================
# TU API KEY REAL DE GOOGLE AI STUDIO
GEMINI_API_KEY = "AIzaSyC5L47dAqWI-CgX0CMxdjtHV4SEbbX9y9k"
genai.configure(api_key=GEMINI_API_KEY)

# ==================== BIBLIOTECA DE PDFs ====================
# TUS IDs REALES DE GOOGLE DRIVE
BIBLIOTECA = {
    "fisica": "1qtIP2Ms9Op_XapFr9sCK2CvTz_kfj0k9",
    "civil": "11vF9zTQcrPQl3Yu4udxaHVLCxeRzWk71",
    "admin": "1pKchzTFLqmNdGIZznVtejFhItz9yY98y"
}

# ==================== USUARIOS ====================
USUARIOS = {
    "estudiante1": "clave123",
    "maria": "clave456",
    "profesor": "admin123",
    "luis": "password123"
}


# ==================== MODELOS ====================
class PreguntaRequest(BaseModel):
    usuario: str
    clave: str
    pregunta: str


class N8NAuthRequest(BaseModel):
    usuario: str
    clave: str


# ==================== ENDPOINTS PRINCIPALES ====================

@app.post("/preguntar")
async def preguntar_auto(request: PreguntaRequest):
    """Endpoint principal para preguntas de estudiantes"""
    print(f"🎓 Pregunta de {request.usuario}: {request.pregunta}")

    # 1. Autenticación
    if not autenticar_usuario(request.usuario, request.clave):
        return {"success": False, "error": "❌ Credenciales inválidas"}

    # 2. Seleccionar PDF automáticamente
    pdf_id = seleccionar_pdf_inteligente(request.pregunta)

    # 3. Procesar PDF
    texto_pdf = descargar_y_extraer_pdf(pdf_id)

    # 4. Consultar a Gemini
    respuesta = consultar_gemini(texto_pdf, request.pregunta, request.usuario)

    return {
        "success": True,
        "usuario": request.usuario,
        "pregunta": request.pregunta,
        "respuesta": respuesta,
        "libro_consultado": obtener_nombre_libro(pdf_id)
    }


@app.post("/n8n-autenticar")
async def autenticar_n8n(request: N8NAuthRequest):
    """Endpoint para integración con N8N existente"""
    if autenticar_usuario(request.usuario, request.clave):
        return {
            "success": True,
            "usuario_id": request.usuario,
            "mensaje": "Autenticación exitosa"
        }
    else:
        return {
            "success": False,
            "mensaje": "Credenciales inválidas"
        }


@app.get("/")
async def root():
    return {
        "mensaje": "🚀 Profesor Ayuni - Sistema Autónomo ACTIVO",
        "version": "1.0",
        "endpoints": {
            "preguntar": "POST /preguntar",
            "n8n_autenticar": "POST /n8n-autenticar",
            "estado": "GET /estado"
        }
    }


@app.get("/estado")
async def estado():
    """Verificar estado del sistema"""
    return {
        "estado": "🟢 FUNCIONANDO",
        "gemini_configurado": bool(GEMINI_API_KEY),
        "pdfs_configurados": len(BIBLIOTECA) > 0,
        "total_usuarios": len(USUARIOS)
    }


# ==================== FUNCIONES AUXILIARES ====================

def autenticar_usuario(usuario: str, clave: str) -> bool:
    """Autenticación simple de usuarios"""
    return usuario in USUARIOS and USUARIOS[usuario] == clave


def seleccionar_pdf_inteligente(pregunta: str) -> str:
    """Selecciona la carpeta más relevante para la pregunta"""
    pregunta_lower = pregunta.lower()

    # Lógica de selección por palabras clave
    if any(palabra in pregunta_lower for palabra in ["civil", "estática", "estructura", "hibbeler", "mecánica"]):
        return BIBLIOTECA["civil"]
    elif any(palabra in pregunta_lower for palabra in ["admin", "sistema", "configuración", "usuario"]):
        return BIBLIOTECA["admin"]
    else:
        return BIBLIOTECA["fisica"]  # Por defecto física


def descargar_y_extraer_pdf(file_id: str) -> str:
    """Descarga PDF de Google Drive y extrae texto"""
    try:
        print(f"📥 Descargando PDF...")
        url = f"https://drive.google.com/uc?export=download&id={file_id}"
        response = requests.get(url, timeout=30)

        pdf_file = io.BytesIO(response.content)
        reader = PyPDF2.PdfReader(pdf_file)

        texto = ""
        # Extraer primeras 5 páginas para prueba
        for i in range(min(5, len(reader.pages))):
            texto_pagina = reader.pages[i].extract_text() or ""
            texto += f"--- Página {i + 1} ---\n{texto_pagina}\n\n"

        print(f"✅ PDF procesado: {len(texto)} caracteres, {len(reader.pages)} páginas")
        return texto[:10000]  # Limitar tamaño

    except Exception as e:
        error_msg = f"❌ Error procesando PDF: {str(e)}"
        print(error_msg)
        return error_msg


def consultar_gemini(texto_pdf: str, pregunta: str, usuario: str) -> str:
    """Consulta a Google AI Studio (Gemini)"""
    try:
        print(f"🧠 Consultando Gemini para {usuario}...")
        model = genai.GenerativeModel('gemini-pro')

        prompt = f"""
        Eres el "Profesor Ayuni", un mentor virtual especializado en ingeniería mecánico-eléctrica.

        CONTENIDO DEL LIBRO DE CONSULTA:
        {texto_pdf}

        PREGUNTA DEL ESTUDIANTE {usuario}:
        {pregunta}

        Por favor responde:
        - De manera pedagógica pero técnica
        - Basándote en el contenido del libro proporcionado
        - Con ejemplos prácticos cuando sea posible
        - En español claro y profesional
        - Citando conceptos específicos del libro cuando sea relevante

        Si la información no está en el libro, sé honesto y sugiere dónde podrían encontrarla.
        """

        response = model.generate_content(prompt)
        print("✅ Respuesta recibida de Gemini")
        return response.text

    except Exception as e:
        error_msg = f"❌ Error en Gemini: {str(e)}"
        print(error_msg)
        return error_msg


def obtener_nombre_libro(file_id: str) -> str:
    """Obtiene el nombre del libro basado en el file_id"""
    if file_id == BIBLIOTECA["fisica"]:
        return "Biblioteca de Física (Tipler, Sears-Zemansky)"
    elif file_id == BIBLIOTECA["civil"]:
        return "Biblioteca de Ingeniería Civil (Hibbeler)"
    elif file_id == BIBLIOTECA["admin"]:
        return "Biblioteca de Administración"
    else:
        return "Material de consulta"


if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 Iniciando Servidor Profesor Ayuni en puerto {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)