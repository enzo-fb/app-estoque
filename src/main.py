import sqlite3
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.image import Image
from kivy.uix.camera import Camera
from kivy.core.image import Image as CoreImage
import io
from kivy.uix.widget import Widget
from kivy.uix.image import Image as KivyImage

CAMINHO_DATA = "estoque.db"
GRUPOS = {
    "01": "Blazer",
    "02": "Calça",
    "03": "Camiseta",
    "04": "Camisa",
    "05": "Vestido",
    "06": "Saia",
}


class MenuScreen(Screen):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        layout = BoxLayout(orientation="vertical", padding=40, spacing=30)
        logo = Image(
            source="assets/logo.png",
            size_hint_y=10,
            height=250,
        )
        label = Label(
            text="Bem-vindo ao Controle de Estoque da Abby's Brechó!",
            font_size=20,
            size_hint_y=None,
            height=60,
        )
        btn_cadastro = Button(
            text="Adicionar ao estoque",
            size_hint_y=None,
            height=45,
            font_size=16,
        )
        btn_cadastro.bind(
            on_press=lambda x: setattr(self.app.sm, "current", "cadastro")
        )
        btn_consulta = Button(
            text="Consultar estoque",
            size_hint_y=None,
            height=45,
            font_size=16,
        )
        btn_consulta.bind(
            on_press=lambda x: setattr(self.app.sm, "current", "consulta")
        )
        btn_retirada = Button(
            text="Retirar do estoque",
            size_hint_y=None,
            height=45,
            font_size=16,
        )
        btn_retirada.bind(
            on_press=lambda x: setattr(self.app.sm, "current", "retirada")
        )
        layout.add_widget(logo)
        layout.add_widget(label)
        layout.add_widget(btn_cadastro)
        layout.add_widget(btn_consulta)
        layout.add_widget(btn_retirada)
        self.add_widget(layout)


class CadastroScreen(Screen):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        layout = BoxLayout(orientation="vertical", padding=10, spacing=10)
        self.input_codigo = TextInput(
            hint_text="Código da peça (8 dígitos)", multiline=False, input_filter="int"
        )
        self.input_quantidade = TextInput(
            hint_text="Quantidade", multiline=False, input_filter="int"
        )
        self.input_cor = TextInput(hint_text="Cor", multiline=False)
        self.input_tamanho = TextInput(hint_text="Tamanho", multiline=False)
        # Tenta criar a câmera, se falhar mostra mensagem
        try:
            self.camera = Camera(
                play=False, resolution=(320, 240), size_hint_y=None, height=240
            )
            camera_widget = self.camera
            camera_ok = True
        except Exception as e:
            self.camera = None
            camera_widget = Label(
                text="Câmera não disponível", size_hint_y=None, height=240
            )
            camera_ok = False
        btn_camera = Button(
            text="Tirar Foto",
            size_hint_y=None,
            height=45,
            font_size=16,
        )
        btn_camera.bind(on_press=self.tirar_foto)
        btn_adicionar = Button(
            text="Adicionar ao estoque",
            size_hint_y=None,
            height=45,
            font_size=16,
        )
        btn_adicionar.bind(on_press=self.adicionar_peca)
        btn_menu = Button(
            text="Voltar ao Menu",
            size_hint_y=None,
            height=45,
            font_size=16,
        )
        btn_menu.bind(on_press=lambda x: setattr(self.app.sm, "current", "menu"))
        self.label_erro = Label(text="", color=(1, 0, 0, 1))
        self.foto_bytes = None  # Armazena a foto capturada
        layout.add_widget(self.input_codigo)
        layout.add_widget(self.input_quantidade)
        layout.add_widget(self.input_cor)
        layout.add_widget(self.input_tamanho)
        layout.add_widget(camera_widget)
        layout.add_widget(btn_camera)
        layout.add_widget(btn_adicionar)
        layout.add_widget(btn_menu)
        layout.add_widget(self.label_erro)
        self.add_widget(layout)

    def tirar_foto(self, instance):
        if not self.camera:
            self.label_erro.text = "Câmera não disponível."
            return
        texture = self.camera.texture
        if texture:
            data = texture.pixels
            size = texture.size
            img = CoreImage(io.BytesIO(data), ext="png")
            buf = io.BytesIO()
            img.save(buf, fmt="png")
            self.foto_bytes = buf.getvalue()
            self.label_erro.text = "Foto capturada!"
        else:
            self.label_erro.text = "Erro ao capturar foto."

    def adicionar_peca(self, instance):
        codigo = self.input_codigo.text.strip()
        quantidade = self.input_quantidade.text.strip()
        cor = self.input_cor.text.strip()
        tamanho = self.input_tamanho.text.strip()
        if len(codigo) != 8 or not codigo.isdigit():
            self.label_erro.text = "O código deve ter exatamente 8 dígitos numéricos."
            return
        grupo_codigo = codigo[:2]
        grupo_nome = GRUPOS.get(grupo_codigo, "Desconhecido")
        if not quantidade:
            self.label_erro.text = "Informe a quantidade."
            return
        if not cor:
            self.label_erro.text = "Informe a cor."
            return
        if not tamanho:
            self.label_erro.text = "Informe o tamanho."
            return
        try:
            cursor = self.app.conexao.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO roupas (id, grupo, quantidade, cor, tamanho, foto) VALUES (?, ?, ?, ?, ?, ?)",
                (codigo, grupo_nome, int(quantidade), cor, tamanho, self.foto_bytes),
            )
            self.app.conexao.commit()
            self.label_erro.text = "Peça adicionada!"
            self.input_codigo.text = ""
            self.input_quantidade.text = ""
            self.input_cor.text = ""
            self.input_tamanho.text = ""
            self.foto_bytes = None
        except Exception as e:
            self.label_erro.text = f"Erro ao adicionar: {e}"


