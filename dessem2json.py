#!/usr/bin/env python3

import os,logging,json
from argparse import ArgumentParser
from io import UnsupportedOperation
from deckparser.dessem2dicts import dessem2dicts
from deckparser.importers.dessem.loader import Loader
from deckparser.dessemsource import dessem_source
from deckparser.importers.dessem.out.result_loader import ResultLoader

class CustomArgParser(ArgumentParser):
    def print_help(self, *args):
        super().print_help(*args)
        print_sample()
        files_desc()

def main():
    logging.basicConfig(level=logging.DEBUG)
    
    parser = init_argument_parser()
    args = parser.parse_args()
    if not validate_args(args):
        parser.print_help()
        return False
    
    elif args.list_files:
        list_files()
        list_result_files()
        return True
    elif args.list_records:
        list_records(args.list_records[0])
        return True
    elif args.list_cases:
        list_cases(args.file[0])
        return True
    elif args.file:
        if not check_files_access(args):
            return False
        deck = dessem2dicts(fn = args.file[0],
                            dia = args.days,
                            rd = compose_grid_option(args),
                            file_filter = compose_filter(args.load_results, args.ds_files, args.ds_records),
                            interval_list = args.grid_intervals,
                            load_results = args.load_results)
        fdeck = format_data(deck)
        
        if args.outfile:
            try:
                with open(args.outfile[0], 'w') as f:
                    json.dump(fdeck,f,indent=3)
            except UnsupportedOperation:
                print('Could not write to ' + args.outfile[0])
                raise
        else:
            print(json.dumps(fdeck,indent=1))
        return True

def init_argument_parser():
    parser = CustomArgParser(description='DESSEM deck files importer')
    parser.add_argument('-list_files', action='store_true', help='List file that can be read')
    parser.add_argument('-list_records', nargs=1, metavar='dsfile', type=str, help='List records that can be read from the file type "dsfile"')
    parser.add_argument('-file', nargs=1, metavar='ZIP_FILE', type=str, help='File containing DESSEM cases (decks)')
    parser.add_argument('-list_cases', action='store_true', help='List cases contained in the given file')
    parser.add_argument('-load_results', action='store_true', help='Load DESSEM results from the given file')
    parser.add_argument('-days', nargs='+', metavar='d', type=int, help='Read only cases with dates corresponding to days (default: all)')
    parser.add_argument('-grid_option', nargs=1, type=str, choices=['on','off','all'], help='Read only cases containing grid data (on) or not (off) (default: all)')
    parser.add_argument('-ds_files', nargs='+', metavar='rec', type=str, help='File types to be read (default: all)')
    parser.add_argument('-ds_records', nargs='+', metavar='rec', type=str, help='Records to be read (default: all)')
    parser.add_argument('-grid_intervals', nargs='+', metavar='t', type=int, help='Grid data time intervals to be read (default: all)')
    parser.add_argument('-outfile', nargs=1, metavar='f', type=str, help='File to save imported data')
    return parser

def validate_args(args):
    if args.list_files and args.list_records:
        print('list_files and list_records are complementary arguments')
        return False
    if not args.file:
        if any([args.list_cases, args.load_results, args.days, args.grid_option, 
                args.ds_records, args.grid_intervals, args.outfile]):
            print('Must provide file for reading optional arguments')
            return False
    return True

def check_files_access(args):
    fp = args.file[0]
    if not os.path.exists(fp):
        print('File doesn\'t exists ' + fp)
        return False
    if not os.access(fp, os.R_OK):
        print('Cannot read from ' + fp)
        return False
    return True
    
def compose_grid_option(args):
    if not args.grid_option:
        return None
    go = args.grid_option[0]
    if go == 'on':
        return True
    elif go == 'off':
        return False

def compose_filter(load_results, arqList, recList):
    if load_results:
        resFiles = ResultLoader().listFiles()
        if not arqList:
            return resFiles
        return [f for f in resFiles if f in arqList]
    ft = {}
    if not arqList:
        arqList = Loader().listFiles()
    for arq in arqList:
        f = Loader().listRecords(arq)
        if not recList:
            ft[arq] = None
            continue
        rl = []
        for rec in recList:
            if rec in f:
                rl.append(rec)
        ft[arq] = rl
    return ft

