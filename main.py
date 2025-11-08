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
    max_caracteres: int = 3000


class PDFResponse(BaseModel):
    success: bool
    contenido: str
    archivo: str
    paginas: int
    error: str = None


@app.post("/buscar-pdf", response_model=PDFResponse)
async def buscar_pdf(request: PDFRequest):
    try:
        # URL base de tu Ngrok (cambiar por tu link actual)
        NGROK_BASE = "https://2013b93fd06c.ngrok-free.app"

        pdf_url = f"{NGROK_BASE}/{request.carpeta}/{request.archivo}"

        print(f"Buscando PDF: {pdf_url}")

        # Descargar PDF
        response = requests.get(pdf_url, timeout=30)

        if response.status_code != 200:
            return PDFResponse(
                success=False,
                contenido="",
                archivo=request.archivo,
                paginas=0,
                error=f"PDF no encontrado: {response.status_code}"
            )

        # Extraer texto
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
            error=str(e)
        )


@app.get("/")
async def root():
    return {"message": "PDF API para Profesor Ayuni - Funcionando"}


@app.get("/archivos-disponibles")
async def archivos_disponibles(carpeta: str = "fisica_api"):
    """Lista archivos disponibles (opcional)"""
    return {
        "carpeta": carpeta,
        "archivos": [
            "007-Física Tipler 5ta Ed. .pdf",
            "008-Fisica Tipler SOL ED5.pdf",
            # Agrega más archivos manualmente
        ]
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))