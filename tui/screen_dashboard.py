from textual.screen import Screen
from textual.widgets import Header, Footer, Label, Button, DataTable, Sparkline
from textual.containers import Container, Horizontal, Vertical
from core.queries import (
    get_admin_dashboard_counts,
    get_admin_recent_races,
    get_admin_escuderias_points,
    get_admin_pilotos_points,
    get_escuderia_dashboard,
    get_piloto_anos,
    get_piloto_desempenho,
    get_escuderia_info,
    get_piloto_info
)
from tui.screen_reports import ReportsScreen
from tui.screen_search_driver import SearchDriverScreen
from tui.screen_import_drivers import ImportDriversScreen
from tui.screen_register_constructor import RegisterConstructorScreen
from tui.screen_register_driver import RegisterDriverScreen



def create_text_bar_chart(data_tuples, color="#a6e3a1"):
    from textual.containers import Vertical
    from textual.widgets import Label
    if not data_tuples:
        return Vertical(Label("Sem dados para o gráfico."))
    max_val = max((v for k, v in data_tuples), default=1)
    if max_val == 0:
        max_val = 1
    
    widgets = []
    for label, val in data_tuples:
        bar_len = int((val / max_val) * 30)
        bar_str = "█" * bar_len
        # Formata o texto garantindo alinhamento e inserindo a barra colorida
        widgets.append(Label(f"{label[:18]:<18} | [{color}]{bar_str}[/{color}] ({val})"))
    
    v = Vertical(*widgets)
    v.styles.height = "auto"
    v.styles.margin = (1, 0, 2, 0)
    return v

