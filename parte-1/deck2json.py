'''
LEITOR DE DECKS DESSEM E CONVERSOR PARA JSON

Author: K. Vinente

Versão: 0.2

Futures versions need to include:
 a) transmission lines limits changes according with case -> not implemented
'''

##### PYTHON MODULES
import json
import pandas as pd
import os
import numpy as np

##### TEMPLATE PARA O ARQUIVO JSON RESULTANTE 
json_data = {
    "Parameters": {
        "Version": "0.2",
        "Case Name": "DESSEM 24 ACAD",
    },
    "Thermal Generators": {
    },
    "Hydro Generators": {
    },
    "Buses": {

    },
    "Transmission lines": {
    }
}

output_file_path = 'data.json'

with open(output_file_path, 'w') as file:
    json.dump(json_data, file, indent=4)

with open(output_file_path, 'r') as file:
    json_data = json.load(file)


##### LISTA DE ARQUIVOS DO DESSEM

FILE_INFLOWS = "dadvaz.dat"
FILE_INPUT_DATA = "entdados.dat"
FILE_INPUT_FCF = "mapcut.rv0"
FILE_DECOMP_CUTS = "cortdeco.rv0"
FILE_HYDRO_DATA = "CadUsH.csv"
FILE_HYDRO_OPERATION = "operuh.dat"
FILE_PREVIOUS_DEFLUENCES = "deflant.dat"
FILE_THERMAL_DATA = "termdat.dat"
FILE_THERMAL_OPERATION = "operut.dat"
FILE_NETWORK_DATA = "desselet.arq"
FILE_PEREIRA_BARRETO_CHANNEL = ""
FILE_MLT = "mlt.dat"
FILE_EER = "entdados.dat"
FILE_BASE_NETWORK = ""

FOLDER_PATH = "casos/case24acad/"

##### TEMP VARIABLES USED TO STORE INFORMATION
total_duration = 0
deficit_cost = []
thermal_generators = {}
hydro_generators = {}
cadunidt_info = {}
ucterm_info = {}
oper_info = {}
processed_units = set() 
dusi_info = {}
dusi_hydro_info = {}
processed_dessem = set() 
tviag_info = {}
inflows_data_corrected_v2 = []
transmission_lines_data = {}
buses_data = {}
time_intervals = []
patamar = []
patamares_info = []
load_mw = {}
arq_patamar = []
patamar_muda = []

##### READING FILES
print(f"********** Reading Files **********\n")

file_path = FOLDER_PATH + FILE_INPUT_DATA

'''
Parameters: Time horizon (h); Deficit Cost ($); time_intervals;
Thermal Generators: No DESSEM"; Name; Subsystem;
Hydro Generators: No DESSEM; Name; Subsystem; Initial Volume (hm3);
''' 
    
file_path = FOLDER_PATH + FILE_INPUT_DATA
reading = False

try:
    with open(file_path, 'r', encoding='ISO-8859-1') as file:
        for line in file:
            if line.startswith('TM'):
                duration = float(line[19:25].strip())
                total_duration += duration
                time_intervals.append(duration)
            if line.startswith('CD'):
                cost = float(line[25:36].strip())
                deficit_cost.append(cost)
            if line.startswith('UT'):
                no_dessem = int(line[4:7].strip())
                name = line[9:22].strip()
                subsystem = int(line[22:24].strip())
                thermal_generators[str(len(thermal_generators) + 1)] = {
                    "No DESSEM": no_dessem,
                    "Name": name,
                    "Subsystem": subsystem
                }
            if line.startswith('UH'):
                no_dessem = int(line[4:7].strip())
                name = line[9:21].strip()
                subsystem = int(line[24:26].strip())
                initial_volume = float(line[29:39].strip())
                hydro_generators[str(len(hydro_generators) + 1)] = {
                    "No DESSEM": no_dessem,
                    "Name": name,
                    "Subsystem": subsystem,
                    "Initial Volume (hm3)": initial_volume
                }

except Exception as e:
    error_message = str(e)
    total_duration = None


