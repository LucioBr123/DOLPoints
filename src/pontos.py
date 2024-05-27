import requests
from lxml import html
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import pandas as pd
import MetaTrader5 as mt5
from dateutil.relativedelta import relativedelta
from decimal import Decimal

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

def obtemDolarComercial():
    url = "https://br.investing.com/currencies/usd-brl"
    response = requests.get(url)
    tree = html.fromstring(response.content)

    # Use XPath para encontrar o elemento que contém o preço de compra
    preco_compra_element = tree.xpath('//*[@id="__next"]/div[2]/div[2]/div[2]/div[1]/div[1]/div[3]/div[1]/div[1]/div[1]/text()')[0]
    preco_compra = preco_compra_element.strip()  # Remova espaços em branco
    preco_compra = float(preco_compra.replace(',','.'))

    return preco_compra

def obtemAjuste():
     #traz o html
    html_text = requests.get('https://www2.bmf.com.br/pages/portal/bmfbovespa/lumis/lum-ajustes-do-pregao-ptBR.asp').text
    soup = BeautifulSoup (html_text, 'lxml')
    #Filtra dados
    tabela_bruta=soup.find('table')
    data = []
    for row in tabela_bruta.find_all('tr'):
        row_data = []
        for cell in row.find_all(['th', 'td']):
            row_data.append(cell.get_text(strip=True))
        data.append(row_data)
    
    # Cria o DataFrame a partir da lista de listas
    df = pd.DataFrame(data[1:], columns=data[0])

    #Lógia do contrato atual 
    hoje=datetime.now()
    mes= hoje.month
    ano=hoje.year-2000

    meses_vencimentos = {
    1 : 'F', 
    2 : 'G',
    3 : 'H', 
    4 : 'J', 
    5 : 'K', 
    6 : 'M', 
    7 : 'N', 
    8 : 'Q', 
    9 : 'U', 
    10 : 'V',
    11 : 'X',
    12 : 'Z'
    }

    # Supondo que 'mes' seja a variável que você está verificando
    vencimento = meses_vencimentos.get(mes)
    contrato=(vencimento + str(ano) )
    dol1=df.loc[df["Mercadoria"]=='DOL   - Dólar comercial']
    # Verificar se o contrato está correto
    if dol1["Vencimento"].iloc[0] != contrato:
        indice_ajuste_atual = dol1.index + 1
    else: 
        indice_ajuste_atual = dol1.index

    # Filtra o index com o index certo
    dol1=df.loc[indice_ajuste_atual]

    # Obter o valor do ajuste
    ajuste = dol1['Preço de ajuste Atual'].iloc[0]

    # Remover a vírgula e converter para float
    ajuste = ajuste.replace(',', '')
    ajuste = float(ajuste)
    return {'ajuste': ajuste}

def obtemDI():
    hoje=datetime.now()
    mes= hoje.month 
    ano=hoje.year-2000

    meses_vencimentos = {
    1 : 'F', 
    2 : 'G',
    3 : 'H', 
    4 : 'J', 
    5 : 'K', 
    6 : 'M', 
    7 : 'N', 
    8 : 'Q', 
    9 : 'U', 
    10 : 'V',
    11 : 'X',
    12 : 'Z'
    }

    
    # Supondo que 'mes' seja a variável que você está verificando
    vencimento = meses_vencimentos.get(mes+1)
    contrato=(vencimento + str(ano) )
    contrato="DI1"+str(contrato)
    
    mt5.initialize()
    # tentamos ativar a exibição do símbolo EURCAD no MarketWatch
    selected=mt5.symbol_select(contrato,True)
    if not selected:
        print("Erro ao adicionar ativo na OBS. de mercado=",mt5.last_error())
   
    ultimo=mt5.symbol_info_tick(contrato).last  
    mt5.shutdown()

    return ultimo

import datetime

def obtemQuantidadeDiasUteis():
    data_atual = datetime.now()  # Corrigindo o acesso à data atual
    ano = data_atual.year
    feriados = [
        datetime(ano, 1, 1),   # Ano Novo
        datetime(ano, 4, 21),  # Tiradentes
        datetime(ano, 5, 1),   # Dia do Trabalhador
        datetime(ano, 9, 7),   # Independência
        datetime(ano, 10, 12), # Nossa Senhora Aparecida
        datetime(ano, 11, 2),  # Finados
        datetime(ano, 12, 25)  # Natal
    ]

    # Contar os dias úteis
    dias_uteis = 0
    data = datetime(ano, 1, 1)
    while data.year == ano:
        if data.weekday() < 5 and data not in feriados:
            dias_uteis += 1
        data += timedelta(days=1)

    return dias_uteis

def obtemDiasParaVencimento():
    data_atual = datetime.now().date()
    data_alvo = data_atual + relativedelta(months=1, day=1) 
    delta = data_alvo - data_atual
    return delta.days

def obtemOver():
    di1 = obtemDI()
    diasUteis = obtemQuantidadeDiasUteis()
    diasParaVencimento = obtemDiasParaVencimento()
    over = ((1+di1)**(1/diasUteis)-1)* diasParaVencimento
    return over


