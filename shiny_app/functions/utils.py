from datetime import datetime
from typing import Dict, List

import requests
from shiny import ui

empty_dict = {
    "s": {"pst": "0"},
    "e": {
        "te": 0,
        "a": 0,
        "pa": 0,
    },
    "v": {
        "vv": 0,
        "pvtn": 0,
        "vn": 0,
        "pvb": 0,
        "vb": 0,
    },
    "cand": []
}


def calculate_time_difference(input_time, refresh_time):
    timestamp = datetime.fromisoformat(input_time)
    now = datetime.now()

    time_difference = now - timestamp

    total_seconds = int(refresh_time - time_difference.total_seconds())
    minutes = total_seconds // 60
    seconds = total_seconds % 60

    return minutes, seconds


def get_config_municipios(
    base_url:str = "https://resultados.tse.jus.br", cod_eleicao: str = "544", env: str = "oficial", ano: str = "2022"
) -> List[Dict]:
    
    req_url = (
        f"{base_url}/{env}/ele{ano}/{cod_eleicao}/config/mun-e{cod_eleicao.zfill(6)}-cm.json"
    )

    try:
        req_tse = requests.get(req_url)
        req_tse.raise_for_status()  # Check if the request was successful
        req_tse_dict = req_tse.json()  # Directly parse JSON response
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return []  # Return empty list on failure

    list_mun = req_tse_dict.get("abr", [])
    return list_mun

def handle_failure():
    return {**empty_dict, "timestamp": datetime.now().isoformat()}

def create_cand_structure(cand):
    # Simplify the creation of candidate structure
    ret_dict = cand["par"][0]["cand"]
    ret_dict_partido = [{**cand_dict, "nm_partido": cand["nm"]} for cand_dict in ret_dict]
    return ret_dict_partido

def remove_municipality_from_states(list_mun):
    for state_dict in list_mun:
        if "mu" in state_dict:
            del state_dict["mu"]
    return list_mun


def group_states_by_region(list_mun_og):

    list_mun = remove_municipality_from_states(list_mun_og)

    regions = {
        "Norte": [],
        "Nordeste": [],
        "Centro-Oeste": [],
        "Sudeste": [],
        "Sul": [],
    }
    state_to_region = {
        "AC": "Norte",
        "AL": "Nordeste",
        "AM": "Norte",
        "AP": "Norte",
        "BA": "Nordeste",
        "CE": "Nordeste",
        "DF": "Centro-Oeste",
        "ES": "Sudeste",
        "GO": "Centro-Oeste",
        "MA": "Nordeste",
        "MT": "Centro-Oeste",
        "MS": "Centro-Oeste",
        "MG": "Sudeste",
        "PA": "Norte",
        "PB": "Nordeste",
        "PR": "Sul",
        "PE": "Nordeste",
        "PI": "Nordeste",
        "RJ": "Sudeste",
        "RN": "Nordeste",
        "RO": "Norte",
        "RS": "Sul",
        "RR": "Norte",
        "SC": "Sul",
        "SE": "Nordeste",
        "SP": "Sudeste",
        "TO": "Norte",
    }

    for state_dict in list_mun:
        state_code = state_dict.get("cd")  # Assuming 'cd' is the state code
        region = state_to_region.get(state_code.upper(), "Unknown")

        # Only add to the region if it's recognized
        if region != "Unknown":
            regions[region].append(state_dict)

    transformed_dict = {}

    for region, states in regions.items():
        # Initialize an empty dictionary for the region
        transformed_dict[region] = {}

        # Loop through the states and build the desired key-value pairs
        for state in states:
            state_code = state["cd"].lower()  # Convert state code to lowercase
            state_name = state["ds"]
            transformed_dict[region][
                state_code
            ] = f"{state_code.upper()}-{state_name.upper()}"

    return transformed_dict

def get_municipality_by_state(list_mun, selected_state: str):

    state = next((x for x in list_mun if x.get("cd") == selected_state.upper()), {})

    ret_dict = {}

    for city in state["mu"]:
        ret_dict[city["cd"]] = city["nm"]

    return ret_dict


def get_municipios_data(
    cod_eleicao: str,
    cod_mun_tse: str,
    cod_cargo: str,
    state: str,
    base_url:str = "https://resultados.tse.jus.br",
    env: str = "oficial",
    ano: str = "2022",
) -> Dict:
    state = state.lower()

    req_url = f"{base_url}/{env}/ele{ano}/{cod_eleicao}/dados/{state}/{state}{cod_mun_tse}-c{cod_cargo}-e{cod_eleicao.zfill(6)}-u.json"

    try:
        req_tse = requests.get(req_url)
        req_tse.raise_for_status()
        req_tse_dict = req_tse.json()
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return handle_failure()

    if req_tse_dict:
        list_cand_partidos = [create_cand_structure(candidate) for candidate in req_tse_dict["carg"][0]["agr"]]
        req_tse_dict["cand"] = [item for sublist in list_cand_partidos for item in sublist]
        req_tse_dict["timestamp"] = datetime.now().isoformat()
        del req_tse_dict["carg"]
    else:
        return handle_failure()

    return req_tse_dict

def card_candidato(
    img_candidato: str, name_candidato: str, progress: float, votos: int
):

    html_string = f"""
        <div class="card-candidato">
        <img src="{img_candidato}" alt="Candidate Image">
        <div class="card-candidato-content">
            <h3>{name_candidato}</h3>
            <div class="progress-bar-container">
                <div class="progress-bar" style="width:{progress}%;"></div>
                <span class="progress-value">{votos:,} votos - {progress}%</span>
            </div>
        </div>
    </div>
    """
    return html_string


def card_secoes(title: str, progress: float):

    html_string = f"""
        <div class="card-secoes">
        <div class="card-secoes-content">
            <h3>{title}</h3>
            <div class="progress-bar-container-secoes">
                <div class="progress-bar-secoes" style="width:{progress}%;">{progress}%</div>
            </div>
        </div>
        </div>
    """
    return html_string
