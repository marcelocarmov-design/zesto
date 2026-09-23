from fastapi import FastAPI
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
import requests
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
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        resposta = requests.get(url, headers=headers, timeout=30)
        soup = BeautifulSoup(resposta.text, 'html.parser')
        
        # Extrai textos que pareçam títulos de produtos
        titulos = soup.find_all(['h2', 'h3', 'h4'])
        nomes_produtos = []
        for titulo in titulos:
            texto = titulo.get_text(strip=True)
            if texto and len(texto) > 3:  # Ignora textos muito curtos
                nomes_produtos.append(texto)

        # Remove duplicados mantendo a ordem
        nomes_produtos = list(dict.fromkeys(nomes_produtos))

        # Estrutura exata do seu ficheiro Excel (Linha 1 de instruções)
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

        # Linha 2 com os verdadeiros nomes das colunas
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

        # Preenche os produtos extraídos no formato exigido
        for i, nome in enumerate(nomes_produtos):
            linha = [""] * 22
            linha[0] = str(i + 1)                 # *Código
            linha[2] = nome                       # *Nome do item
            linha[4] = "Extraído do Site"         # *Categoria do item
            linha[7] = 0                          # *Preço (0 por defeito, ajustar manualmente depois)
            linha[8] = 1                          # WhatsApp = 1
            linha[9] = 1                          # Escanear = 1
            dados.append(linha)

        # Cria o DataFrame e o ficheiro Excel em memória
        df = pd.DataFrame(dados, columns=colunas_instrucoes)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Item Regular', index=False)
        output.seek(0)
        
        # Devolve o ficheiro .xlsx
        return Response(
            content=output.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=cardapio_importacao.xlsx"}
        )
    except Exception as e:
        return {"erro": str(e)}
