import copy
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pyperclip3
from functions.icons import *
from functions.utils import *
from shiny import App, reactive, render, ui

refresh_time = 90  # seconds

list_municipios = get_config_municipios()

list_states = group_states_by_region(copy.deepcopy(list_municipios))


app_ui = ui.page_fluid(
    ui.include_css(Path(__file__).parent / "styles.css"),
    ui.row(
        ui.column(
            3,
            ui.input_action_button("share_button", "Compartilhe...", icon=share_icon),
            class_="d-flex justify-content-center",
        ),
        ui.column(6, ui.h1("Apuração Eleições 2024")),
        ui.column(3, ui.output_text("next_update_in")),
        style="margin-top:1rem;",
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
                    ui.h3("Prefeito"),
                    ui.output_text_verbatim("refresh_prefeito"),
                    ui.output_ui("prefeito_ui"),
                    class_="col-sm-6 column-prefeito",
                ),
                ui.column(
                    6,
                    ui.h3("Vereador"),
                    ui.output_text_verbatim("refresh_vereador"),
                    ui.output_ui("vereador_ui"),
                    class_="col-sm-6 column-vereador",
                ),
                style="height: 70vh;",
            ),
        ),
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
            cod_cargo="0003",
            cod_eleicao="546",
            cod_mun_tse="85995",
            env="oficial",
            state="rs",
        )
    )
    onstartup = reactive.value(True)

    @reactive.effect
    @reactive.event(input.select_state)
    def _():
        selected_state = input.select_state()

        url_query_inputs = session.input[".clientdata_url_search"]()

        parsed_qs = parse_qs(urlparse(url_query_inputs).query)

        if onstartup():
            if parsed_qs.get("uf") is not None:
                ui.update_selectize("select_state", selected=parsed_qs["uf"][0])
            else:
                onstartup.set(False)
            if parsed_qs.get("mu") is not None:
                ui.update_selectize(
                    "select_municipality",
                    selected=parsed_qs["mu"][0],
                    choices=get_municipality_by_state(list_municipios, selected_state),
                )
                if selected_state == parsed_qs["uf"][0]:
                    onstartup.set(False)
        else:
            if selected_state != "":
                ui.update_selectize(
                    "select_municipality",
                    choices=get_municipality_by_state(list_municipios, selected_state),
                )

    @reactive.effect
    @reactive.event(input.share_button)
    def _():
        share_modal = ui.modal(
            ui.row(
                ui.column(12, ui.output_text_verbatim("modal_link")),
                # ui.column(4, ui.input_action_button("copy_link", "Copiar link!")),
            ),
            title="Compartilhe!",
            easy_close=True,
            footer=None,
        )
        ui.modal_show(share_modal)

    @render.text
    def modal_link():
        return f"https://paeselhz.github.io/eleicoes_2024/?uf={input.select_state()}&mu={input.select_municipality()}"

    @reactive.effect
    @reactive.event(input.copy_link)
    def copy_link():
        pyperclip3.copy(
            f"https://paeselhz.github.io/eleicoes_2024/?uf={input.select_state()}&mu={input.select_municipality()}"
        )

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
                cod_cargo="0003",
                cod_eleicao="546",
                cod_mun_tse=input.select_municipality(),
                env="oficial",
                state=input.select_state(),
            )
        )
        return f"{data_vereador()['timestamp']}"

    @render.ui
    def side_cards_kpi():
        return [
            ui.layout_column_wrap(
                ui.value_box(
                    "Número de Eleitores",
                    f"{int(data_prefeito()['e']):,}",
                    theme="bg-gradient-purple-teal",
                    full_screen=False,
                ),
                ui.value_box(
                    "Abstenções",
                    f"{data_prefeito()['pa']}% ({int(data_prefeito()['a']):,} eleitores)",
                    theme="bg-gradient-purple-teal",
                    full_screen=False,
                ),
            ),
            ui.layout_column_wrap(
                ui.value_box(
                    "Número de Votos Válidos",
                    f"{int(data_prefeito()['vv']):,}",
                    theme="bg-gradient-purple-teal",
                    full_screen=False,
                )
            ),
            ui.layout_column_wrap(
                ui.value_box(
                    "Votos Nulos",
                    f"{data_prefeito()['ptvn']}% ({int(data_prefeito()['vn']):,} eleitores)",
                    theme="bg-gradient-purple-teal",
                    full_screen=False,
                ),
                ui.value_box(
                    "Votos Brancos",
                    f"{data_prefeito()['pvb']}% ({int(data_prefeito()['vb']):,} eleitores)",
                    theme="bg-gradient-purple-teal",
                    full_screen=False,
                ),
            ),
        ]

    @render.ui
    def perc_secoes_card():

        selected_state = input.select_state()
        selected_mun = input.select_municipality()

        try:
            name_mun = (
                get_municipality_by_state(list_municipios, selected_state)[selected_mun]
                + " - "
                + selected_state.upper()
            )
        except:
            name_mun = ""

        return ui.HTML(
            card_secoes(
                f"Percentual de seções totalizadas: {name_mun}",
                float(data_prefeito()["pst"].replace(",", ".")),
            )
        )

    @render.ui
    def prefeito_ui():
        sort_prefeito = sorted(data_prefeito()["cand"], key=lambda x: int(x["seq"]))
        return [
            ui.HTML(
                card_candidato(
                    "https://via.placeholder.com/60",
                    cand["n"] + " - " + cand["st"],
                    float(cand["pvap"].replace(",", ".")),
                    int(cand["vap"]),
                )
            )
            for cand in sort_prefeito
        ]

    @render.ui
    def vereador_ui():
        sort_vereador = sorted(data_vereador()["cand"], key=lambda x: int(x["seq"]))
        return [
            ui.HTML(
                card_candidato(
                    "https://via.placeholder.com/60",
                    cand["n"] + " - " + cand["st"],
                    float(cand["pvap"].replace(",", ".")),
                    int(cand["vap"]),
                )
            )
            for cand in sort_vereador
        ]


app = App(app_ui, server)
