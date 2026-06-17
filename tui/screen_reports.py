from textual.screen import Screen
from textual.widgets import Header, Footer, Label, Button, DataTable, Input
from textual.containers import Container, Horizontal, Vertical
from core.queries import (
    get_relatorio_1_status,
    get_relatorio_2_aeroportos,
    get_relatorio_3_circuitos,
    get_relatorio_3_corridas,
    get_relatorio_4_pilotos_vitorias,
    get_relatorio_5_status_escuderia,
    get_relatorio_6_pontos_piloto,
    get_relatorio_7_status_piloto
)

class ReportsScreen(Screen):
    """
    Tela de Relatórios (Tela 3). Exibe os relatórios permitidos ao tipo
    de usuário autenticado, com suporte a filtros e detalhamento interativo.
    """
    
    CSS = """
    #reports_layout {
        layout: horizontal;
        background: #1e1e2e;
        padding: 1;
        height: 1fr;
        overflow: hidden;
    }
    
    #sidebar {
        width: 35;
        background: #181825;
        border: round #45475a;
        padding: 1;
        margin-right: 1;
        layout: vertical;
        height: 1fr;
    }
    
    #content_area {
        width: 1fr;
        layout: vertical;
        background: #181825;
        border: round #45475a;
        padding: 1;
        height: 1fr;
        overflow: hidden;
    }
    
    .sidebar_title {
        text-align: center;
        text-style: bold;
        color: #f5c2e7;
        margin-bottom: 1;
    }
    
    .report_btn {
        width: 100%;
        margin-bottom: 1;
        background: #313244;
        color: #cdd6f4;
        text-style: bold;
    }
    
    .report_btn:hover {
        background: #45475a;
    }
    
    #btn_back_dashboard {
        background: #f38ba8;
        color: #11111b;
        margin-top: 1;
        width: 100%;
    }
    #btn_logout {
        background: #cba6f7;
        color: #11111b;
        margin-top: 1;
        width: 100%;
    }
    
    #report_title {
        text-align: center;
        text-style: bold;
        color: #cba6f7;
        background: #313244;
        padding: 1;
        margin-bottom: 1;
        border: round #cdd6f4;
    }
    
    #report_instructions {
        color: #89b4fa;
        margin-bottom: 1;
        text-style: italic;
    }
    
    #filter_panel {
        height: auto;
        layout: horizontal;
        margin-bottom: 1;
        align: left middle;
        background: #313244;
        padding: 1;
        border: round #45475a;
    }
    
    #filter_panel Label {
        margin-right: 1;
        margin-top: 1;
        color: #f9e2af;
        text-style: bold;
    }
    
    #filter_panel Input {
        width: 30;
        margin-right: 2;
        background: #1e1e2e;
        color: #cdd6f4;
        border: tall #45475a;
    }
    
    #filter_panel Button {
        background: #a6e3a1;
        color: #11111b;
        text-style: bold;
    }
    
    DataTable {
        width: 1fr;
        height: 1fr;
        border: round #45475a;
        background: #181825;
    }
    
    #btn_hierarchical_back {
        background: #fab387;
        color: #11111b;
        margin-bottom: 1;
        width: 25;
    }
    """
    
    def compose(self):
        yield Header(show_clock=True)
        
        with Horizontal(id="reports_layout"):
            # Barra lateral de controle
            with Vertical(id="sidebar"):
                yield Label("RELATÓRIOS", classes="sidebar_title")
                yield Label("Selecione um relatório:")
                
                # Botões serão exibidos dinamicamente no on_mount de acordo com o papel
                yield Vertical(id="buttons_container")
                
                yield Button("⬅ Voltar ao Dashboard", id="btn_back_dashboard")
                yield Button("Sair (Logout)", id="btn_logout")
                
            # Área principal de exibição do relatório
            with Vertical(id="content_area"):
                yield Label("Selecione um relatório na barra lateral para começar", id="report_title")
                yield Label("", id="report_instructions")
                
                # Painel de Filtros (inicialmente invisível)
                with Horizontal(id="filter_panel"):
                    yield Label("Cidade:")
                    yield Input(placeholder="Digite a cidade (ex: São Paulo)", id="txt_filter_city")
                    yield Button("Buscar", id="btn_run_filter")
                
                # Botão para retornar no relatório hierárquico
                yield Button("⬅ Voltar aos Circuitos", id="btn_hierarchical_back")
                
                # Tabela de dados
                yield DataTable(id="tbl_report")
                
        yield Footer()

    def on_mount(self) -> None:
        user = self.app.user_session
        if not user:
            return
        
        # Oculta elementos condicionais inicialmente
        self.query_one("#filter_panel").display = False
        self.query_one("#btn_hierarchical_back").display = False
        
        btn_container = self.query_one("#buttons_container")
        self.active_report = None
        self.circuit_data_level2 = []  # Guarda estado do R3 Nível 2
        
        # Popula os botões baseado no tipo de usuário (RBAC)
        if user['tipo'] == 'Admin':
            btn_container.mount(Button("Relatório 1: Status Geral", id="btn_r1", classes="report_btn"))
            btn_container.mount(Button("Relatório 2: Aeroportos", id="btn_r2", classes="report_btn"))
            btn_container.mount(Button("Relatório 3: Circuitos (Hierárquico)", id="btn_r3", classes="report_btn"))
        elif user['tipo'] == 'Escuderia':
            btn_container.mount(Button("Relatório 4: Vitórias de Pilotos", id="btn_r4", classes="report_btn"))
            btn_container.mount(Button("Relatório 5: Status da Escuderia", id="btn_r5", classes="report_btn"))
        elif user['tipo'] == 'Piloto':
            btn_container.mount(Button("Relatório 6: Pontos por Ano", id="btn_r6", classes="report_btn"))
            btn_container.mount(Button("Relatório 7: Status do Piloto", id="btn_r7", classes="report_btn"))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        table = self.query_one("#tbl_report", DataTable)
        
        # Oculta filtros por padrão a cada clique em novo relatório
        self.query_one("#filter_panel").display = False
        self.query_one("#btn_hierarchical_back").display = False
        self.query_one("#report_instructions").update("")
        
        if button_id == "btn_back_dashboard":
            self.app.pop_screen()
        elif button_id == "btn_logout":
            from core.security import registrar_acesso
            if self.app.user_session:
                registrar_acesso(self.app.user_session['userid'], 'LOGOUT')
            self.app.user_session = None
            self.app.pop_screen()
            self.app.pop_screen()
            self.notify("Sessão encerrada com sucesso.", severity="warning")
            
        elif button_id == "btn_r1":
            self.active_report = 1
            self.query_one("#report_title").update("Relatório 1: Resultados Gerais por Status")
            self.load_relatorio_1()
            
        elif button_id == "btn_r2":
            self.active_report = 2
            self.query_one("#report_title").update("Relatório 2: Aeroportos Brasileiros Próximos (<= 100 km)")
            self.query_one("#filter_panel").display = True
            table.clear(columns=True)
            self.query_one("#txt_filter_city").focus()
            
        elif button_id == "btn_run_filter" and self.active_report == 2:
            self.load_relatorio_2()
            
        elif button_id == "btn_r3":
            self.active_report = 3
            self.query_one("#report_title").update("Relatório 3: Estatísticas de Circuitos & Corridas")
            self.query_one("#report_instructions").update("[bold #a6e3a1]* DICA: Dê dois cliques ou pressione Enter em uma linha para ver as corridas do circuito.[/bold #a6e3a1]")
            self.load_relatorio_3()
            
        elif button_id == "btn_hierarchical_back":
            # Retorna do nível 3 para o nível 2 no Relatório 3
            self.active_report = 3
            self.query_one("#report_title").update("Relatório 3: Estatísticas de Circuitos & Corridas")
            self.query_one("#report_instructions").update("[bold #a6e3a1]* DICA: Dê dois cliques ou pressione Enter em uma linha para ver as corridas do circuito.[/bold #a6e3a1]")
            self.query_one("#btn_hierarchical_back").display = False
            self.load_relatorio_3()
            
        elif button_id == "btn_r4":
            self.active_report = 4
            self.query_one("#report_title").update("Relatório 4: Histórico de Vitórias dos Pilotos da Escuderia")
            self.load_relatorio_4()
            
        elif button_id == "btn_r5":
            self.active_report = 5
            self.query_one("#report_title").update("Relatório 5: Resultados por Status da Escuderia")
            self.load_relatorio_5()
            
        elif button_id == "btn_r6":
            self.active_report = 6
            self.query_one("#report_title").update("Relatório 6: Pontos Obtidos por Ano e Corrida")
            self.load_relatorio_6()
            
        elif button_id == "btn_r7":
            self.active_report = 7
            self.query_one("#report_title").update("Relatório 7: Histórico de Resultados por Status do Piloto")
            self.load_relatorio_7()

    # -------------------------------------------------------------------------
    # MÉTODOS DE CARGA DE DADOS
    # -------------------------------------------------------------------------

    def load_relatorio_1(self):
        table = self.query_one("#tbl_report", DataTable)
        table.clear(columns=True)
        table.add_columns("Nome do Status", "Quantidade de Resultados")
        
        data = get_relatorio_1_status()
        for row in data:
            table.add_row(row['status_nome'], str(row['contagem']))
        self.notify("Relatório 1 carregado.", severity="information")

    def load_relatorio_2(self):
        city = self.query_one("#txt_filter_city", Input).value.strip()
        if not city:
            self.notify("Por favor, digite o nome de uma cidade.", severity="error")
            return
            
        table = self.query_one("#tbl_report", DataTable)
        table.clear(columns=True)
        table.add_columns("Cidade Pesquisada", "Código IATA", "Aeroporto", "Cidade do Aeroporto", "Distância", "Tipo")
        
        data = get_relatorio_2_aeroportos(city)
        if not data:
            self.notify(f"Nenhum aeroporto encontrado em até 100km de '{city}'.", severity="warning")
            return
            
        for row in data:
            table.add_row(
                row['cidade_pesquisada'],
                row['codigo_iata'] if row['codigo_iata'] else "-",
                row['nome_aeroporto'],
                row['cidade_aeroporto'],
                f"{row['distancia_km']} km",
                row['tipo_aeroporto']
            )
        self.notify(f"Aeroportos próximos a {city} carregados.", severity="information")

    def load_relatorio_3(self):
        table = self.query_one("#tbl_report", DataTable)
        table.clear(columns=True)
        table.cursor_type = "row"  # Essencial para acionar RowSelected
        table.add_columns("ID Circuito", "Nome do Circuito", "Total Corridas", "Mín Voltas", "Média Voltas", "Máx Voltas")
        
        data = get_relatorio_3_circuitos()
        for row in data:
            table.add_row(
                str(row['circuit_id']),
                row['circuito'],
                str(row['total_corridas']),
                str(row['min_voltas']) if row['min_voltas'] is not None else "-",
                str(row['media_voltas']) if row['media_voltas'] is not None else "-",
                str(row['max_voltas']) if row['max_voltas'] is not None else "-"
            )
        self.notify("Lista de circuitos carregada.", severity="information")

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """
        Navegação hierárquica do Relatório 3: ao selecionar um circuito (nível 2),
        carrega suas respectivas corridas (nível 3).
        """
        if self.active_report == 3:
            table = self.query_one("#tbl_report", DataTable)
            row = table.get_row(event.row_key)
            circuit_id = int(row[0])
            circuit_name = row[1]
            self.load_relatorio_3_nivel_3(circuit_id, circuit_name)

    def load_relatorio_3_nivel_3(self, circuit_id: int, circuit_name: str):
        self.active_report = 33  # Nível 3 do relatório 3
        self.query_one("#report_title").update(f"Relatório 3: Corridas no Circuito '{circuit_name}'")
        self.query_one("#report_instructions").update("")
        self.query_one("#btn_hierarchical_back").display = True
        
        table = self.query_one("#tbl_report", DataTable)
        table.clear(columns=True)
        table.add_columns("Nome da Corrida", "Voltas Registradas", "Total Pilotos Participantes")
        
        data = get_relatorio_3_corridas(circuit_id)
        if not data:
            self.notify("Nenhuma corrida registrada neste circuito.", severity="warning")
            return
            
        for row in data:
            table.add_row(
                row['corrida'],
                str(row['voltas_registradas']) if row['voltas_registradas'] is not None else "0",
                str(row['total_pilotos'])
            )
        self.notify(f"Corridas de '{circuit_name}' carregadas.", severity="information")

    def load_relatorio_4(self):
        user = self.app.user_session
        table = self.query_one("#tbl_report", DataTable)
        table.clear(columns=True)
        table.add_columns("Piloto", "Vitórias (1ª Posição)")
        
        constructor_ref = user['login'][:-2]  # Remove sufixo '_c'
        data = get_relatorio_4_pilotos_vitorias(constructor_ref)
        for row in data:
            table.add_row(row['nome_piloto'], str(row['qtd_vitorias']))
        self.notify("Vitórias de pilotos carregadas.", severity="information")

    def load_relatorio_5(self):
        user = self.app.user_session
        table = self.query_one("#tbl_report", DataTable)
        table.clear(columns=True)
        table.add_columns("Status do Resultado", "Contagem")
        
        constructor_ref = user['login'][:-2]  # Remove sufixo '_c'
        data = get_relatorio_5_status_escuderia(constructor_ref)
        for row in data:
            table.add_row(row['status'], str(row['contagem']))
        self.notify("Status da escuderia carregado.", severity="information")

    def load_relatorio_6(self):
        user = self.app.user_session
        table = self.query_one("#tbl_report", DataTable)
        table.clear(columns=True)
        table.cursor_type = "cell"  # Habilita rolagem celular para textos muito longos
        table.add_columns("Ano", "Total de Pontos", "Corridas Pontuadas (Detalhes)")
        
        data = get_relatorio_6_pontos_piloto(user['id_original'])
        for row in data:
            table.add_row(str(row['ano']), str(row['total_pontos']), row['corridas_lista'])
        self.notify("Pontos por ano carregados.", severity="information")

    def load_relatorio_7(self):
        user = self.app.user_session
        table = self.query_one("#tbl_report", DataTable)
        table.clear(columns=True)
        table.add_columns("Status do Resultado", "Contagem")
        
        data = get_relatorio_7_status_piloto(user['id_original'])
        for row in data:
            table.add_row(row['status_nome'], str(row['contagem']))
        self.notify("Status do piloto carregado.", severity="information")
