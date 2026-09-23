from fastapi import FastAPI
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from playwright.async_api import async_playwright
import pandas as pd
import io

app = FastAPI()

# Permite que o Google Sites converse com este servidor
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/extrair")
async def extrair_cardapio(url: str):
    itens_extraidos = []
    
    async with async_playwright() as p:
        # Abre um navegador invisível
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            # Acessa o site que o usuário digitou
            await page.goto(url, timeout=60000)
            
            # Aqui o robô rola a página para carregar itens dinâmicos
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(3000) # Espera 3 segundos
            
            # ATENÇÃO: Esta é uma extração genérica. 
            # Puxa todos os textos que parecem títulos (h2, h3)
            # Para um sistema perfeito, futuramente você integraria IA aqui.
            titulos = await page.query_selector_all('h2, h3')
            
            for titulo in titulos:
                texto = await titulo.inner_text()
                if texto.strip():
                    itens_extraidos.append({"Item Encontrado": texto.strip()})
                    
        except Exception as e:
            return {"erro": str(e)}
        finally:
            await browser.close()

    # Cria a planilha (CSV)
    df = pd.DataFrame(itens_extraidos)
    stream = io.StringIO()
    df.to_csv(stream, index=False)
    
    # Devolve o arquivo para download
    return Response(
        content=stream.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=cardapio_extraido.csv"}
    )