import pandas as pd
import xml.etree.ElementTree as ET
import os
import zipfile
from datetime import datetime

# Dicionário de mapeamento de códigos de complemento
CODIGOS_COMPLEMENTO = {
    "AC": 1, "AA": 2, "AF": 3, "AL": 4, "AS": 5, "AB": 6, "AN": 7, "AX": 8,
    "AP": 9, "AZ": 10, "AT": 11, "BS": 12, "BA": 13, "BR": 14, "BC": 15,
    "BL": 16, "BX": 17, "CS": 18, "CM": 20, "CP": 21, "CA": 22, "CE": 23,
    "CT": 24, "CB": 25, "CL": 26, "CD": 27, "CJ": 28, "CR": 29, "CO": 30,
    "DP": 31, "DT": 32, "DV": 34, "ED": 35, "EN": 36, "ES": 37, "EC": 38,
    "ET": 39, "EP": 40, "FO": 42, "FR": 43, "FU": 44, "GL": 45, "GP": 46,
    "GA": 47, "GB": 48, "GJ": 49, "GR": 50, "GH": 52, "HG": 53, "LD": 55,
    "LM": 56, 'LH': 57, "LE": 58, "LJ": 59, "LT": 60, "LO": 61, "M": 62,
    "MT": 63, "MC": 64, "MZ": 65, "MD": 66, "NC": 67, "OM": 68, "OG": 69,
    "PC": 70, "PR": 71, "PP": 72, "PV": 73, "PM": 74, "PS": 75, "PA": 76,
    "PL": 77, "P": 78, "PO": 80, "PT": 81, "PD": 82, "PE": 83, "QU": 85,
    "QT": 86, "KM": 87, "QN": 88, "QQ": 89, "RM": 90, "RP": 91, "RF": 92,
    "RT": 93, "RL": 95, "SL": 96, "SC": 97, "SR": 98, "SB": 100, "SJ": 101,
    "SD": 102, "SU": 103, "SS": 104, "SQ": 105, "TN": 106, "TO": 107,
    "TE": 109, "TV": 110, "TR": 111, "VL": 112, "VZ": 113, "AD": 114,
    "BI": 115, "SA": 116, "NA": 117, "SK": 118, "ND": 119, "SE": 120,
    "AM": 121, "NR": 122, "CH": 124
}

def formatar_coordenada(coord):
    """Converte coordenada de formato brasileiro para internacional"""
    if pd.isna(coord):
        return None
    try:
        return float(str(coord).replace(',', '.'))
    except ValueError:
        return None

def obter_codigo_complemento(texto):
    """
    Obtém o código do complemento baseado nas duas primeiras letras do texto
    """
    if pd.isna(texto) or texto == '':
        return '60'  # Default para LT (LOTE)
    
    texto_str = str(texto).strip().upper()
    
    # Pegar as duas primeiras letras
    if len(texto_str) >= 2:
        codigo = texto_str[:2]
        return str(CODIGOS_COMPLEMENTO.get(codigo, 60))  # Default 60 se não encontrar
    else:
        return '60'  # Default para LT (LOTE)

def extrair_numero_argumento(texto):
    """
    Extrai TODO o conteúdo depois das duas primeiras letras
    Exemplo: 
    "LT 14" → "14"
    "LT AREA 14" → "AREA 14" 
    "CA1" → "1"
    "QU 26" → "26"
    "BL A" → "A"
    """
    if pd.isna(texto) or texto == '':
        return '1'  # Valor padrão
    
    texto_str = str(texto).strip()
    
    # Se o texto tiver menos de 2 caracteres, retorna padrão
    if len(texto_str) < 2:
        return '1'
    
    # Pegar TUDO depois dos dois primeiros caracteres
    argumento = texto_str[2:].strip()
    
    # Se estiver vazio, retorna padrão
    if argumento == '':
        return '1'
    
    return argumento

def determinar_destinacao(ucs_residenciais, ucs_comerciais):
    """Determina a destinação baseado nas UCs residenciais e comerciais"""
    if ucs_residenciais > 0 and ucs_comerciais == 0:
        return 'RESIDENCIA'
    elif ucs_comerciais > 0 and ucs_residenciais == 0:
        return 'COMERCIO'
    else:
        return 'MISTA'