json_data["Parameters"]["Time horizon (h)"] = total_duration
json_data["Parameters"]["Deficit Cost ($)"] = deficit_cost
json_data["Parameters"]["time_intervals"] = time_intervals
json_data["Parameters"]["base (MVA)"] = 100
json_data["Parameters"]["Spillage Cost ($)"] = 1
json_data["Thermal Generators"] = thermal_generators
json_data["Hydro Generators"] = hydro_generators

'''
Thermal Generators: Max Power (MW); Min Power (MW); Minimum Uptime (h);
Minimum Downtime (h);
'''

file_path = FOLDER_PATH + FILE_THERMAL_DATA

with open(file_path, 'r', encoding='ISO-8859-1') as file:
    for line in file:
        if line.startswith('CADUNIDT'):
            key = line[10:12].strip()
            max_power = float(line[33:43].strip())
            min_power = float(line[44:54].strip())
            min_uptime = int(line[55:60].strip())
            min_downtime = int(line[61:66].strip())

            cadunidt_info[key] = {
                "Max Power (MW)": max_power,
                "Min Power (MW)": min_power,
                "Minimum Uptime (h)": min_uptime,
                "Minimum Downtime (h)": min_downtime
            }


for key, values in cadunidt_info.items():
    if key in json_data["Thermal Generators"]:
        json_data["Thermal Generators"][key].update(values)


'''
Thermal Generators: Initial Power (MW); Initial Status (h);
'''

file_path = FOLDER_PATH + FILE_THERMAL_OPERATION
processing = False

with open(file_path, 'r', encoding='ISO-8859-1') as file:
    for line in file:
        if "INIT" in line:
            processing = True
            continue
        if "FIM" in line:
            break
        if processing and line.strip() and not line.strip().startswith('&'):
            key = line[0:3].strip()
            initial_power = float(line[29:39].strip())
            initial_status = int(line[41:46].strip())
            status_sign = -1 if line[24:26].strip() == "0" else 1
            initial_status *= status_sign
            ucterm_info[key] = {
                "Initial Power (MW)": initial_power,
                "Initial Status (h)": initial_status
            }


for key, values in ucterm_info.items():
    if key in json_data["Thermal Generators"]:
        json_data["Thermal Generators"][key].update(values)

'''
Thermal Generators: Production cost curve ($);
'''

with open(file_path, 'r', encoding='ISO-8859-1') as file:
    for line in file:
        if line.startswith('OPER') or line.startswith('&'):
            continue
        if line.strip():
            unit_id = line[0:3].strip()
            if unit_id not in processed_units:
                if line[56:66].strip().replace('.', '', 1).isdigit():
                    cost = float(line[56:66].strip())
                    oper_info[unit_id] = {
                        "Production cost curve ($)": [0, cost, 0]
                    }
                    processed_units.add(unit_id)


for key, values in oper_info.items():
    if key in json_data["Thermal Generators"]:
        json_data["Thermal Generators"][key].update(values)

'''Thermal Generators: Bus'''

file_path = FOLDER_PATH + FILE_NETWORK_DATA
reading = False
with open(file_path, 'r', encoding='ISO-8859-1') as file:
    for line in file:
        if '( Arquivos de caso base' in line:
            reading = True
            continue
        if '99999' in line and reading:
            break
        if '(### (Id C. Base)' in line:
            continue
        if reading:
            FILE_BASE_NETWORK = line[19:54].strip()
            break

file_path = FOLDER_PATH + FILE_BASE_NETWORK
reading = False
with open(file_path, 'r', encoding='ISO-8859-1') as file:
    for line in file:
        if 'DUSI' in line:
            reading = True
            continue
        if '99999' in line and reading:
            break
        if '(No) O( No)' in line:
            continue
        if reading:
            if line.strip() and line[77:78] == 'T':
                no_dessem = int(line[73:76].strip())
                bus = int(line[6:10].strip())
                dusi_info[no_dessem] = {"Bus": bus}

for key, values in json_data["Thermal Generators"].items():
    no_dessem = values.get("No DESSEM")
    if no_dessem in dusi_info:
        json_data["Thermal Generators"][key].update({"Bus": dusi_info[no_dessem]["Bus"]})

