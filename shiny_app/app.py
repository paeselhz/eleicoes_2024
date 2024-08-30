import json
import copy
from datetime import datetime
from functions.utils import *
from shiny import App, reactive, render, ui

refresh_time = 90 #seconds

list_municipios = get_config_municipios()

list_states = group_states_by_region(copy.deepcopy(list_municipios))


app_ui = ui.page_fluid(
    ui.row(
        ui.column(
            3,
            ui.input_select(
                "select_state",
                "Selecione o Estado: ",
                choices = list_states,
                selected="sp"
            ),
            ui.input_select(
                "select_municipality",
                "Selecione o Municipio: ",
                choices = get_municipality_by_state(list_municipios, "sp")
            )
        ),
        ui.column(
            9,
            ui.output_text_verbatim("txt"),
            ui.output_text_verbatim("diff"),
        )
    )
    
)


def server(input, output, session):

    @reactive.effect
    def _():
        x = input.select_state()

        ui.update_select(
            "select_municipality",
            choices=get_municipality_by_state(list_municipios, x)
        )

    ret_dict = reactive.value(get_municipios_data(ano="2022", cod_cargo="0001", cod_eleicao="544", cod_mun_tse="85995", env="oficial", state="rs"))

    @render.text
    def diff():

        reactive.invalidate_later(1)

        minutes, seconds = calculate_time_difference(ret_dict()['timestamp'], refresh_time=refresh_time)

        return f"Difference: {minutes} and {seconds} seconds"


    @render.text
    def txt():
        reactive.invalidate_later(refresh_time)
        ret_dict.set(get_municipios_data(ano="2022", cod_cargo="0001", cod_eleicao="544", cod_mun_tse=input.select_municipality(), env="oficial", state=input.select_state()))
        return json.dumps(ret_dict())


app = App(app_ui, server)
