import json
from pathlib import Path
import copy
from datetime import datetime
from functions.utils import *
from shiny import App, reactive, render, ui

refresh_time = 90 #seconds

list_municipios = get_config_municipios()

list_states = group_states_by_region(copy.deepcopy(list_municipios))


app_ui = ui.page_fluid(
    ui.include_css(Path(__file__).parent / 'styles.css'),
    ui.row(
        ui.column(
            9,
            ui.h1("Apuração Eleições 2024", style="align:center")
        ),
        ui.column(
            3,
            ui.output_text("next_update_in")
        )   
    ),
    ui.hr(),
    ui.row(
        ui.column(
            3,
            ui.input_selectize(
                "select_state",
                "Selecione o Estado: ",
                choices = list_states,
                selected="sp",
                multiple=False
            ),
            ui.input_selectize(
                "select_municipality",
                "Selecione o Municipio: ",
                choices = get_municipality_by_state(list_municipios, "sp"),
                multiple=False
            ),
            ui.output_text("perc_secoes_concluidas"),
            ui.layout_column_wrap(
                ui.value_box(
                    "Número de Eleitores",
                    ui.output_text("numero_eleitorado"),
                    theme="bg-gradient-orange-red",
                    full_screen=False,
                ),
                ui.value_box(
                    "Abstenções",
                    ui.output_text("abstencoes"),
                    theme="bg-gradient-orange-red",
                    full_screen=False,
                )
            ),
            ui.layout_column_wrap(
                ui.value_box(
                    "Número de Votos Válidos",
                    ui.output_text("numero_votos_validos"),
                    theme="bg-gradient-orange-red",
                    full_screen=False,
                )
            ),
            ui.layout_column_wrap(
                ui.value_box(
                    "Votos Nulos",
                    ui.output_text("votos_nulos"),
                    theme="bg-gradient-orange-red",
                    full_screen=False,
                ),
                ui.value_box(
                    "Votos Brancos",
                    ui.output_text("votos_brancos"),
                    theme="bg-gradient-orange-red",
                    full_screen=False,
                )
            )
        ),
        ui.column(
            9,
            ui.navset_tab(
                ui.nav_panel(
                    "Prefeito",
                    ui.output_text_verbatim("refresh_prefeito"),
                    "Prefeito"
                ),
                ui.nav_panel(
                    "Vereador",
                    ui.output_text_verbatim("refresh_vereador"),
                    "Vereador"
                )
            ),
            ui.output_text_verbatim("txt"),
        )
    )
    
)


def server(input, output, session):

    #app starter
    data_prefeito = reactive.value(get_municipios_data(ano="2022", cod_cargo="0001", cod_eleicao="544", cod_mun_tse="85995", env="oficial", state="rs"))
    data_vereador = reactive.value(get_municipios_data(ano="2022", cod_cargo="0001", cod_eleicao="545", cod_mun_tse="85995", env="oficial", state="rs"))

    @reactive.effect
    def _():
        selected_state = input.select_state()

        ui.update_selectize(
            "select_municipality",
            choices=get_municipality_by_state(list_municipios, selected_state)
        )

    @render.text
    def perc_secoes_concluidas():
        return f"Percentual de seções totalizadas: {data_prefeito()['pst']} %"
    
    @render.text
    def numero_eleitorado():
        return f"{data_prefeito()['e']}"
    
    @render.text
    def numero_votos_validos():
        return f"{data_prefeito()['vv']}"
    
    @render.text
    def abstencoes():
        return f"{data_prefeito()['pa']}% ({data_prefeito()['a']} eleitores)"
    
    @render.text
    def votos_brancos():
        return f"{data_prefeito()['pvb']}% ({data_prefeito()['vb']} eleitores)"
    
    @render.text
    def votos_nulos():
        return f"{data_prefeito()['ptvn']}% ({data_prefeito()['vn']} eleitores)"


    @render.text
    def next_update_in():

        reactive.invalidate_later(1)

        minutes, seconds = calculate_time_difference(data_prefeito()['timestamp'], refresh_time=refresh_time)

        return f"Próxima atualização: {minutes}m e {seconds}s"

    @render.text
    def refresh_prefeito():
        reactive.invalidate_later(refresh_time)
        data_prefeito.set(get_municipios_data(ano="2022", cod_cargo="0001", cod_eleicao="544", cod_mun_tse=input.select_municipality(), env="oficial", state=input.select_state()))
        return f"{data_prefeito()['timestamp']}"
    
    @render.text
    def refresh_vereador():
        reactive.invalidate_later(refresh_time)
        data_vereador.set(get_municipios_data(ano="2022", cod_cargo="0001", cod_eleicao="545", cod_mun_tse=input.select_municipality(), env="oficial", state=input.select_state()))
        return f"{data_vereador()['timestamp']}"
    


app = App(app_ui, server)
