from textual.screen import Screen
from textual.widgets import Header, Footer, Label, Button, Input, DataTable
from textual.containers import Container, Horizontal, Vertical
from core.queries import cadastrar_escuderia, get_countries

class RegisterConstructorScreen(Screen):
    """
    Tela de Cadastro de Escuderias para Administrador (RF-07).
    """
    
    CSS = """
    #register_layout {
        background: #1e1e2e;
        padding: 1;
        layout: vertical;
    }
    
    .screen_title {
        text-align: center;
        text-style: bold;
        color: #a6e3a1;
        background: #313244;
        padding: 1;
        margin-bottom: 1;
        border: round #cdd6f4;
    }
    
    #main_columns {
        layout: horizontal;
        height: 25;
        margin-bottom: 1;
    }
    
    #form_column {
        width: 45;
        background: #181825;
        border: round #45475a;
        padding: 1;
        margin-right: 1;
    }
    
    #reference_column {
        width: 1fr;
        background: #181825;
        border: round #45475a;
        padding: 1;
    }
    
    .column_title {
        text-style: bold;
        color: #f5c2e7;
        margin-bottom: 1;
        text-align: center;
    }
    
    Input {
        margin-bottom: 1;
        background: #313244;
        color: #cdd6f4;
        border: tall #45475a;
    }
    
    Input:focus {
        border: tall #a6e3a1;
    }
    
    #btn_save {
        background: #a6e3a1;
        color: #11111b;
        text-style: bold;
        width: 100%;
        margin-top: 1;
    }
    
    DataTable {
        height: 100%;
        border: round #313244;
        background: #181825;
    }
    
    .bottom_actions {
        layout: horizontal;
        height: 3;
        margin-top: 1;
    }
    #btn_back_dashboard {
        background: #f38ba8;
        color: #11111b;
        width: 25;
        margin-right: 1;
    }
    #btn_logout {
        background: #cba6f7;
        color: #11111b;
        width: 25;
    }
    """
    
    def compose(self):
        yield Header(show_clock=True)
        
        with Vertical(id="register_layout"):
            yield Label("CADASTRAR NOVA ESCUDERIA (ADMINISTRADOR)", classes="screen_title")
            
            with Horizontal(id="main_columns"):
                # Formulário de Cadastro
                with Vertical(id="form_column"):
                    yield Label("Formulário de Entrada", classes="column_title")
                    
                    yield Label("Constructor Ref (ex: mclaren):")
                    yield Input(placeholder="Código curto (minúsculas, sem espaço)", id="txt_ref")
                    
                    yield Label("Nome da Escuderia (ex: McLaren):")
                    yield Input(placeholder="Nome oficial", id="txt_name")
                    
                    yield Label("ID do País (ver tabela ao lado):")
                    yield Input(placeholder="Digite o ID numérico do país", id="txt_country_id")
                    
                    yield Label("URL Wikipédia (Opcional):")
                    yield Input(placeholder="http://...", id="txt_wiki")
                    
                    yield Button("Salvar Cadastro", id="btn_save")
                    
                # Tabela de referência de países
                with Vertical(id="reference_column"):
                    yield Label("Tabela de Referência: Países e IDs", classes="column_title")
                    yield DataTable(id="tbl_countries")
            
            with Horizontal(classes="bottom_actions"):
                yield Button("⬅ Voltar", id="btn_back_dashboard")
                yield Button("Sair (Logout)", id="btn_logout")
            
        yield Footer()

    def on_mount(self) -> None:
        # Carrega a tabela de países
        table = self.query_one("#tbl_countries", DataTable)
        table.add_columns("ID", "Nome do País")
        
        countries = get_countries()
        for c in countries:
            table.add_row(str(c['id']), c['name'])
            
        self.query_one("#txt_ref").focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_back_dashboard":
            self.app.pop_screen()
        elif event.button.id == "btn_logout":
            from core.security import registrar_acesso
            if self.app.user_session:
                registrar_acesso(self.app.user_session['userid'], 'LOGOUT')
            self.app.user_session = None
            self.app.pop_screen()
            self.app.pop_screen()
            self.notify("Sessão encerrada com sucesso.", severity="warning")
        elif event.button.id == "btn_save":
            self.save_constructor()

    def save_constructor(self):
        ref = self.query_one("#txt_ref", Input).value.strip()
        name = self.query_one("#txt_name", Input).value.strip()
        country_id_str = self.query_one("#txt_country_id", Input).value.strip()
        wiki = self.query_one("#txt_wiki", Input).value.strip()
        
        if not ref or not name or not country_id_str:
            self.notify("Por favor, preencha todos os campos obrigatórios.", severity="error")
            return
            
        try:
            country_id = int(country_id_str)
        except ValueError:
            self.notify("O ID do país deve ser um número inteiro.", severity="error")
            return
            
        # Executa no banco de dados
        result_msg = cadastrar_escuderia(ref, name, country_id, wiki)
        
        if "sucesso" in result_msg:
            self.notify(result_msg, severity="information")
            # Limpa formulário
            self.query_one("#txt_ref", Input).value = ""
            self.query_one("#txt_name", Input).value = ""
            self.query_one("#txt_country_id", Input).value = ""
            self.query_one("#txt_wiki", Input).value = ""
            self.query_one("#txt_ref").focus()
        else:
            self.notify(result_msg, severity="error")