class DashboardScreen(Screen):
    """
    Tela principal de Dashboard. Apresenta informações sumarizadas
    com base no tipo de usuário logado (Admin, Escuderia ou Piloto).
    """
    
    # Estilização CSS premium (Aesthetics)
    CSS = """
    #dashboard_container {
        padding: 1;
        layout: vertical;
        background: #1e1e2e;
        overflow-y: auto;
    }
    
    .section_title {
        text-align: center;
        text-style: bold;
        color: #f5c2e7;
        background: #313244;
        padding: 1;
        margin-bottom: 1;
        border: round #cdd6f4;
    }
    
    #info_row {
        height: 7;
        margin-bottom: 1;
        layout: horizontal;
    }
    
    .card {
        background: #181825;
        border: round #45475a;
        padding: 1;
        margin: 0 1 0 0;
        align: center middle;
    }
    
    .card-label {
        text-align: center;
        text-style: bold;
        color: #89b4fa;
    }
    
    .card-value {
        text-align: center;
        text-style: bold;
        color: #a6e3a1;
    }
    
    DataTable {
        height: 15;
        border: round #45475a;
        background: #181825;
        margin-bottom: 1;
    }
    
    #menu_bar {
        height: 4;
        layout: horizontal;
        align: center middle;
        background: #11111b;
        border: round #45475a;
        padding: 0 1;
    }
    
    #menu_bar Button {
        margin-right: 2;
    }
    
    #btn_logout {
        background: #f38ba8;
        color: #11111b;
    }
    
    #btn_reports {
        background: #cba6f7;
        color: #11111b;
    }
    
    .action_btn {
        background: #fab387;
        color: #11111b;
    }
    
    #ranking_layout {
        height: 18;
    }
    
    .actions_bar {
        height: 4;
    }
    """

    def compose(self):
        yield Header(show_clock=True)
        
        # O container principal será preenchido dinamicamente no on_mount
        yield Container(id="dashboard_container")
        
        # Menu de Navegação no rodapé
        yield Horizontal(
            Button("Relatórios (Tela 3)", id="btn_reports"),
            Button("Sair (Logout)", id="btn_logout"),
            id="menu_bar"
        )
        
        yield Footer()

    def on_mount(self) -> None:
        """
        Monta o painel específico para o nível de acesso (RBAC) do usuário logado.
        """
        user = self.app.user_session
        container = self.query_one("#dashboard_container", Container)
        
        if not user:
            return

        # ----------------------------------------------------
        # PAINEL DO ADMINISTRADOR (ADMIN)
        # ----------------------------------------------------
        if user['tipo'] == 'Admin':
            # 1. Título e cabeçalho de boas-vindas
            container.mount(Label(f"DASHBOARD ADMINISTRADOR — Logado como: {user['login']} (Acesso Total)", classes="section_title"))
            
            # 2. Contadores do Banco de Dados
            counts = get_admin_dashboard_counts()
            if counts:
                row = Horizontal(
                    Vertical(Label("Total de Pilotos", classes="card-label"), Label(str(counts['total_pilotos']), classes="card-value"), classes="card"),
                    Vertical(Label("Total de Escuderias", classes="card-label"), Label(str(counts['total_escuderias']), classes="card-value"), classes="card"),
                    Vertical(Label("Total de Temporadas", classes="card-label"), Label(str(counts['total_temporadas']), classes="card-value"), classes="card"),
                    id="info_row"
                )
                container.mount(row)

            # 3. Tabela de Corridas da Temporada Recente
            container.mount(Label("[bold #89b4fa]Corridas da Temporada Recente[/bold #89b4fa]"))
            table_races = DataTable(id="tbl_races")
            table_races.add_columns("Corrida", "Circuito", "Data", "Horário", "Voltas")
            races = get_admin_recent_races()
            for r in races:
                table_races.add_row(
                    r['corrida'], r['circuito'], str(r['data']), 
                    str(r['horario']) if r['horario'] else "-", str(r['total_voltas']) if r['total_voltas'] else "-"
                )
            container.mount(table_races)

            # 4. Tabelas de Pontuação (Pilotos e Escuderias) em colunas paralelas
            container.mount(Label("[bold #89b4fa]Desempenho da Temporada Recente[/bold #89b4fa]"))
            
            tbl_escuderias = DataTable(id="tbl_escuderias")
            tbl_escuderias.add_columns("Escuderia", "Total Pontos")
            escuderias_data = get_admin_escuderias_points()
            spark_points = [float(e['total_pontos'] or 0) for e in escuderias_data]
            for esc in escuderias_data:
                tbl_escuderias.add_row(esc['escuderia'], str(esc['total_pontos']))
            
            tbl_pilotos = DataTable(id="tbl_pilotos")
            tbl_pilotos.add_columns("Piloto", "Total Pontos")
            for pil in get_admin_pilotos_points():
                tbl_pilotos.add_row(pil['piloto'], str(pil['total_pontos']))
            
            h_layout = Horizontal(
                Vertical(Label("Ranking de Escuderias (Gráfico)", classes="card-label"), create_text_bar_chart([(e['escuderia'], float(e['total_pontos'] or 0)) for e in escuderias_data], color="#f38ba8")),
                Vertical(Label("Ranking de Pilotos", classes="card-label"), tbl_pilotos),
                id="ranking_layout"
            )
            container.mount(h_layout)

            # 5. Ações Disponíveis para o Admin
            container.mount(Label("[bold #89b4fa]Ações Disponíveis[/bold #89b4fa]"))

            actions_bar = Horizontal(
                Button("Cadastrar Escuderia", id="btn_register_constructor", classes="action_btn"),
                Button("Cadastrar Piloto", id="btn_register_driver", classes="action_btn"),
                classes="actions_bar"
            )
            container.mount(actions_bar)

        # ----------------------------------------------------
        # PAINEL DA ESCUDERIA
        # ----------------------------------------------------
        elif user['tipo'] == 'Escuderia':
            esc_info = get_escuderia_info(user['id_original'])
            esc_name = esc_info['name'] if esc_info else user['login']
            esc_pilotos = esc_info['total_pilotos'] if esc_info else 0
            container.mount(Label(f"DASHBOARD ESCUDERIA — {esc_name} | Pilotos Associados: {esc_pilotos}", classes="section_title"))
            
            # 1. Estatísticas da Escuderia no Banco
            constructor_ref = user['login'][:-2]  # Remove sufixo '_c'
            esc_data = get_escuderia_dashboard(constructor_ref)
            if esc_data:
                row = Horizontal(
                    Vertical(Label("Vitórias (1ª Posição)", classes="card-label"), Label(str(esc_data['qtd_vitorias']), classes="card-value"), classes="card"),
                    Vertical(Label("Pilotos Diferentes", classes="card-label"), Label(str(esc_data['qtd_pilotos_diferentes']), classes="card-value"), classes="card"),
                    Vertical(Label("Anos de Atividade", classes="card-label"), Label(f"{esc_data['primeiro_ano']} - {esc_data['ultimo_ano']}" if esc_data['primeiro_ano'] else "Sem Dados", classes="card-value"), classes="card"),
                    id="info_row"
                )
                container.mount(row)

            # 2. Ações Específicas de Escuderia
            container.mount(Label("[bold #89b4fa]Ações Disponíveis[/bold #89b4fa]"))

            actions_bar = Horizontal(
                Button("Buscar Piloto por Sobrenome", id="btn_search_driver", classes="action_btn"),
                Button("Importar Pilotos por Arquivo", id="btn_import_drivers", classes="action_btn"),
                classes="actions_bar"
            )
            container.mount(actions_bar)

        # ----------------------------------------------------
        # PAINEL DO PILOTO
        # ----------------------------------------------------
        elif user['tipo'] == 'Piloto':
            pil_info = get_piloto_info(user['id_original'])
            pil_name = pil_info['nome_completo'] if pil_info else user['login']
            pil_escuderia = pil_info['escuderia_nome'] if pil_info else "Sem Escuderia"
            container.mount(Label(f"DASHBOARD PILOTO — {pil_name} | Escuderia: {pil_escuderia}", classes="section_title"))
            
            # 1. Anos de Atividade do Piloto
            pil_anos = get_piloto_anos(user['id_original'])
            if pil_anos:
                row = Horizontal(
                    Vertical(Label("Primeiro Ano na F1", classes="card-label"), Label(str(pil_anos['primeiro_ano']) if pil_anos['primeiro_ano'] else "-", classes="card-value"), classes="card"),
                    Vertical(Label("Último Ano na F1", classes="card-label"), Label(str(pil_anos['ultimo_ano']) if pil_anos['ultimo_ano'] else "-", classes="card-value"), classes="card"),
                    id="info_row"
                )
                container.mount(row)

            # 2. Agregação de Desempenho por Ano e por Circuito
            perf_data = get_piloto_desempenho(user['id_original'])
            
            por_ano = {}
            por_circuito = {}
            
            for row in perf_data:
                ano = str(row['ano'])
                circ = row['circuito_nome']
                pts = float(row['pontos'] or 0)
                vits = int(row['vitorias'] or 0)
                corrs = int(row['corridas'] or 0)
                
                if ano not in por_ano:
                    por_ano[ano] = {'pontos': 0, 'vitorias': 0, 'corridas': 0}
                por_ano[ano]['pontos'] += pts
                por_ano[ano]['vitorias'] += vits
                por_ano[ano]['corridas'] += corrs
                
                if circ not in por_circuito:
                    por_circuito[circ] = {'pontos': 0, 'vitorias': 0, 'corridas': 0}
                por_circuito[circ]['pontos'] += pts
                por_circuito[circ]['vitorias'] += vits
                por_circuito[circ]['corridas'] += corrs

            # Tabela por Ano
            container.mount(Label("[bold #89b4fa]Desempenho por Ano[/bold #89b4fa]"))
            table_ano = DataTable(id="tbl_perf_ano")
            table_ano.add_columns("Ano", "Pontos Obtidos", "Vitórias", "Total de Corridas")
            
            for ano in sorted(por_ano.keys()):
                d = por_ano[ano]
                table_ano.add_row(ano, str(d['pontos']), str(d['vitorias']), str(d['corridas']))
            container.mount(table_ano)
            
            # Gráfico de Evolução (Agregado por Ano)
            if por_ano:
                container.mount(Label("[bold #89b4fa]Evolução de Pontos por Ano (Gráfico)[/bold #89b4fa]"))
                chart_data = [(ano, por_ano[ano]['pontos']) for ano in sorted(por_ano.keys())]
                container.mount(create_text_bar_chart(chart_data, color="#a6e3a1"))

            # Tabela por Circuito
            container.mount(Label("[bold #89b4fa]Desempenho por Circuito[/bold #89b4fa]"))
            table_circ = DataTable(id="tbl_perf_circ")
            table_circ.add_columns("Circuito", "Pontos Obtidos", "Vitórias", "Total de Corridas")
            
            # Ordena circuitos por nome
            for circ in sorted(por_circuito.keys()):
                d = por_circuito[circ]
                table_circ.add_row(circ, str(d['pontos']), str(d['vitorias']), str(d['corridas']))
            container.mount(table_circ)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        Navegação entre telas e Logout.
        """
        if event.button.id == "btn_logout":
            # Realiza Logout, limpa sessão e volta para tela de Login
            from core.security import registrar_acesso
            if self.app.user_session:
                registrar_acesso(self.app.user_session['userid'], 'LOGOUT')
            self.app.user_session = None
            self.app.pop_screen()  # Volta para a tela anterior (Login)
            self.notify("Sessão encerrada com sucesso.", severity="warning")

        elif event.button.id == "btn_reports":
            self.app.push_screen(ReportsScreen())

        elif event.button.id == "btn_search_driver":
            self.app.push_screen(SearchDriverScreen())

        elif event.button.id == "btn_import_drivers":
            self.app.push_screen(ImportDriversScreen())

        elif event.button.id == "btn_register_constructor":
            self.app.push_screen(RegisterConstructorScreen())

        elif event.button.id == "btn_register_driver":
            self.app.push_screen(RegisterDriverScreen())