def criar_xml_edificio(dados_csv, numero_pasta):
    # Criar o elemento raiz
    edificio = ET.Element('edificio')
    edificio.set('tipo', 'M')
    edificio.set('versao', '7.9.2')
    
    # Adicionar elementos filhos
    ET.SubElement(edificio, 'gravado').text = 'false'
    ET.SubElement(edificio, 'nEdificio').text = dados_csv['COD_SURVEY']
    
    # Coordenadas do CSV
    latitude = formatar_coordenada(dados_csv['LATITUDE'])
    longitude = formatar_coordenada(dados_csv['LONGITUDE'])
    
    ET.SubElement(edificio, 'coordX').text = str(longitude) 
    ET.SubElement(edificio, 'coordY').text = str(latitude) 
    
    # Código e nome da zona do CSV
    codigo_zona = str(dados_csv['COD_ZONA']) if 'COD_ZONA' in dados_csv and not pd.isna(dados_csv['COD_ZONA']) else 'DF-GURX-ETGR-CEOS-68'
    ET.SubElement(edificio, 'codigoZona').text = codigo_zona
    ET.SubElement(edificio, 'nomeZona').text = codigo_zona
    
    # Localidade - usar do CSV
    localidade = str(dados_csv['LOCALIDADE']) if 'LOCALIDADE' in dados_csv and not pd.isna(dados_csv['LOCALIDADE']) else 'GUARA'
    ET.SubElement(edificio, 'localidade').text = localidade
    
    # Endereço do edifício
    endereco = ET.SubElement(edificio, 'enderecoEdificio')
    ET.SubElement(endereco, 'id').text = str(dados_csv['ID_ENDERECO']) if 'ID_ENDERECO' in dados_csv and not pd.isna(dados_csv['ID_ENDERECO']) else '93128133'
    
    # Logradouro do CSV
    logradouro = str(dados_csv['LOGRADOURO'] +", "+ dados_csv['BAIRRO']+", "+dados_csv['MUNICIPIO']+"- "+dados_csv['LOCALIDADE']+" - "+ dados_csv["UF"]+ f" ({dados_csv['COD_LOGRADOURO']})" )
    ET.SubElement(endereco, 'logradouro').text = logradouro
    
    # Número da fachada do CSV
    num_fachada = str(dados_csv['NUM_FACHADA']) if 'NUM_FACHADA' in dados_csv and not pd.isna(dados_csv['NUM_FACHADA']) else 'SN'
    ET.SubElement(endereco, 'numero_fachada').text = num_fachada
    
    # COMPLEMENTO1 - usa coluna COMPLEMENTO
    complemento1 = dados_csv['COMPLEMENTO'] if 'COMPLEMENTO' in dados_csv else ''
    codigo_complemento1 = obter_codigo_complemento(complemento1)
    argumento1 = extrair_numero_argumento(complemento1)
    
    ET.SubElement(endereco, 'id_complemento1').text = codigo_complemento1
    ET.SubElement(endereco, 'argumento1').text = argumento1
    
    # COMPLEMENTO2 - usa coluna COMPLEMENTO2
    complemento2 = dados_csv['COMPLEMENTO2'] if 'COMPLEMENTO2' in dados_csv else ''
    codigo_complemento2 = obter_codigo_complemento(complemento2)
    argumento2 = extrair_numero_argumento(complemento2)
    
    ET.SubElement(endereco, 'id_complemento2').text = codigo_complemento2
    ET.SubElement(endereco, 'argumento2').text = argumento2
    
    # COMPLEMENTO3 - usa coluna RESULTADO
    complemento3 = dados_csv['RESULTADO'] if 'RESULTADO' in dados_csv else ''
    codigo_complemento3 = obter_codigo_complemento(complemento3)
    argumento3 = extrair_numero_argumento(complemento3)
    
    ET.SubElement(endereco, 'id_complemento3').text = codigo_complemento3
    ET.SubElement(endereco, 'argumento3').text = argumento3
    
    # CEP do CSV
    cep = str(dados_csv['CEP']) if 'CEP' in dados_csv and not pd.isna(dados_csv['CEP']) else '71065071'
    ET.SubElement(endereco, 'cep').text = cep
    
    # Bairro do CSV
    bairro = str(dados_csv['BAIRRO']) if 'BAIRRO' in dados_csv and not pd.isna(dados_csv['BAIRRO']) else localidade
    ET.SubElement(endereco, 'bairro').text = bairro
    
    # IDs do roteiro e localidade do CSV
    ET.SubElement(endereco, 'id_roteiro').text = str(dados_csv['ID_ROTEIRO']) if 'ID_ROTEIRO' in dados_csv and not pd.isna(dados_csv['ID_ROTEIRO']) else '57149008'
    ET.SubElement(endereco, 'id_localidade').text = str(dados_csv['ID_LOCALIDADE']) if 'ID_LOCALIDADE' in dados_csv and not pd.isna(dados_csv['ID_LOCALIDADE']) else '1894644'
    
    # Código do logradouro do CSV
    cod_lograd = str(dados_csv['COD_LOGRADOURO']) if 'COD_LOGRADOURO' in dados_csv and not pd.isna(dados_csv['COD_LOGRADOURO']) else '2700035341'
    ET.SubElement(endereco, 'cod_lograd').text = cod_lograd
    
    # Técnico
    tecnico = ET.SubElement(edificio, 'tecnico')
    ET.SubElement(tecnico, 'id').text = '1828772688'
    ET.SubElement(tecnico, 'nome').text = 'NADIA CAROLINE'
    
    # Empresa
    empresa = ET.SubElement(edificio, 'empresa')
    ET.SubElement(empresa, 'id').text = '42541126'
    ET.SubElement(empresa, 'nome').text = 'TELEMONT'
    
    # Data atual
    data_atual = datetime.now().strftime('%Y%m%d%H%M%S')
    ET.SubElement(edificio, 'data').text = data_atual
    
    # Total de UCs do CSV
    total_ucs = int(dados_csv['QUANTIDADE_UMS']) if 'QUANTIDADE_UMS' in dados_csv and not pd.isna(dados_csv['QUANTIDADE_UMS']) else 1
    ET.SubElement(edificio, 'totalUCs').text = str(total_ucs)
    
    # Ocupação e destinação
    ET.SubElement(edificio, 'ocupacao').text = 'EDIFICACAOCOMPLETA'
    
    ucs_residenciais = int(dados_csv['UCS_RESIDENCIAIS']) if 'UCS_RESIDENCIAIS' in dados_csv and not pd.isna(dados_csv['UCS_RESIDENCIAIS']) else 0
    ucs_comerciais = int(dados_csv['UCS_COMERCIAIS']) if 'UCS_COMERCIAIS' in dados_csv and not pd.isna(dados_csv['UCS_COMERCIAIS']) else 0
    destinacao = determinar_destinacao(ucs_residenciais, ucs_comerciais)
    ET.SubElement(edificio, 'destinacao').text = destinacao
    
    # Número de pisos
    ET.SubElement(edificio, 'numPisos').text = '1'
    
    # Criar o XML
    xml_str = ET.tostring(edificio, encoding='UTF-8', method='xml')
    
    # Adicionar declaração XML
    xml_completo = b'<?xml version="1.0" encoding="UTF-8"?>' + xml_str
    
    return xml_completo

