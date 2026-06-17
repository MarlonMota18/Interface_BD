from textual.screen import Screen
from textual.widgets import Header, Footer, Label, Button, Input, DataTable
from textual.containers import Container, Horizontal, Vertical
from core.queries import cadastrar_novo_piloto, get_countries

class RegisterDriverScreen(Screen):
    """
    Tela de Cadastro de Pilotos para Administrador (RF-08).
    """
    
    CSS = """
    #register_layout {
        background: #1e1e2e;
        padding: 1;
        layout: vertical;
        overflow-y: auto;
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
        height: auto;
        margin-bottom: 1;
    }
    
    #form_column {
        width: 45;
        background: #181825;
        border: round #45475a;
        padding: 1;
        margin-right: 1;
        overflow-y: auto;
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
            yield Label("CADASTRAR NOVO PILOTO (ADMINISTRADOR)", classes="screen_title")
            
            with Horizontal(id="main_columns"):
                # Formulário de Cadastro
                with Vertical(id="form_column"):
                    yield Label("Formulário de Entrada", classes="column_title")
                    
                    yield Label("Driver ID (ex: markinho):")
                    yield Input(placeholder="Código curto", id="txt_driver_id")
                    
                    yield Label("Given Name (ex: Mark):")
                    yield Input(placeholder="Primeiro nome do piloto", id="txt_givenName")
                    
                    yield Label("Family Name (ex: Takakura):")
                    yield Input(placeholder="Sobrenome do piloto", id="txt_familyName")
                    
                    yield Label("Nationality (ex: brazilian):")
                    yield Input(placeholder="Nacionalidade do piloto", id="txt_nationality")
                    
                    yield Label("Date of Birth (AAAA-MM-DD):")
                    yield Input(placeholder="Ex: 2005-05-25", id="txt_dob")
                    
                    yield Button("Salvar Cadastro", id="btn_save")
                    
                # Tabela de referência de países
                with Vertical(id="reference_column"):
                    yield Label("Tabela de Referência: Nacionalidades", classes="column_title")
                    yield DataTable(id="tbl_countries")
            
            with Horizontal(classes="bottom_actions"):
                yield Button("⬅ Voltar", id="btn_back_dashboard")
                yield Button("Sair (Logout)", id="btn_logout")
            
        yield Footer()

    def on_mount(self) -> None:
        # Carrega a tabela de países
        table = self.query_one("#tbl_countries", DataTable)
        table.add_columns("ID", "Nacionalidade")
        
        countries = get_countries()
        for c in countries:
            table.add_row(str(c['id']), c['nationality'] if c['nationality'] else "N/A")
            
        self.query_one("#txt_driver_id").focus()

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
            self.save_driver()

    def save_driver(self):
        driver_id = self.query_one("#txt_driver_id", Input).value.strip()
        givenName = self.query_one("#txt_givenName", Input).value.strip()
        familyName = self.query_one("#txt_familyName", Input).value.strip()
        nationality = self.query_one("#txt_nationality", Input).value.strip()
        dob = self.query_one("#txt_dob", Input).value.strip()
        
        if not driver_id or not givenName or not familyName or not nationality or not dob:
            self.notify("Por favor, preencha todos os campos obrigatórios.", severity="error")
            return
            
        try:
            from datetime import datetime
            datetime.strptime(dob, "%Y-%m-%d")
        except ValueError:
            self.notify("A Data de Nascimento deve estar no formato exato AAAA-MM-DD.", severity="error")
            return
            
        # Executa no banco de dados chamando a procedure que valida duplicados
        result_msg = cadastrar_novo_piloto(driver_id, givenName, familyName, nationality, dob)
        
        if "com sucesso" in result_msg:
            self.notify(result_msg, severity="information")
            # Limpa formulário
            self.query_one("#txt_driver_id", Input).value = ""
            self.query_one("#txt_givenName", Input).value = ""
            self.query_one("#txt_familyName", Input).value = ""
            self.query_one("#txt_nationality", Input).value = ""
            self.query_one("#txt_dob", Input).value = ""
            self.query_one("#txt_driver_id").focus()
        else:
            self.notify(result_msg, severity="error")