'''Hydro Generators: Bus'''

file_path = FOLDER_PATH + FILE_BASE_NETWORK
reading = False
with open(file_path, 'r', encoding='ISO-8859-1') as file:
    for line in file:
        if line.startswith('DUSI'):
            reading = True
            continue
        if line.startswith('99999') and reading == True:
            break
        if '(No) O( No)' in line:
            continue
        if reading:
            if line.strip() and line[77:78] == 'H':
                no_dessem = int(line[73:76].strip())
                if no_dessem not in processed_dessem:
                    bus = int(line[6:10].strip())
                    dusi_hydro_info[no_dessem] = {"Bus": bus}
                    processed_dessem.add(no_dessem)

for key, values in json_data["Hydro Generators"].items():
    no_dessem = values.get("No DESSEM")
    if no_dessem in dusi_hydro_info:
        json_data["Hydro Generators"][key].update({"Bus": dusi_hydro_info[no_dessem]["Bus"]})

'''Hydro Generators: Upriver; Downriver; Traveltime (h); '''

file_path = FOLDER_PATH + FILE_INPUT_DATA

with open(file_path, 'r', encoding='ISO-8859-1') as file:
    for line in file:
        if line.startswith('TVIAG'):
            no_dessem = int(line[6:9].strip())
            downriver = int(line[10:13].strip())
            travel_time = int(line[19:22].strip())
            tviag_info[no_dessem] = {
                "Upriver": "", 
                "Downriver": downriver,
                "Traveltime (h)": travel_time
            }

for key, values in json_data["Hydro Generators"].items():
    no_dessem = values.get("No DESSEM")
    if no_dessem in tviag_info:
        json_data["Hydro Generators"][key].update(tviag_info[no_dessem])
    else:
        json_data["Hydro Generators"][key].update({
            "Upriver": "",
            "Downriver": 0,
            "Traveltime (h)": 0
        })

'''Hydro Generators:
                Max Power (MW)
                Min Power (MW)
                Status
                Max Volume (hm3)
                Min Volume (hm3)
                Max Spillage (m3/s)
                Max Turbined Outflow (m3/s)
                Min Turbined Outflow (m3/s)
                Productibility (MW/m3/s)
                Type
'''

file_path = FOLDER_PATH + FILE_HYDRO_DATA

columns_of_interest = [
    "CodUsina", "Usina", "Jusante", "Vol.Máx.(hm3)", "Vol.min.(hm3)", 
    "Prod.Esp.(MW/m3/s/m)", "Num.Conj.Máq.", "#Maq(1)", "PotEf(1)", "QEf(1)",
    "#Maq(2)", "PotEf(2)", "QEf(2)", "#Maq(3)", "PotEf(3)", "QEf(3)",
    "#Maq(4)", "PotEf(4)", "QEf(4)", "#Maq(5)", "PotEf(5)", "QEf(5)", "Reg"
]

try:
    data = pd.read_csv(file_path, delimiter=';', encoding='ISO-8859-1')
    selected_data = data[columns_of_interest]
    success = True
except Exception as e:
    success = False
    error = e

selected_data if success else error

usinas_dict = selected_data.to_dict(orient='index')

def convert_to_float(str_number):
    return float(str_number.replace(',', '.')) if str_number else 0.0

for key, values in json_data["Hydro Generators"].items():
    no_dessem = values.get("No DESSEM")
    for usina in usinas_dict.values():
        if usina['CodUsina'] == no_dessem:
            max_power = sum(usina[f'#Maq({i})'] * convert_to_float(usina[f'PotEf({i})']) for i in range(1, 6))
            max_turbined_outflow = sum(usina[f'#Maq({i})'] * usina[f'QEf({i})'] for i in range(1, 6))
            json_data["Hydro Generators"][key].update({
                "Max Power (MW)": max_power,
                "Min Power (MW)": 0,
                "Status": 1,
                "Max Volume (hm3)": usina['Vol.Máx.(hm3)'],
                "Min Volume (hm3)": usina['Vol.min.(hm3)'],
                "Max Spillage (m3/s)": "INF",
                "Max Turbined Outflow (m3/s)": max_turbined_outflow,
                "Min Turbined Outflow (m3/s)": 0,
                "Productibility (MW/m3/s)": convert_to_float(usina['Prod.Esp.(MW/m3/s/m)']),
                "Type": usina['Reg']
            })
            break

