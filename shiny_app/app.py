import copy
import json
import locale
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from functions.icons import *
from functions.utils import *
from shiny import App, reactive, render, ui

locale.setlocale(locale.LC_TIME, "pt_BR.UTF-8")

url_tse = "https://resultados.tse.jus.br"
env_tse = "oficial"
ele_tse = "619"

refresh_time = 90  # seconds

list_municipios = get_config_municipios(
    ano="2024", base_url=url_tse, cod_eleicao=ele_tse, env=env_tse
)

list_states = group_states_by_region(copy.deepcopy(list_municipios))


app_ui = ui.page_fluid(
    ui.include_css(Path(__file__).parent / "styles.css"),
    ui.row(
        ui.column(
            3,
            #   ui.h3("AMBIENTE SIMULADO DO TSE")
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
            ui.row(
                ui.column(
                    9,
                    ui.output_ui("perc_secoes_card"),
                ),
                ui.column(3, ui.output_ui("md_card")),
            ),
            ui.row(
                ui.column(
                    6,
                    ui.h3("Prefeito"),
                    ui.output_ui("prefeito_ui"),
                    class_="col-sm-6 column-prefeito",
                ),
                ui.column(
                    6,
                    ui.h3("Vereador"),
                    ui.output_ui("vereador_ui"),
                    class_="col-sm-6 column-vereador",
                ),
                style="height: 70vh;",
            ),
        ),
    ),
    ui.output_ui("footer_update"),
)


def server(input, output, session):

    # app starter
    data_prefeito = reactive.value(
        get_municipios_data(
            ano="2024",
            cod_cargo="0011",
            cod_eleicao=ele_tse,
            cod_mun_tse="85995",
            env=env_tse,
            base_url=url_tse,
            state="rs",
        )
    )
    data_vereador = reactive.value(
        get_municipios_data(
            ano="2024",
            cod_cargo="0013",
            cod_eleicao=ele_tse,
            cod_mun_tse="85995",
            env=env_tse,
            base_url=url_tse,
            state="rs",
        )
    )

    @reactive.effect
    @reactive.event(input.select_state)
    def _():
        selected_state = input.select_state()

        if selected_state != "":
            ui.update_selectize(
                "select_municipality",
                choices=get_municipality_by_state(list_municipios, selected_state),
            )

    @render.text
    def next_update_in():

        reactive.invalidate_later(1)

        minutes, seconds = calculate_time_difference(
            data_prefeito()["timestamp"], refresh_time=refresh_time
        )

        return f"Próxima atualização: {minutes}m e {seconds}s"

    @render.ui
    def side_cards_kpi():
        return [
            ui.layout_column_wrap(
                ui.value_box(
                    "Número de Eleitores",
                    f"{int(data_prefeito()['e']['te']):,}",
                    theme="bg-gradient-purple-teal",
                    full_screen=False,
                ),
                ui.value_box(
                    "Abstenções",
                    f"{data_prefeito()['e']['pa']}% ({int(data_prefeito()['e']['a']):,} eleitores)",
                    theme="bg-gradient-purple-teal",
                    full_screen=False,
                ),
            ),
            ui.layout_column_wrap(
                ui.value_box(
                    "Número de Votos Válidos",
                    f"{int(data_prefeito()['v']['vv']):,}",
                    theme="bg-gradient-purple-teal",
                    full_screen=False,
                )
            ),
            ui.layout_column_wrap(
                ui.value_box(
                    "Votos Nulos",
                    f"{data_prefeito()['v']['ptvn']}% ({int(data_prefeito()['v']['vn']):,} eleitores)",
                    theme="bg-gradient-purple-teal",
                    full_screen=False,
                ),
                ui.value_box(
                    "Votos Brancos",
                    f"{data_prefeito()['v']['pvb']}% ({int(data_prefeito()['v']['vb']):,} eleitores)",
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
                float(data_prefeito()["s"]["pst"].replace(",", ".")),
            )
        )

    @render.ui
    def md_card():
        return ui.HTML(card_md(data_prefeito().get("md", "n")))

    @render.ui
    def prefeito_ui():
        mun = input.select_municipality()
        st = input.select_state()
        region = find_region(st, list_states)
        sort_prefeito = sorted(data_prefeito()["cand"], key=lambda x: int(x["seq"]))
        return [
            ui.HTML(
                card_candidato(
                    url_candcontas=f"https://divulgacandcontas.tse.jus.br/divulga/#/candidato/{region}/{st.upper()}/2045202024/{cand['sqcand']}/2024/{mun}",
                    img_candidato=f"{url_tse}/{env_tse}/ele2024/{ele_tse}/fotos/{st}/{cand['sqcand']}.jpeg",
                    name_candidato=cand["n"] + " - " + cand["nm"],
                    progress=float(cand["pvap"].replace(",", ".")),
                    votos=int(cand["vap"]),
                    status=cand["st"],
                )
            )
            for cand in sort_prefeito
        ]

    @render.ui
    def vereador_ui():
        mun = input.select_municipality()
        st = input.select_state()
        region = find_region(st, list_states)
        sort_vereador = sorted(data_vereador()["cand"], key=lambda x: int(x["seq"]))
        return [
            ui.HTML(
                card_candidato(
                    url_candcontas=f"https://divulgacandcontas.tse.jus.br/divulga/#/candidato/{region}/{st.upper()}/2045202024/{cand['sqcand']}/2024/{mun}",
                    img_candidato=f"{url_tse}/{env_tse}/ele2024/{ele_tse}/fotos/{st}/{cand['sqcand']}.jpeg",
                    name_candidato=cand["n"] + " - " + cand["nm"],
                    progress=float(cand["pvap"].replace(",", ".")),
                    votos=int(cand["vap"]),
                    status=cand["st"],
                )
            )
            for cand in sort_vereador
        ]

    @render.ui
    def footer_update():

        reactive.invalidate_later(refresh_time)
        data_prefeito.set(
            get_municipios_data(
                ano="2024",
                cod_cargo="0011",
                cod_eleicao=ele_tse,
                cod_mun_tse=input.select_municipality(),
                env=env_tse,
                base_url=url_tse,
                state=input.select_state(),
            )
        )

        data_vereador.set(
            get_municipios_data(
                ano="2024",
                cod_cargo="0013",
                cod_eleicao=ele_tse,
                cod_mun_tse=input.select_municipality(),
                env=env_tse,
                base_url=url_tse,
                state=input.select_state(),
            )
        )

        datetime_readable = datetime.fromisoformat(
            data_prefeito()["timestamp"]
        ).strftime("%d de %B de %Y às %H:%M:%S")

        return ui.HTML(
            f"""
            <footer> Última atualização: {datetime_readable}
            """
        )


app = App(app_ui, server)