class ConsultaScreen(Screen):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        layout = BoxLayout(orientation="vertical", padding=10, spacing=10)
        self.input_pesquisa = TextInput(
            hint_text="Pesquisar por código ou grupo...", multiline=False
        )
        self.input_pesquisa.bind(text=self.atualizar_estoque)
        btn_voltar = Button(
            text="Voltar ao Menu",
            size_hint_y=None,
            height=45,
            font_size=16,
        )
        btn_voltar.bind(on_press=lambda x: setattr(self.app.sm, "current", "menu"))
        self.resultado_layout = BoxLayout(
            orientation="vertical", spacing=10, size_hint_y=None
        )
        self.resultado_layout.bind(
            minimum_height=self.resultado_layout.setter("height")
        )
        layout.add_widget(self.input_pesquisa)
        layout.add_widget(self.resultado_layout)
        layout.add_widget(btn_voltar)
        self.add_widget(layout)
        self.atualizar_estoque()

    def atualizar_estoque(self, *args):
        pesquisa = self.input_pesquisa.text.strip().lower()
        cursor = self.app.conexao.cursor()
        cursor.execute("SELECT id, grupo, quantidade, cor, tamanho, foto FROM roupas")
        roupas = cursor.fetchall()
        self.resultado_layout.clear_widgets()
        encontrou = False
        for codigo, grupo, quantidade, cor, tamanho, foto in roupas:
            if pesquisa in codigo.lower() or pesquisa in grupo.lower():
                encontrou = True
                info = f"{codigo} ({grupo}) - Qtde: {quantidade} | Cor: {cor} | Tam: {tamanho}"
                self.resultado_layout.add_widget(
                    Label(
                        text=info,
                        size_hint_y=None,
                        height=30,
                        halign="left",
                        valign="middle",
                    )
                )
                if foto:
                    try:
                        img = CoreImage(io.BytesIO(foto), ext="png")
                        self.resultado_layout.add_widget(
                            KivyImage(texture=img.texture, size_hint_y=None, height=120)
                        )
                    except Exception:
                        self.resultado_layout.add_widget(
                            Label(
                                text="Erro ao exibir imagem",
                                size_hint_y=None,
                                height=30,
                            )
                        )
        if not encontrou:
            self.resultado_layout.add_widget(
                Label(text="Nenhum item encontrado.", size_hint_y=None, height=30)
            )