'''Hydro Generators:
            Inflows (m3/s)
            Initial Inflow (m3/s)
            Initial Turbined Outflow (m3/s)
            Initial Spillage (m3/s)
'''

file_path = FOLDER_PATH + FILE_INFLOWS

reading = False
ignore_header = True

with open(file_path, 'r', encoding='ISO-8859-1') as file:
    for line in file:
        if line.startswith('VAZOES DIARIAS'):
            reading = True
            continue
        if line.startswith('FIM') and reading == True:
            break
        if reading and not ignore_header:
            try:
                no_dessem = int(line[0:3].strip())
                inflow = float(line[44:53].strip())
                inflows_data_corrected_v2.append((no_dessem, inflow))
            except ValueError:
                continue
        if reading:
            ignore_header = False

for no_dessem, inflow in inflows_data_corrected_v2:
    for key, hydro_generator in json_data["Hydro Generators"].items():
        if hydro_generator.get("No DESSEM") == no_dessem:
            hydro_generator["Inflows (m3/s)"] = inflow
            break

for key in json_data["Hydro Generators"]:
    json_data["Hydro Generators"][key].update({
        "Initial Inflow (m3/s)": 0,
        "Initial Turbined Outflow (m3/s)": 0,
        "Initial Spillage (m3/s)": 0
    })
   
''' Transmission Lines:             
            Source bus
            Target bus
            R (pu)
            X (pu)
            B (pu)
            Status
            Normal flow limit (MVA)
            Emergency flow limit (MVA)
            Flow limit penalty ($/MVA)

'''
file_path = FOLDER_PATH + FILE_BASE_NETWORK
    

reading = False
line_number = 1

with open(file_path, 'r', encoding='ISO-8859-1') as file:
    for line in file:
        if 'DLIN' in line and not reading:
            reading = True
            continue
        if '99999' in line and reading:
            break
        if reading:
            if '(De )d O' in line:
                continue
            source_bus = int(line[0:5].strip())
            target_bus = int(line[10:15].strip())
            r_pu = float(line[20:26].strip()) / 100
            x_pu = float(line[26:32].strip()) / 100
            b_pu = float(line[32:38].strip()) / 100
            normal_flow_limit = float(line[64:68].strip())
            transmission_lines_data[str(line_number)] = {
                "Source bus": source_bus,
                "Target bus": target_bus,
                "R (pu)": r_pu,
                "X (pu)": x_pu,
                "B (pu)": b_pu,
                "Status": 1,
                "Normal flow limit (MVA)": normal_flow_limit,
                "Emergency flow limit (MVA)": normal_flow_limit,
                "Flow limit penalty ($/MVA)": normal_flow_limit
            }
            line_number += 1

json_data["Transmission lines"] = transmission_lines_data

''' Buses: 
                Name
                Type
                Area
                Maximum Voltage
                Minimum Voltage
                Load (MW)
'''
file_path = FOLDER_PATH + FILE_BASE_NETWORK

reading = False
bus_number = 1

with open(file_path, 'r', encoding='ISO-8859-1') as file:
    for line in file:
        if 'DBAR' in line and not reading:
            reading = True
            continue
        if '99999' in line and reading:
            break
        if reading:
            if '(Num)OETGb' in line:
                continue
            bus_name = line[10:22].strip()
            bus_type = "REF" if line[5:10].strip() == "2G" else "PVQ"
            bus_area = int(line[73:76].strip())
            max_voltage = float(line[24:28].strip())

            buses_data[str(bus_number)] = {
                "Name": bus_name,
                "Type": bus_type,
                "Area": bus_area,
                "Maximum Voltage": max_voltage,
                "Minimum Voltage": 0.85,
                "Load (MW)": 0
            }
            bus_number += 1

