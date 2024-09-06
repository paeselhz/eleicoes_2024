import copy
import json
from datetime import datetime
from pathlib import Path

from functions.utils import *
from shiny import App, reactive, render, ui

refresh_time = 90  # seconds

list_municipios = get_config_municipios()

list_states = group_states_by_region(copy.deepcopy(list_municipios))


app_ui = ui.page_fluid(
    ui.include_css(Path(__file__).parent / "styles.css"),
    ui.row(
        ui.column(9, ui.h1("Apuração Eleições 2024")),
        ui.column(3, ui.output_text("next_update_in")),
    ),
    ui.hr(),
    ui.row(
        ui.column(
            3,
            ui.input_selectize(
                "select_state",
                "Selecione o Estado: ",
                choices=list_states,
                selected="sp",
                multiple=False,
            ),
            ui.input_selectize(
                "select_municipality",
                "Selecione o Municipio: ",
                choices=get_municipality_by_state(list_municipios, "sp"),
                multiple=False,
            ),
            ui.output_ui("side_cards_kpi"),
        ),
        ui.column(
            9,
            ui.output_ui("perc_secoes_card"),
            ui.row(
                ui.column(
                    6,
                    ui.output_text_verbatim("refresh_prefeito"),
                    ui.output_ui("prefeito_ui"),
                    class_="col-sm-6 column-prefeito",
                ),
                ui.column(
                    6,
                    ui.output_text_verbatim("refresh_vereador"),
                    ui.output_ui("vereador_ui"),
                    class_="col-sm-6 column-vereador",
                ),
                class_="g-5",
            ),
        ),
        class_="g-5",
    ),
)


def server(input, output, session):

    # app starter
    data_prefeito = reactive.value(
        get_municipios_data(
            ano="2022",
            cod_cargo="0001",
            cod_eleicao="544",
            cod_mun_tse="85995",
            env="oficial",
            state="rs",
        )
    )
    data_vereador = reactive.value(
        get_municipios_data(
            ano="2022",
            cod_cargo="0001",
            cod_eleicao="545",
            cod_mun_tse="85995",
            env="oficial",
            state="rs",
        )
    )

    @reactive.effect
    def _():
        selected_state = input.select_state()

        if selected_state != "":
            ui.update_selectize(
                "select_municipality",
                choices=get_municipality_by_state(list_municipios, selected_state),
            )

    @render.ui
    def perc_secoes_card():
        return ui.HTML(card_secoes(float(data_prefeito()["pst"].replace(",", "."))))

    @render.text
    def next_update_in():

        reactive.invalidate_later(1)

        minutes, seconds = calculate_time_difference(
            data_prefeito()["timestamp"], refresh_time=refresh_time
        )

        return f"Próxima atualização: {minutes}m e {seconds}s"

    @render.text
    def refresh_prefeito():
        reactive.invalidate_later(refresh_time)
        data_prefeito.set(
            get_municipios_data(
                ano="2022",
                cod_cargo="0001",
                cod_eleicao="544",
                cod_mun_tse=input.select_municipality(),
                env="oficial",
                state=input.select_state(),
            )
        )
        return f"{data_prefeito()['timestamp']}"

    @render.text
    def refresh_vereador():
        reactive.invalidate_later(refresh_time)
        data_vereador.set(
            get_municipios_data(
                ano="2022",
                cod_cargo="0001",
                cod_eleicao="545",
                cod_mun_tse=input.select_municipality(),
                env="oficial",
                state=input.select_state(),
            )
        )
        return f"{data_vereador()['timestamp']}"

    @render.text
    def votos_nulos():
        return

    @render.ui
    def side_cards_kpi():
        return [
            ui.layout_column_wrap(
                ui.value_box(
                    "Número de Eleitores",
                    f"{int(data_prefeito()['e']):,}",
                    theme="bg-gradient-orange-red",
                    full_screen=False,
                ),
                ui.value_box(
                    "Abstenções",
                    f"{data_prefeito()['pa']}% ({int(data_prefeito()['a']):,} eleitores)",
                    theme="bg-gradient-orange-red",
                    full_screen=False,
                ),
            ),
            ui.layout_column_wrap(
                ui.value_box(
                    "Número de Votos Válidos",
                    f"{int(data_prefeito()['vv']):,}",
                    theme="bg-gradient-orange-red",
                    full_screen=False,
                )
            ),
            ui.layout_column_wrap(
                ui.value_box(
                    "Votos Nulos",
                    f"{data_prefeito()['ptvn']}% ({int(data_prefeito()['vn']):,} eleitores)",
                    theme="bg-gradient-orange-red",
                    full_screen=False,
                ),
                ui.value_box(
                    "Votos Brancos",
                    f"{data_prefeito()['pvb']}% ({int(data_prefeito()['vb']):,} eleitores)",
                    theme="bg-gradient-orange-red",
                    full_screen=False,
                ),
            ),
        ]

    @render.ui
    def prefeito_ui():
        return [
            ui.HTML(
                card_candidato(
                    "https://via.placeholder.com/60", "Candidato Prefeito 1", 55
                )
            ),
            ui.HTML(
                card_candidato(
                    "https://via.placeholder.com/60", "Candidato Prefeito 2", 45
                )
            ),
        ]

    @render.ui
    def vereador_ui():
        return [
            ui.HTML(
                card_candidato(
                    "https://via.placeholder.com/60", "Candidato Vereador 1", 42
                )
            ),
            ui.HTML(
                card_candidato(
                    "https://via.placeholder.com/60", "Candidato Vereador 2", 31
                )
            ),
            ui.HTML(
                card_candidato(
                    "https://via.placeholder.com/60", "Candidato Vereador 3", 27
                )
            ),
        ]


app = App(app_ui, server)
