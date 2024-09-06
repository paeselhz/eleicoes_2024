from datetime import datetime
from typing import Dict, List

import requests
from shiny import ui


def calculate_time_difference(input_time, refresh_time):
    timestamp = datetime.fromisoformat(input_time)
    now = datetime.now()

    time_difference = now - timestamp

    total_seconds = int(refresh_time - time_difference.total_seconds())
    minutes = total_seconds // 60
    seconds = total_seconds % 60

    return minutes, seconds


def get_config_municipios(
    cod_eleicao: str = "544", env: str = "oficial", ano: str = "2022"
) -> List[Dict]:
    base_url = "https://resultados.tse.jus.br"
    req_url = (
        f"{base_url}/{env}/ele{ano}/{cod_eleicao}/config/mun-e000{cod_eleicao}-cm.json"
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
        region = state_to_region.get(state_code, "Unknown")

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
    cod_mun_tse: int,
    cod_cargo: str,
    state: str,
    env: str = "oficial",
    ano: str = "2022",
) -> Dict:
    base_url = "https://resultados.tse.jus.br"
    state = state.lower()

    req_url = f"{base_url}/{env}/ele{ano}/{cod_eleicao}/dados/{state}/{state}{cod_mun_tse}-c{cod_cargo}-e000{cod_eleicao}-v.json"

    try:
        req_tse = requests.get(req_url)
        req_tse.raise_for_status()  # Check if the request was successful
        req_tse_dict = req_tse.json()  # Directly parse JSON response
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return {}  # Return empty dict on failure

    dados_mun = next(
        (x for x in req_tse_dict.get("abr", []) if x.get("tpabr") == "MU"), {}
    )
    if dados_mun:
        dados_mun["md"] = req_tse_dict.get("md")
        dados_mun["timestamp"] = datetime.now().isoformat()

    return dados_mun


def card_candidato(img_candidato: str, name_candidato: str, progress: float):

    html_string = f"""
        <div class="card-candidato">
        <img src="{img_candidato}" alt="Candidate Image">
        <div class="card-candidato-content">
            <h3>{name_candidato}</h3>
            <div class="progress-bar-container">
                <div class="progress-bar" style="width:{progress}%;">{progress}%</div>
            </div>
        </div>
    </div>
    """
    return html_string


def card_secoes(progress: float):

    html_string = f"""
        <div class="card-secoes">
        <div class="card-secoes-content">
            <h3>Percentual de seções totalizadas</h3>
            <div class="progress-bar-container-secoes">
                <div class="progress-bar-secoes" style="width:{progress}%;">{progress}%</div>
            </div>
        </div>
        </div>
    """
    return html_string
