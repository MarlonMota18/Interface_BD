from textual.screen import Screen
from textual.widgets import Header, Footer, Label, Button, Input, DataTable
from textual.containers import Container, Horizontal, Vertical
from core.queries import buscar_piloto_por_sobrenome

class SearchDriverScreen(Screen):
    """
    Tela de busca de pilotos por sobrenome para a Escuderia logada (RF-09).
    """
    
    CSS = """
    #search_layout {
        background: #1e1e2e;
        padding: 1;
        layout: vertical;
    }
    
    .screen_title {
        text-align: center;
        text-style: bold;
        color: #fab387;
        background: #313244;
        padding: 1;
        margin-bottom: 1;
        border: round #cdd6f4;
    }
    
    #search_form {
        height: auto;
        layout: horizontal;
        margin-bottom: 1;
        align: left middle;
        background: #181825;
        padding: 1;
        border: round #45475a;
    }
    
    #search_form Label {
        margin-right: 1;
        margin-top: 1;
        color: #f9e2af;
        text-style: bold;
    }
    
    #search_form Input {
        width: 40;
        margin-right: 2;
        background: #313244;
        color: #cdd6f4;
        border: tall #45475a;
    }
    
    #search_form Button {
        background: #a6e3a1;
        color: #11111b;
        text-style: bold;
    }
    
    DataTable {
        height: 15;
        border: round #45475a;
        background: #181825;
        margin-bottom: 1;
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
        
        with Vertical(id="search_layout"):
            yield Label("BUSCAR PILOTO POR SOBRENOME (Histórico da Escuderia)", classes="screen_title")
            
            with Horizontal(id="search_form"):
                yield Label("Sobrenome:")
                yield Input(placeholder="Digite o sobrenome do piloto...", id="txt_lastname")
                yield Button("Buscar", id="btn_search")
                
            yield DataTable(id="tbl_results")
            
            with Horizontal(classes="bottom_actions"):
                yield Button("⬅ Voltar", id="btn_back_dashboard")
                yield Button("Sair (Logout)", id="btn_logout")
            
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#tbl_results", DataTable)
        table.add_columns("Nome Completo", "Data de Nascimento", "Nacionalidade / País")
        self.query_one("#txt_lastname").focus()

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
        elif event.button.id == "btn_search":
            self.perform_search()

    def perform_search(self):
        lastname = self.query_one("#txt_lastname", Input).value.strip()
        if not lastname:
            self.notify("Por favor, digite um sobrenome.", severity="error")
            return
            
        user = self.app.user_session
        table = self.query_one("#tbl_results", DataTable)
        table.clear()
        
        # Faz a chamada para a procedure usando o constructor_ref extraído do login
        constructor_ref = user['login'][:-2]  # Remove sufixo '_c'
        data = buscar_piloto_por_sobrenome(constructor_ref, lastname)
        if not data:
            self.notify(f"Nenhum piloto com sobrenome '{lastname}' correu por esta escuderia.", severity="warning")
            return
            
        for row in data:
            # Protege a conversão de data caso venha como objeto data ou string
            dob = row['data_nascimento']
            if dob:
                if hasattr(dob, 'strftime'):
                    dob_str = dob.strftime('%d/%m/%Y')
                else:
                    dob_str = str(dob)
            else:
                dob_str = "-"
                
            table.add_row(row['nome_completo'], dob_str, row['pais'])
            
        self.notify("Busca finalizada.", severity="information")
