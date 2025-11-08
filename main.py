from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import PyPDF2
import io
import os
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="PDF API para Profesor Ayuni")

# CORS para permitir GPT
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class PDFRequest(BaseModel):
    archivo: str
    carpeta: str = "fisica_api"  # fisica_api, civil_api, admin_api
    max_caracteres: int = 4000


class PDFResponse(BaseModel):
    success: bool
    contenido: str
    archivo: str
    paginas: int
    error: str = None


@app.post("/buscar-pdf", response_model=PDFResponse)
async def buscar_pdf(request: PDFRequest):
    try:
        # URL base de tu Ngrok ACTUAL
        NGROK_BASE = "https://e714395d7c19.ngrok-free.app"

        pdf_url = f"{NGROK_BASE}/{request.carpeta}/{request.archivo}"

        print(f"Buscando PDF: {pdf_url}")

        # Descargar PDF desde ngrok
        response = requests.get(pdf_url, timeout=30)

        if response.status_code != 200:
            return PDFResponse(
                success=False,
                contenido="",
                archivo=request.archivo,
                paginas=0,
                error=f"PDF no encontrado: {response.status_code}. URL: {pdf_url}"
            )

        # Extraer texto del PDF
        pdf_file = io.BytesIO(response.content)
        reader = PyPDF2.PdfReader(pdf_file)

        texto_completo = ""
        for i, pagina in enumerate(reader.pages):
            texto_pagina = pagina.extract_text() or ""
            texto_completo += f"--- Página {i + 1} ---\n{texto_pagina}\n\n"

        # Limitar tamaño
        texto_limite = texto_completo[:request.max_caracteres]

        return PDFResponse(
            success=True,
            contenido=texto_limite,
            archivo=request.archivo,
            paginas=len(reader.pages)
        )

    except Exception as e:
        return PDFResponse(
            success=False,
            contenido="",
            archivo=request.archivo,
            paginas=0,
            error=f"Error: {str(e)}"
        )


@app.get("/")
async def root():
    return {
        "message": "PDF API para Profesor Ayuni - Funcionando con Ngrok",
        "ngrok_url": "https://e714395d7c19.ngrok-free.app",
        "endpoints": {
            "buscar_pdf": "POST /buscar-pdf",
            "archivos_disponibles": "GET /archivos-disponibles?carpeta=fisica_api"
        }
    }


@app.get("/archivos-disponibles")
async def archivos_disponibles(carpeta: str = "fisica_api"):
    """Lista archivos disponibles a través de ngrok"""
    try:
        # Intentar listar archivos via ngrok
        ngrok_url = f"https://e714395d7c19.ngrok-free.app/{carpeta}/"
        response = requests.get(ngrok_url, timeout=10)

        if response.status_code == 200:
            # Si ngrok muestra lista de archivos (depende de la configuración)
            return {
                "carpeta": carpeta,
                "archivos": "Listado disponible via ngrok",
                "url_ngrok": ngrok_url
            }
        else:
            # Lista manual de archivos conocidos
            archivos_por_carpeta = {
                "fisica_api": [
                    "007-Física Tipler 5ta Ed. .pdf",
                    "008-Física Tipler SOL ED5.pdf",
                    "009-SearsZemanskyFisicaUniversitaria12va.Ed.Vol.1.pdf",
                    "010-Sears Zemansky 12 ed - Vol 2 - Español.pdf",
                    "Fisica_Universitaria_Sears_Zemansky_12va.pdf",
                    "011-Solucionario Zemansky (inglés).pdf"
                ],
                "civil_api": [
                    "020-Estática12ed-russelc-.pdf"
                ],
                "admin_api": [
                    # Agregar archivos de admin si los tienes
                ]
            }

            return {
                "carpeta": carpeta,
                "archivos": archivos_por_carpeta.get(carpeta, []),
                "nota": "Lista manual - verificar disponibilidad en ngrok"
            }

    except Exception as e:
        return {
            "carpeta": carpeta,
            "error": f"No se pudo obtener lista de archivos: {str(e)}"
        }


@app.get("/test-ngrok")
async def test_ngrok():
    """Endpoint para probar la conexión con ngrok"""
    try:
        test_url = "https://e714395d7c19.ngrok-free.app/fisica_api/"
        response = requests.get(test_url, timeout=10)

        return {
            "ngrok_status": "online" if response.status_code == 200 else "error",
            "status_code": response.status_code,
            "test_url": test_url
        }
    except Exception as e:
        return {
            "ngrok_status": "error",
            "error": str(e)
        }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))