json_data["Buses"] = buses_data

'''Buses: Load (MW) '''

file_path = FOLDER_PATH + FILE_INPUT_DATA

with open(file_path, 'r') as file:
    for line in file:
        if line.startswith('TM'):
            extracted_data = line[33:39].strip()
            patamar.append(extracted_data)

file_path = FOLDER_PATH + FILE_NETWORK_DATA

reading = False
with open(file_path, 'r', encoding='ISO-8859-1') as file:
    for line in file:
        if '( Arquivos de caso base' in line:
            reading = True
            continue
        if '99999' in line and reading:
            break
        if '(### (Id C. Base)' in line:
            continue
        if reading:
            id_int = int(line[0:5].strip())
            patamar_nome = line[5:17].strip()
            arquivo_nome = line[19:54].strip()
            patamares_info.append((id_int, patamar_nome, arquivo_nome))

patamar_para_id = {nome: id_int for (id_int, nome, _) in patamares_info}
patamar_int = [patamar_para_id[pat] for pat in patamar]

for period, patamar_id in enumerate(patamar_int, start=1):
    arquivo_nome = next((arq for id, pat, arq in patamares_info if id == patamar_id), None)

    if arquivo_nome:
        file_path = os.path.join(FOLDER_PATH, arquivo_nome)
        demandas = []
        with open(file_path, 'r', encoding='ISO-8859-1') as file:
            reading = False
            for line in file:
                if 'DBAR' in line:
                    reading = True
                    continue
                if '99999' in line and reading:
                    break
                if reading:
                    try:
                        demanda_ = float(line[58:63].strip())
                        demandas.append(demanda_)
                    except ValueError:
                        continue
        load_mw[f"period_{period}"] = demandas

load_matrix = np.array([demands for demands in load_mw.values()])
load = load_matrix.T

file_path = FOLDER_PATH + FILE_NETWORK_DATA
with open(file_path, 'r', encoding='ISO-8859-1') as file:
    reading = False
    for line in file:
        if '( Alteracoes dos casos base' in line:
            reading = True
            continue
        if '(###' in line:
            continue
        if reading:
            if line.strip() == '':
                continue
            elif '99999' in line:
                break
            else:
                extracted_content = line[45:67].strip()
                arq_patamar.append(extracted_content)

for period, arquivo in enumerate(arq_patamar):
    file_path = os.path.join(FOLDER_PATH, arquivo)
    temp_patamar_muda = []
    try:
        with open(file_path, 'r', encoding='ISO-8859-1') as file:
            reading = False
            for line in file:
                if 'DANC' in line:
                    reading = True
                    continue
                if '99999' in line and reading:
                    break
                if reading:
                    try:
                        area_str = line[0:3].strip()
                        factor_str = line[4:10].strip()

                        if area_str.isdigit() and factor_str.replace('.', '', 1).isdigit():
                            area = int(area_str)
                            factor = float(factor_str)
                            temp_patamar_muda.append((area, factor))
                    except ValueError:
                        continue
        patamar_muda.append(temp_patamar_muda)

    except FileNotFoundError:
        print(f"Arquivo {arquivo} não encontrado. Continuando com o próximo.")


json_buses = json_data.get("Buses", {})

for period in range(len(patamar_int)):
    current_patamar_muda = patamar_muda[period] if period < len(patamar_muda) else []

    for bus_str, bus_info in json_buses.items():
        bus = int(bus_str) - 1
        area = bus_info.get("Area", None)

        pos = next((i for i, (a, _) in enumerate(current_patamar_muda) if a == area), None)
        if pos is not None:
            load[bus, period] *= current_patamar_muda[pos][1] / 100


for bus in range(len(load)):
    bus_str = str(bus + 1)
    if bus_str in json_buses:
        json_data["Buses"][bus_str]["Load (MW)"] = load[bus, :].tolist()

with open(output_file_path, 'w') as file:
    json.dump(json_data, file, indent=4)