class RetiradaScreen(Screen):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        layout = BoxLayout(orientation="vertical", padding=10, spacing=10)
        self.input_codigo_retirada = TextInput(
            hint_text="Código para retirada (8 dígitos)",
            multiline=False,
            input_filter="int",
        )
        self.input_quantidade_retirada = TextInput(
            hint_text="Quantidade a retirar", multiline=False, input_filter="int"
        )
        btn_retirar = Button(
            text="Retirar do estoque",
            size_hint_y=None,
            height=45,
            font_size=16,
        )
        btn_retirar.bind(on_press=self.retirar_peca)
        btn_voltar = Button(
            text="Voltar ao Menu",
            size_hint_y=None,
            height=45,
            font_size=16,
        )
        btn_voltar.bind(on_press=lambda x: setattr(self.app.sm, "current", "menu"))
        self.label_erro_retirada = Label(text="", color=(1, 0, 0, 1))
        layout.add_widget(self.input_codigo_retirada)
        layout.add_widget(self.input_quantidade_retirada)
        layout.add_widget(btn_retirar)
        layout.add_widget(btn_voltar)
        layout.add_widget(self.label_erro_retirada)
        self.add_widget(layout)

    def retirar_peca(self, instance):
        codigo = self.input_codigo_retirada.text.strip()
        quantidade = self.input_quantidade_retirada.text.strip()
        if len(codigo) != 8 or not codigo.isdigit():
            self.label_erro_retirada.text = "Código inválido."
            return
        if not quantidade or not quantidade.isdigit():
            self.label_erro_retirada.text = "Informe a quantidade numérica."
            return
        quantidade = int(quantidade)
        cursor = self.app.conexao.cursor()
        cursor.execute("SELECT quantidade FROM roupas WHERE id = ?", (codigo,))
        resultado = cursor.fetchone()
        if not resultado:
            self.label_erro_retirada.text = "Peça não encontrada."
            return
        quantidade_atual = resultado[0]
        if quantidade > quantidade_atual:
            self.label_erro_retirada.text = "Quantidade insuficiente no estoque."
            return
        nova_quantidade = quantidade_atual - quantidade
        if nova_quantidade == 0:
            cursor.execute("DELETE FROM roupas WHERE id = ?", (codigo,))
        else:
            cursor.execute(
                "UPDATE roupas SET quantidade = ? WHERE id = ?",
                (nova_quantidade, codigo),
            )
        self.app.conexao.commit()
        self.label_erro_retirada.text = "Retirada realizada!"
        self.input_codigo_retirada.text = ""
        self.input_quantidade_retirada.text = ""


class EstoqueApp(App):
    def build(self):
        self.conexao = sqlite3.connect(CAMINHO_DATA)
        self.criar_tabela()
        self.sm = ScreenManager()
        self.sm.add_widget(MenuScreen(self, name="menu"))
        self.sm.add_widget(CadastroScreen(self, name="cadastro"))
        self.sm.add_widget(ConsultaScreen(self, name="consulta"))
        self.sm.add_widget(RetiradaScreen(self, name="retirada"))
        self.sm.current = "menu"  # Inicia no menu
        return self.sm

    def criar_tabela(self):
        cursor = self.conexao.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS roupas (
                id TEXT PRIMARY KEY,
                grupo TEXT NOT NULL,
                quantidade INTEGER NOT NULL
            )
            """
        )
        # Adiciona colunas se não existirem
        try:
            cursor.execute("ALTER TABLE roupas ADD COLUMN cor TEXT")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("ALTER TABLE roupas ADD COLUMN tamanho TEXT")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("ALTER TABLE roupas ADD COLUMN foto BLOB")
        except sqlite3.OperationalError:
            pass
        self.conexao.commit()

    def on_stop(self):
        self.conexao.close()


if __name__ == "__main__":
    EstoqueApp().run()