def obtemJusto():
    over = obtemOver()
    dolar = obtemDolarComercial()

    calc1 = Decimal(over)/100
    calc2 = Decimal(dolar) * Decimal(calc1)
    justo = Decimal(calc1)+Decimal(dolar)
    return {'justo':justo} 

##FALTA ARRUMAR ESSA BELEZURAS

import requests
from lxml import html
import pandas as pd
from decimal import Decimal

import requests
from lxml import html
import pandas as pd

def obtemMovimentaçãoMadrugada():
    # URL do site com a tabela
    url = 'https://br.investing.com/currencies/brl-usd-historical-data'

    # Faz a solicitação HTTP
    response = requests.get(url)

    # Analisa o conteúdo HTML da resposta
    tree = html.fromstring(response.content)

    # Encontra todas as linhas da tabela usando XPath
    linhas_tabela = tree.xpath('//*[@id="__next"]/div[2]/div[2]/div[2]/div[1]/div[2]/div[3]/table//tr')

    # Extrai os dados da primeira linha da tabela
    primeira_linha = linhas_tabela[1].xpath('.//td//text()')

    # Cria um DataFrame do Pandas com os dados da primeira linha
    df = pd.DataFrame([primeira_linha], columns=["Data", "Último", "Abertura", "Máxima", "Mínima", "Variação"])

    # Convertendo apenas a variação para float
    df['Máxima'] = df['Máxima'].str.replace(',', '').astype(float)
    df['Mínima'] = df['Mínima'].str.replace(',', '').astype(float)
    
    # Encontrando o máximo e o mínimo
    maxima = df['Máxima'].max()
    minima = df['Mínima'].min()

    # Formatando para ter 4 casas decimais
    maxima = '{:.4f}'.format(maxima)
    minima = '{:.4f}'.format(minima)

    return {'madrugada':{"maxima": maxima, "minima": minima}}



    # pontos_padrao=[Justo,maxima,minima,ajuste]    

def obtemFibo(ponto1, ponto2):
    # Verifica se os pontos são válidos
    if ponto1 >= ponto2:
        return "Erro: Ponto 1 deve ser menor que Ponto 2"

    # Calcula a diferença entre os dois pontos
    diff = ponto2 - ponto1

    # Calcula os níveis de Fibonacci
    fibonacci_38 = ponto2 - (0.382 * diff)
    fibonacci_62 = ponto2 - (0.618 * diff)

    return {"fibonacci_38": fibonacci_38, "fibonacci_62": fibonacci_62}


from datetime import datetime
import MetaTrader5 as mt5

import pandas as pd
pd.set_option('display.max_columns', 500) # número de colunas
pd.set_option('display.width', 1500)      # largura máxima da tabela



def obtemPontos(periodo):
    periodos = {
        'diario': mt5.TIMEFRAME_D1,
        'semanal': mt5.TIMEFRAME_W1,
        'mensal': mt5.TIMEFRAME_MN1,
        'anual': mt5.TIMEFRAME_MN1
    }

    if periodo in periodos:
        periodo_mt5 = periodos[periodo]
        # Restante da sua função
        # Use 'periodo_mt5' conforme necessário
    else:
        print("Período não suportado")
        return None

    #Obtem Dados
    if not mt5.initialize():
        print("initialize() failed, error code =",mt5.last_error())
        quit()
    mesAtual = datetime.now().month    
    rates = mt5.copy_rates_from_pos("DOL$", periodo_mt5, 0, mesAtual)
    mt5.shutdown()

    # a partir dos dados recebidos criamos o DataFrame
    rates_frame = pd.DataFrame(rates)
    # convertemos o tempo em segundos no formato datetime
    rates_frame['time']=pd.to_datetime(rates_frame['time'], unit='s')

    # Como você está interessado nos dados do último ponto, vamos usar iloc[-1] para acessar o último ponto no DataFrame.
    
    ultimo_ponto = rates_frame.iloc[-1]
    
    if periodo == 'anual':
        abertura = rates_frame.iloc[0]['open']
        maxima = rates_frame['high'].max()
        minima = rates_frame['low'].min()
        fechamento = ultimo_ponto['close']
    else:
        abertura = ultimo_ponto['open']
        maxima = ultimo_ponto['high']
        minima = ultimo_ponto['low']
        fechamento = ultimo_ponto['close']

    return {
        'abertura-'+periodo: abertura,
        'maxima-'+periodo: maxima,
        'minima-'+periodo: minima,
        'fechamento-'+periodo: fechamento
    }


pts = {
    str(obtemPontos('diario')),
    str(obtemPontos('semanal')),
    str(obtemPontos('mensal')),
    str(obtemPontos('anual')),
    str(obtemJusto()),
    str(obtemAjuste()),
    str(obtemMovimentaçãoMadrugada())
}

print(pts)


# print(obtemPontos('diario'))
# print(obtemPontos('semanal'))
# print(obtemPontos('mensal'))
# print(obtemPontos('anual'))


# print(obtemDolarComercial())
# print(obtemDI())
# print(obtemQuantidadeDiasUteis())
# print(obtemDiasParaVencimento())

# print(obtemOver())

# print(obtemJusto())
# print(obtemAjuste())

# # print(obtemFibo(100,200))
# print(obtemMovimentaçãoMadrugada())