def main():
    # Ler o CSV com tabulação como separador
    try:
        # Tentar diferentes encodings
        encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
        
        for encoding in encodings:
            try:
                df = pd.read_csv('cto.csv', sep=';', encoding=encoding)
                print(f"Arquivo lido com encoding: {encoding}")
                break
            except UnicodeDecodeError:
                continue
        else:
            print("Tentando ler com encoding padrão...")
            df = pd.read_csv('cto.csv', sep=';')
            
    except Exception as e:
        print(f"Erro ao ler o arquivo CSV: {e}")
        print("Verifique se o arquivo existe e o separador está correto.")
        return
    
    # Mostrar informações do arquivo
    print(f"Total de linhas: {len(df)}")
    print(f"Colunas disponíveis: {list(df.columns)}")
    
    # Criar diretório principal
    diretorio_principal = 'moradias_xml_'+ df['ESTACAO_ABASTECEDORA'].iloc[0]+ "_" + datetime.now().strftime('%Y%m%d%H%M%S')
    os.makedirs(diretorio_principal, exist_ok=True)
    
    # Lista para armazenar caminhos das pastas
    pastas_criadas = []
    
    print("\nProcessando CSV e gerando XMLs...")
    
    # Processar cada linha do CSV
    for i, (index, linha) in enumerate(df.iterrows(), 1):
        # Criar nome da pasta
        nome_pasta = f'moradia{i}'
        caminho_pasta = os.path.join(diretorio_principal, nome_pasta)
        
        # Criar a pasta
        os.makedirs(caminho_pasta, exist_ok=True)
        pastas_criadas.append(caminho_pasta)
        
        # Criar leitura dos dados para verificar
        comp1 = linha['COMPLEMENTO'] if 'COMPLEMENTO' in linha else ''
        comp2 = linha['COMPLEMENTO2'] if 'COMPLEMENTO2' in linha else ''
        resultado = linha['RESULTADO'] if 'RESULTADO' in linha else ''
        
        # Criar o XML
        xml_content = criar_xml_edificio(linha, i)
        
        # Caminho do arquivo XML
        caminho_xml = os.path.join(caminho_pasta, f'{nome_pasta}.xml')
        
        # Salvar o XML
        with open(caminho_xml, 'wb') as f:
            f.write(xml_content)
        
        # Mostrar informações do processamento a cada 10 registros
        if i % 10 == 0 or i == 1:
            codigo1 = obter_codigo_complemento(comp1)
            codigo2 = obter_codigo_complemento(comp2)
            codigo3 = obter_codigo_complemento(resultado)
            
            arg1 = extrair_numero_argumento(comp1)
            arg2 = extrair_numero_argumento(comp2)
            arg3 = extrair_numero_argumento(resultado)
            
            print(f'Registro {i}:')
            print(f'  COMP1("{comp1}" → código:{codigo1} argumento:"{arg1}")')
            print(f'  COMP2("{comp2}" → código:{codigo2} argumento:"{arg2}")')
            print(f'  RESULT("{resultado}" → código:{codigo3} argumento:"{arg3}")')
            print('-' * 50)
    
    # Criar arquivo ZIP
    zip_filename = f'{diretorio_principal}.zip'
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for pasta in pastas_criadas:
            for root, dirs, files in os.walk(pasta):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, diretorio_principal)
                    zipf.write(file_path, arcname)
    
    print(f'\n✅ Arquivo ZIP criado: {zip_filename}')
    print(f'✅ Total de {len(df)} pastas e arquivos XML criados.')

if __name__ == '__main__':
    main()