from fastapi import FastAPI
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
import requests
from bs4 import BeautifulSoup
import pandas as pd
import io

app = FastAPI()

# Permite a comunicação com o Google Sites
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/extrair")
def extrair_cardapio(url: str):
    try:
        # Finge ser um navegador normal para evitar bloqueios simples
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        # Acede ao site
        resposta = requests.get(url, headers=headers, timeout=30)
        
        # Lê o HTML da página
        soup = BeautifulSoup(resposta.text, 'html.parser')
        
        itens_extraidos = []
        
        # Procura por textos que pareçam títulos de produtos (h2, h3, h4)
        titulos = soup.find_all(['h2', 'h3', 'h4'])
        
        for titulo in titulos:
            texto = titulo.get_text(strip=True)
            if texto:
                itens_extraidos.append({"Item Encontrado": texto})

        # Cria o ficheiro CSV
        df = pd.DataFrame(itens_extraidos)
        stream = io.StringIO()
        df.to_csv(stream, index=False)
        
        # Envia o ficheiro para download
        return Response(
            content=stream.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=cardapio.csv"}
        )
    except Exception as e:
        return {"erro": str(e)}
