from fastapi import FastAPI
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
import cloudscraper
from bs4 import BeautifulSoup
import pandas as pd
import io

app = FastAPI()

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
        # Cria um scraper disfarçado para contornar bloqueios (ex: Cloudflare)
        scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True})
        
        resposta = scraper.get(url, timeout=30)
        soup = BeautifulSoup(resposta.text, 'html.parser')
        
        # Procura os nomes dos produtos (h2, h3, h4)
        titulos = soup.find_all(['h2', 'h3', 'h4', 'span', 'p']) # Adicionado span e p para apanhar mais formatos
        nomes_produtos = []
        
        for titulo in titulos:
            texto = titulo.get_text(strip=True)
            # Filtra para evitar textos vazios ou mensagens de erro curtas
            if texto and len(texto) > 3 and "blocked" not in texto.lower() and "access" not in texto.lower():
                nomes_produtos.append(texto)

        # Remove duplicados mantendo a ordem original
        nomes_produtos = list(dict.fromkeys(nomes_produtos))

        # Colunas de instrução do seu modelo Excel
        colunas_instrucoes = [
            'Código do item, usado para verificação de unicidade', 'Se vincular vários grupos de itens adicionais, separe todos com vírgulas', 
            'Obrigatório', 'Opcional', 'Obrigatório.1', 'Insira a URL da imagem', 'Se o item tiver apenas um tamanho, deixe em branco por padrão', 
            'Insira apenas um preço numérico', 'Digite 1 para exibir neste canal, ou 0 para não exibir neste canal', 
            'Digite 1 para exibir neste canal, ou 0 para não exibir neste canal.1', 'Insira 0 se não houver limite, ou 1 se houver limite', 
            'Insira 0 se não houver limite, ou 1 se houver limite.1', 'Insira 0 se não houver limite, ou 1 se houver limite.2', 
            'Insira 0 se não houver limite, ou 1 se houver limite.3', 'Insira 0 se não houver limite, ou 1 se houver limite.4', 
            'Insira 0 se não houver limite, ou 1 se houver limite.5', 'Insira 0 se não houver limite, ou 1 se houver limite.6', 
            'Insira 0 se não houver limite, ou 1 se houver limite.7', 'Insira 0 se não houver limite, ou 1 se houver limite.8', 
            'Insira 0 se não houver limite, ou 1 se houver limite.9', 'Insira 0 se não houver limite, ou 1 se houver limite.10', 'Unnamed: 21'
        ]

        # Cabeçalhos reais do modelo
        linha_cabecalhos = [
            '*Código', '\t\nID do grupo de itens adicionais vinculados', '*Nome do item', 'Descrição do item', 
            '*Categoria do item', 'Link da imagem do item', 'Nome do tamanho', '*Preço de venda', 
            '*Canal de vendas: WhatsApp', '*Canal de vendas: escanear para fazer pedido', 'Vender somente em combos', 
            'Restrições alimentares: vegetariano', 'Restrições alimentares: vegano', 'Restrições alimentares: orgânico', 
            'Restrições alimentares: sem glúten', 'Restrições alimentares: sem açúcar', 'Restrições alimentares: sem lactose', 
            'Restrições alimentares: sem adição de açúcar', 'Restrições alimentares: sem bebida fria', 'Restrições alimentares: sem álcool', 
            'Restrições alimentares: tudo natural', 'Código PDV'
        ]

        dados = [linha_cabecalhos]

        for i, nome in enumerate(nomes_produtos):
            linha = [""] * 22
            linha[0] = str(i + 1)                 
            linha[2] = nome                       
            linha[4] = "Extraído"                 
            linha[7] = 0                          
            linha[8] = 1                          
            linha[9] = 1                          
            dados.append(linha)

        # Retorna erro claro se o Cloudscraper também for bloqueado
        if len(nomes_produtos) == 0:
            return {"erro": "O site bloqueou a extração (Anti-Bot Ativo) ou não foram encontrados produtos."}

        df = pd.DataFrame(dados, columns=colunas_instrucoes)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Item Regular', index=False)
        output.seek(0)
        
        return Response(
            content=output.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=cardapio_importacao.xlsx"}
        )
    except Exception as e:
        return {"erro": str(e)}