def format_data(deck):
    fdeck = {}
    for d in deck:
        sd = str(d)
        fdeck[sd] = {}
        for r in deck[d]:
            sr = ('com_rede' if r else 'sem_rede')
            fdeck[sd][sr] = deck[d][r]
    return fdeck

def files_desc():
    print_header('Arquivos disponíveis para leitura')
    print('Arquivos de índice: dessem, desselet')
    print('Arquivo com dados gerais do caso: entdados')
    print('Arquivos com dados das usinas hidrelétricas, rede hidráulica e restrições aplicáveis: hidr, operuh, dadvaz, curvtviag, cotasr11, ils_tri')
    print('Arquivos com dados para simulação: simul, deflant')
    print('Arquivos com dados sobre área de controle e reserva de potência: areacont, respot')
    print('Arquivos com dados de controle das restrições de segurança: rstlpp, restseg')
    print('Arquivos com dados da rede elétrica: eletbase, eletmodif')
    print('Arquivos com dados das usinas termelétricas: termdat, operut, ptoper, rampas')
    print('Arquivos com dados outras usinas: renovaveis')
    print('Outros arquivos: infofcf, tolperd')
    print('Arquivos com resultados: pdo_operacao, pdo_sist, pdo_sumaoper')

def print_sample():
    print_header('Exemplos')
    __print_sample('Lista de arquivos que podem ser lidos', 'dessem2json -list_files')
    __print_sample('Lista de registros que podem ser lidos de um dado arquivo', 'dessem2json -list_records arquivo')
    __print_sample('Lista de casos contidos no arquivo', 'dessem2json -list_cases -file DES_201805.zip')
    __print_sample('Exportação de todos os decks contidos no arquivo fornecido', 'dessem2json -file DES_201805.zip')
    __print_sample('Exportação dos decks com data 02/05/2018', 'dessem2json -file DES_201805.zip -days 2')
    __print_sample('Exportação dos decks com datas 02/05/2018 e 05/05/2018', 'dessem2json -file DES_201805.zip -days 2 5')
    __print_sample('Exportação do deck com rede elétrica', 'dessem2json -file DES_201805.zip -days 2 -grid_option on')
    __print_sample('Exportação do arquivo entdados, contido no deck especificado', 'dessem2json -file DES_201805.zip -days 2 -grid_option on -ds_files entdados')
    __print_sample('Exportação do registro UH do arquivo entdados', 'dessem2json -file DES_201805.zip -days 2 -grid_option on -ds_files entdados -ds_records UH')
    __print_sample('Exportação dos dados de barramentos da rede elétrica básica* para o primeiro intervalo de tempo', 'dessem2json -file DES_201805.zip -days 2 -grid_option on -ds_files eletbase -ds_records DBAR -grid_intervals 1')
    __print_sample('Exportação dos dados de modificação de barramentos da rede elétrica básica para o primeiro intervalo de tempo', 'dessem2json -file DES_201805.zip -days 2 -grid_option on -ds_files eletmodif -ds_records DBAR -grid_intervals 1')
    __print_sample('Exportação de resultados', 'dessem2json -file DES_201805.zip -load_results')
    print('\n* Rede elétrica básica é aquela que não contém as modificações específicas para o intervalo de tempo dado')
    
def print_header(h):
    print('-'*50)
    print(h)
    print('-'*50)

def __print_sample(header, code):
    print('- '+header)
    print('>>>> '+code)
    
def list_cases(fn):
    dessem_source(fn).printIndex()

def list_files():
    print_header('Lista de arquivos')
    lst = Loader().listFiles()
    lst.sort()
    for f in lst:
        print(f)

def list_result_files():
    print_header('Lista de arquivos (resultado)')
    lst = ResultLoader().listFiles()
    lst.sort()
    for f in lst:
        print(f)

def list_records(f):
    print_header('Lista de registros do arquivo: '+f)
    lst = Loader().listRecords(f)
    if not lst:
        return
    lst.sort()
    for f in lst:
        print(f)

if __name__ == '__main__':
    main()