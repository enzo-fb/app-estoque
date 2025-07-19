from kivy.config import Config

Config.set("graphics", "width", "400")
Config.set("graphics", "height", "700")

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
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.utils import platform
import os
from kivy.uix.behaviors import ButtonBehavior


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
        layout = BoxLayout(orientation="vertical", padding=60, spacing=30)
        logo = Image(
            source="assets/logo.png",
            size_hint_y=5,
            height=150,
        )
        label = Label(
            text="Bem-vindo ao Controle de Estoque da Abby's Brechó!",
            font_size=22,
            size_hint_y=None,
            height=50,
            halign="center",
            valign="middle",
        )
        label.bind(size=lambda instance, value: setattr(instance, "text_size", value))
        btn_cadastro = Button(
            text="Adicionar ao estoque",
            size_hint_y=None,
            height=100,
            font_size=35,
        )
        btn_cadastro.bind(
            on_press=lambda x: setattr(self.app.sm, "current", "cadastro")
        )
        btn_consulta = Button(
            text="Consultar estoque",
            size_hint_y=None,
            height=100,
            font_size=35,
        )
        btn_consulta.bind(
            on_press=lambda x: setattr(self.app.sm, "current", "consulta")
        )
        btn_retirada = Button(
            text="Retirar do estoque",
            size_hint_y=None,
            height=100,
            font_size=35,
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


class AvisoBox(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.height = 36
        self.padding = [8, 4, 8, 4]
        self.orientation = "vertical"
        self.opacity = 0
        with self.canvas.before:
            Color(0.93, 0.93, 0.93, 1)  # cinza claro
            self.bg = RoundedRectangle(radius=[12], pos=self.pos, size=self.size)
        self.bind(pos=self._update_bg, size=self._update_bg)

    def _update_bg(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size


class CadastroScreen(Screen):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.camera = None
        self.camera_popup = None  # Novo popup para captura grande
        layout = BoxLayout(orientation="vertical", padding=35, spacing=10)
        self.input_codigo = TextInput(
            hint_text="Código da peça (8 dígitos)",
            multiline=False,
            input_filter="int",
            size_hint_y=None,
            height=100,
            font_size=25,
        )
        self.input_quantidade = TextInput(
            hint_text="Quantidade",
            multiline=False,
            input_filter="int",
            size_hint_y=None,
            height=100,
            font_size=25,
        )
        self.input_cor = TextInput(
            hint_text="Cor", multiline=False, size_hint_y=None, height=100, font_size=25
        )
        self.input_tamanho = TextInput(
            hint_text="Tamanho",
            multiline=False,
            size_hint_y=None,
            height=100,
            font_size=25,
        )
        self.input_preco = TextInput(
            hint_text="Preço",
            multiline=False,
            input_filter="float",
            size_hint_y=None,
            height=100,
            font_size=25,
        )
        self.foto_bytes = None
        self.foto_preview = KivyImage(size_hint_y=None, height=120)
        # Só adiciona o botão de foto se houver suporte à câmera (Android ou desktop com câmera)
        self.btn_add_foto = None
        if (
            platform == "android"
            or platform == "linux"
            or platform == "win"
            or platform == "macosx"
        ):
            self.btn_add_foto = Button(
                text="Adicionar Foto",
                size_hint_y=None,
                height=80,
                font_size=28,
            )
            self.btn_add_foto.bind(on_press=self.abrir_camera_popup)
        btn_adicionar = Button(
            text="Adicionar ao estoque",
            size_hint_y=None,
            height=80,
            font_size=28,
        )
        btn_adicionar.bind(on_press=self.adicionar_peca)
        btn_menu = Button(
            text="Voltar ao Menu",
            size_hint_y=None,
            height=80,
            font_size=28,
        )
        btn_menu.bind(on_press=lambda x: setattr(self.app.sm, "current", "menu"))
        self.label_erro = Label(
            text="",
            color=(0.2, 0.2, 0.2, 1),
            halign="center",
            valign="middle",
            font_size=16,
        )
        self.aviso_box = AvisoBox()
        self.aviso_box.add_widget(self.label_erro)
        layout.add_widget(self.input_codigo)
        layout.add_widget(self.input_quantidade)
        layout.add_widget(self.input_cor)
        layout.add_widget(self.input_tamanho)
        layout.add_widget(self.input_preco)
        # Só adiciona o botão de foto se ele ainda não foi adicionado
        if self.btn_add_foto and self.btn_add_foto.parent is None:
            layout.add_widget(self.btn_add_foto)
        layout.add_widget(btn_adicionar)
        layout.add_widget(btn_menu)
        layout.add_widget(self.aviso_box)
        self.layout = layout
        self.add_widget(layout)

    def abrir_camera_popup(self, instance):
        # ATENÇÃO: Para Android, adicione as permissões no buildozer.spec:
        # android.permissions = CAMERA,WRITE_EXTERNAL_STORAGE
        content = BoxLayout(orientation="vertical", spacing=10, padding=10)

        # Remove câmera anterior se existir
        if self.camera:
            self.camera.play = False
            self.camera = None

        camera_ok = False
        try:
            self.camera = Camera(
                index=0,
                play=True,
                resolution=(640, 480),
                size_hint=(1, 0.85),
            )
            camera_ok = True
            content.add_widget(self.camera)
        except Exception:
            camera_ok = False

        if camera_ok:
            btn_tirar = Button(
                text="Tirar Foto",
                size_hint=(1, 0.15),
                font_size=22,
                height=60,
            )
            btn_tirar.bind(on_press=self.abrir_popup_grande_camera)
            content.add_widget(btn_tirar)
        else:
            content.add_widget(
                Label(
                    text="Câmera não disponível. Verifique permissões do app.",
                    size_hint=(1, 1),
                )
            )

        btn_cancelar = Button(
            text="Cancelar", size_hint=(1, 0.12), height=50, font_size=18
        )
        btn_cancelar.bind(on_press=self.fechar_popup_camera)
        content.add_widget(btn_cancelar)
        self.popup_camera = Popup(
            title="Adicionar Foto",
            content=content,
            size_hint=(0.9, None),
            height=400,
            auto_dismiss=False,
        )
        self.popup_camera.open()

    def abrir_popup_grande_camera(self, instance):
        # Fecha o popup pequeno
        if hasattr(self, "popup_camera") and self.popup_camera:
            self.popup_camera.dismiss()
        # Cria popup grande para captura
        content = BoxLayout(orientation="vertical", spacing=10, padding=10)
        # Reutiliza a mesma câmera
        if self.camera:
            self.camera.size_hint = (1, 0.85)
            content.add_widget(self.camera)
        btn_capturar = Button(
            text="Capturar",
            size_hint=(1, 0.15),
            font_size=26,
            height=70,
        )
        btn_capturar.bind(on_press=self.tirar_foto_popup_grande)
        content.add_widget(btn_capturar)
        btn_cancelar = Button(
            text="Cancelar",
            size_hint=(1, 0.12),
            height=50,
            font_size=18,
        )
        btn_cancelar.bind(on_press=self.fechar_popup_camera_grande)
        content.add_widget(btn_cancelar)
        self.camera_popup = Popup(
            title="Capturar Foto",
            content=content,
            size_hint=(0.95, 0.85),  # Janela maior
            auto_dismiss=False,
        )
        self.camera_popup.open()

    def mostrar_aviso(self, mensagem):
        self.label_erro.text = mensagem
        self.aviso_box.opacity = 1 if mensagem else 0

    def tirar_foto_popup(self, instance):
        if not self.camera or not self.camera.texture:
            self.mostrar_aviso("Câmera não disponível ou sem imagem.")
            return
        texture = self.camera.texture
        buf = io.BytesIO()
        texture.save(buf, flipped=False, fmt="png")
        self.foto_bytes = buf.getvalue()
        # Adiciona o preview da foto somente após tirar a foto
        if self.foto_preview.parent:
            self.layout.remove_widget(self.foto_preview)
        self.foto_preview.texture = texture
        self.layout.add_widget(
            self.foto_preview, index=self.layout.children.index(self.btn_add_foto)
        )
        self.mostrar_aviso("Foto capturada!")
        self.fechar_popup_camera()

    def tirar_foto_popup_grande(self, instance):
        if not self.camera or not self.camera.texture:
            self.mostrar_aviso("Câmera não disponível ou sem imagem.")
            return
        texture = self.camera.texture
        buf = io.BytesIO()
        texture.save(buf, flipped=False, fmt="png")
        self.foto_bytes = buf.getvalue()
        # Adiciona o preview da foto somente após tirar a foto
        if self.foto_preview.parent:
            self.layout.remove_widget(self.foto_preview)
        self.foto_preview.texture = texture
        self.layout.add_widget(
            self.foto_preview, index=self.layout.children.index(self.btn_add_foto)
        )
        self.mostrar_aviso("Foto capturada!")
        self.fechar_popup_camera_grande()

    def fechar_popup_camera(self, *args):
        if hasattr(self, "popup_camera") and self.popup_camera:
            self.popup_camera.dismiss()
        # Não fecha a câmera aqui, pois pode ser usada no popup grande

    def fechar_popup_camera_grande(self, *args):
        if hasattr(self, "camera_popup") and self.camera_popup:
            self.camera_popup.dismiss()
        if self.camera:
            self.camera.play = False
            self.camera = None

    def adicionar_peca(self, instance):
        codigo = self.input_codigo.text.strip()
        quantidade = self.input_quantidade.text.strip()
        cor = self.input_cor.text.strip()
        tamanho = self.input_tamanho.text.strip()
        preco = self.input_preco.text.strip()
        status = "disponível"
        if len(codigo) != 8 or not codigo.isdigit():
            self.mostrar_aviso("O código deve ter exatamente 8 dígitos numéricos.")
            return
        grupo_codigo = codigo[:2]
        grupo_nome = GRUPOS.get(grupo_codigo, "Desconhecido")
        if not quantidade:
            self.mostrar_aviso("Informe a quantidade.")
            return
        if not cor:
            self.mostrar_aviso("Informe a cor.")
            return
        if not tamanho:
            self.mostrar_aviso("Informe o tamanho.")
            return
        if not preco:
            self.mostrar_aviso("Informe o preço.")
            return
        try:
            cursor = self.app.conexao.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO roupas (id, grupo, quantidade, cor, tamanho, preco, foto, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    codigo,
                    grupo_nome,
                    int(quantidade),
                    cor,
                    tamanho,
                    float(preco),
                    self.foto_bytes,
                    status,
                ),
            )
            self.app.conexao.commit()
            self.mostrar_aviso("Peça adicionada!")
            self.input_codigo.text = ""
            self.input_quantidade.text = ""
            self.input_cor.text = ""
            self.input_tamanho.text = ""
            self.input_preco.text = ""
            self.foto_bytes = None
        except Exception as e:
            self.mostrar_aviso(f"Erro ao adicionar: {e}")


class ClickableImage(ButtonBehavior, KivyImage):
    pass


class ConsultaScreen(Screen):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        layout = BoxLayout(orientation="vertical", padding=35, spacing=10)
        self.input_pesquisa = TextInput(
            hint_text="Pesquisar por código, grupo, cor ou tamanho...",
            multiline=False,
            size_hint_y=None,
            height=100,
            font_size=25,
        )
        self.input_pesquisa.bind(text=self.atualizar_estoque)
        btn_voltar = Button(
            text="Voltar ao Menu",
            size_hint_y=None,
            height=80,
            font_size=28,
        )
        btn_voltar.bind(on_press=lambda x: setattr(self.app.sm, "current", "menu"))
        btn_ver_tudo = Button(
            text="Ver tudo",
            size_hint_y=None,
            height=80,
            font_size=28,
        )
        btn_ver_tudo.bind(on_press=self.abrir_estoque_completo)
        # Layout para os dois botões juntos
        botoes_layout = BoxLayout(
            orientation="horizontal", size_hint_y=None, height=80, spacing=10
        )
        botoes_layout.add_widget(btn_voltar)
        botoes_layout.add_widget(btn_ver_tudo)
        self.resultado_layout = BoxLayout(
            orientation="vertical", spacing=10, size_hint_y=None
        )
        self.resultado_layout.bind(
            minimum_height=self.resultado_layout.setter("height")
        )
        scroll = ScrollView(size_hint=(1, 1))
        scroll.add_widget(self.resultado_layout)
        self.input_preco_min = TextInput(
            hint_text="Preço mínimo",
            multiline=False,
            input_filter="float",
            size_hint_y=None,
            height=60,
            font_size=20,
        )
        self.input_preco_max = TextInput(
            hint_text="Preço máximo",
            multiline=False,
            input_filter="float",
            size_hint_y=None,
            height=60,
            font_size=20,
        )
        # Adiciona eventos para atualizar ao digitar nos campos de preço
        self.input_preco_min.bind(text=self.on_preco_change)
        self.input_preco_max.bind(text=self.on_preco_change)
        preco_box = BoxLayout(
            orientation="horizontal", size_hint_y=None, height=60, spacing=10
        )
        preco_box.add_widget(self.input_preco_min)
        preco_box.add_widget(self.input_preco_max)
        layout.add_widget(self.input_pesquisa)
        layout.add_widget(preco_box)
        layout.add_widget(scroll)
        layout.add_widget(botoes_layout)
        self.add_widget(layout)
        self.atualizar_estoque()

    def abrir_estoque_completo(self, instance):
        # Atualiza a tela de estoque completo antes de trocar de tela
        self.app.sm.get_screen("estoque_completo").atualizar_estoque_completo()
        self.app.sm.current = "estoque_completo"

    def ver_tudo(self, instance):
        self.input_pesquisa.text = ""
        self.atualizar_estoque()

    def on_preco_change(self, instance, value):
        self.atualizar_estoque()

    def atualizar_estoque(self, *args):
        pesquisa = self.input_pesquisa.text.strip().lower()
        preco_min = self.input_preco_min.text.strip()
        preco_max = self.input_preco_max.text.strip()
        try:
            preco_min = float(preco_min) if preco_min else None
        except ValueError:
            preco_min = None
        try:
            preco_max = float(preco_max) if preco_max else None
        except ValueError:
            preco_max = None

        cursor = self.app.conexao.cursor()
        cursor.execute(
            "SELECT id, grupo, quantidade, cor, tamanho, preco, foto, status FROM roupas"
        )
        roupas = cursor.fetchall()
        self.resultado_layout.clear_widgets()
        encontrou = False
        for codigo, grupo, quantidade, cor, tamanho, preco, foto, status in roupas:
            # Filtros de pesquisa
            termo = pesquisa
            termo_ok = (
                (
                    termo in codigo.lower()
                    or termo in grupo.lower()
                    or termo in (cor or "").lower()
                    or termo in (tamanho or "").lower()
                    or (
                        termo
                        and termo.replace(",", ".")
                        .replace("r$", "")
                        .strip()
                        .replace(" ", "")
                        in f"{preco:.2f}".replace(".", "").replace(",", "")
                    )
                )
                if termo
                else True
            )

            preco_ok = True
            if preco_min is not None and (preco is None or preco < preco_min):
                preco_ok = False
            if preco_max is not None and (preco is None or preco > preco_max):
                preco_ok = False

            if termo_ok and preco_ok:
                encontrou = True
                preco_str = f"R$ {preco:.2f}" if preco is not None else "N/A"
                info = f"{codigo} ({grupo})\nQtde: {quantidade} | Cor: {cor.upper()} | Tam: {tamanho.upper()}\nPreço: {preco_str} | Status: {status}"

                item_layout = BoxLayout(
                    orientation="vertical", size_hint_y=None, height=180, spacing=5
                )
                # Fundo branco para o retângulo do item
                with item_layout.canvas.before:
                    Color(1, 1, 1, 1)
                    item_layout.bg_rect = RoundedRectangle(
                        pos=item_layout.pos, size=item_layout.size, radius=[12]
                    )

                def update_bg_rect(instance, value):
                    item_layout.bg_rect.pos = item_layout.pos
                    item_layout.bg_rect.size = item_layout.size

                item_layout.bind(pos=update_bg_rect, size=update_bg_rect)

                top_layout = BoxLayout(
                    orientation="horizontal",
                    size_hint_y=None,
                    height=140,  # aumenta altura do item
                )
                foto_layout = BoxLayout(size_hint_x=0.48)  # aumenta espaço da foto
                if foto:
                    try:
                        img = CoreImage(io.BytesIO(foto), ext="png")
                        img_widget = ClickableImage(
                            texture=img.texture,
                            size_hint_y=None,
                            height=130,  # aumenta altura da imagem
                        )
                        img_widget.bind(
                            on_press=lambda inst, f=foto: self.abrir_imagem_popup(f)
                        )
                        foto_layout.add_widget(img_widget)
                    except Exception:
                        foto_layout.add_widget(
                            Label(text="Erro na\nimagem", size_hint_y=None, height=130)
                        )
                else:
                    foto_layout.add_widget(
                        Label(text="Sem foto", size_hint_y=None, height=130)
                    )
                info_col = BoxLayout(orientation="vertical", size_hint_x=0.52)
                info_label = Label(
                    text=info,
                    halign="left",
                    valign="middle",
                    size_hint_x=1,
                    font_size=24,  # aumenta fonte
                    color=(0.1, 0.1, 0.1, 1),
                    bold=True,
                )
                info_label.bind(size=info_label.setter("text_size"))
                info_col.add_widget(info_label)
                top_layout.add_widget(foto_layout)
                top_layout.add_widget(info_col)
                item_layout.add_widget(top_layout)
                botoes_linha = BoxLayout(
                    orientation="horizontal", size_hint_y=None, height=60
                )
                if status.upper() == "DISPONÍVEL":
                    btn_status = Button(
                        text="Marcar como Vendida",
                        font_size=18,
                    )
                    btn_status.bind(
                        on_press=lambda inst, cod=codigo: self.marcar_status(
                            cod, "VENDIDA"
                        )
                    )
                    botoes_linha.add_widget(btn_status)
                elif status.upper() == "VENDIDA":
                    btn_status = Button(
                        text="Marcar como Disponível",
                        font_size=18,
                    )
                    btn_status.bind(
                        on_press=lambda inst, cod=codigo: self.marcar_status(
                            cod, "DISPONÍVEL"
                        )
                    )
                    botoes_linha.add_widget(btn_status)
                if status.upper() in ["DISPONÍVEL", "VENDIDA"]:
                    item_layout.add_widget(botoes_linha)
                else:
                    item_layout.height = 130
                self.resultado_layout.add_widget(item_layout)
        if not encontrou:
            self.resultado_layout.add_widget(
                Label(text="Nenhum item encontrado.", size_hint_y=None, height=30)
            )

    def abrir_imagem_popup(self, foto_bytes):
        if not foto_bytes:
            return
        try:
            img = CoreImage(io.BytesIO(foto_bytes), ext="png")
            popup_img = KivyImage(
                texture=img.texture, allow_stretch=True, keep_ratio=True
            )
            popup = Popup(
                title="Visualização da Imagem",
                content=popup_img,
                size_hint=(0.95, 0.95),
                auto_dismiss=True,
            )
            popup.open()
        except Exception:
            pass

    def marcar_status(self, codigo, novo_status):
        cursor = self.app.conexao.cursor()
        cursor.execute(
            "UPDATE roupas SET status = ? WHERE id = ?", (novo_status, codigo)
        )
        self.app.conexao.commit()
        self.atualizar_estoque()


class RetiradaScreen(Screen):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        layout = BoxLayout(orientation="vertical", padding=50, spacing=10)
        # Título da tela
        titulo = Label(
            text="Retirar do Estoque",
            font_size=30,
            size_hint_y=None,
            height=50,
            halign="center",
            valign="middle",
        )
        titulo.bind(size=lambda instance, value: setattr(instance, "text_size", value))
        layout.add_widget(titulo)

        # Texto de orientação para pesquisa
        texto_pesquisa = Label(
            text="Não sabe qual roupa retirar? Pesquise pelo código, grupo, cor ou tamanho abaixo:",
            font_size=20,
            color=(1, 1, 1, 1),  # branco
            size_hint_y=None,
            height=40,
            halign="center",
            valign="middle",
        )
        texto_pesquisa.bind(
            size=lambda instance, value: setattr(instance, "text_size", value)
        )
        layout.add_widget(texto_pesquisa)

        # Campo de pesquisa
        self.input_pesquisa = TextInput(
            hint_text="Pesquisar por código, grupo, cor ou tamanho...",
            multiline=False,
            size_hint_y=None,
            height=60,
            font_size=20,
        )
        self.input_pesquisa.bind(text=self.atualizar_lista_retirada)
        layout.add_widget(self.input_pesquisa)

        # Lista de itens para retirada
        self.lista_retirada_layout = BoxLayout(
            orientation="vertical", spacing=5, size_hint_y=None
        )
        self.lista_retirada_layout.bind(
            minimum_height=self.lista_retirada_layout.setter("height")
        )
        scroll_lista = ScrollView(size_hint=(1, 0.35))
        scroll_lista.add_widget(self.lista_retirada_layout)
        layout.add_widget(scroll_lista)

        # Adiciona um espaço vazio para empurrar os campos mais para o meio da tela
        espaco = Widget(size_hint_y=1)
        layout.add_widget(espaco)

        # Campos de entrada no meio da tela
        campos_box = BoxLayout(
            orientation="vertical", spacing=10, size_hint_y=None, height=100
        )
        self.input_codigo_retirada = TextInput(
            hint_text="Código para retirada (8 dígitos)",
            multiline=False,
            input_filter="int",
            size_hint_y=None,
            height=70,
            font_size=25,
        )
        self.input_quantidade_retirada = TextInput(
            hint_text="Quantidade a retirar",
            multiline=False,
            input_filter="int",
            size_hint_y=None,
            height=70,
            font_size=25,
        )
        campos_box.add_widget(self.input_codigo_retirada)
        campos_box.add_widget(self.input_quantidade_retirada)
        layout.add_widget(campos_box)

        # Outro espaço para empurrar os botões para o final
        espaco2 = Widget(size_hint_y=1)
        layout.add_widget(espaco2)

        # Centraliza o botão "Retirar do estoque"
        botoes_box = BoxLayout(
            orientation="horizontal", spacing=10, size_hint_y=None, height=70
        )
        botoes_box.add_widget(Widget(size_hint_x=0.2))
        btn_retirar = Button(
            text="Retirar do estoque",
            size_hint_x=0.6,
            height=70,
            font_size=24,
        )
        btn_retirar.bind(on_press=self.retirar_peca)
        botoes_box.add_widget(btn_retirar)
        botoes_box.add_widget(Widget(size_hint_x=0.2))
        layout.add_widget(botoes_box)

        # Botão "Voltar ao Menu" centralizado abaixo
        btn_voltar = Button(
            text="Voltar ao Menu",
            size_hint_x=0.7,
            size_hint_y=None,
            height=70,
            font_size=24,
            pos_hint={"center_x": 0.5},
        )
        btn_voltar.bind(on_press=lambda x: setattr(self.app.sm, "current", "menu"))
        layout.add_widget(btn_voltar)

        # Mensagem de aviso
        self.label_erro_retirada = Label(
            text="",
            color=(0.2, 0.2, 0.2, 1),
            halign="center",
            valign="middle",
            font_size=16,
            size_hint_y=None,
            height=30,
        )
        self.aviso_box_retirada = AvisoBox()
        self.aviso_box_retirada.add_widget(self.label_erro_retirada)
        layout.add_widget(self.aviso_box_retirada)
        self.add_widget(layout)
        self.atualizar_lista_retirada()

    def atualizar_lista_retirada(self, *args):
        pesquisa = self.input_pesquisa.text.strip().lower()
        cursor = self.app.conexao.cursor()
        cursor.execute("SELECT id, grupo, quantidade, cor, tamanho, preco FROM roupas")
        roupas = cursor.fetchall()
        self.lista_retirada_layout.clear_widgets()
        for codigo, grupo, quantidade, cor, tamanho, preco in roupas:
            if (
                pesquisa in codigo.lower()
                or pesquisa in grupo.lower()
                or pesquisa in (cor or "").lower()
                or pesquisa in (tamanho or "").lower()
                or not pesquisa
            ):
                preco_str = f"R$ {preco:.2f}" if preco is not None else "N/A"
                info = f"{codigo} ({grupo}) | Qtde: {quantidade} | Cor: {cor.upper()} | Tam: {tamanho.upper()} | Preço: {preco_str}"
                btn_item = Button(
                    text=info,
                    size_hint_y=None,
                    height=50,
                    font_size=18,
                    halign="left",
                    valign="middle",
                )
                btn_item.bind(
                    on_press=lambda inst, cod=codigo: self.selecionar_codigo_retirada(
                        cod
                    )
                )
                self.lista_retirada_layout.add_widget(btn_item)

    def selecionar_codigo_retirada(self, codigo):
        self.input_codigo_retirada.text = codigo

    def mostrar_aviso(self, mensagem):
        self.label_erro_retirada.text = mensagem
        self.aviso_box_retirada.opacity = 1 if mensagem else 0

    def retirar_peca(self, instance):
        codigo = self.input_codigo_retirada.text.strip()
        quantidade = self.input_quantidade_retirada.text.strip()
        if len(codigo) != 8 or not codigo.isdigit():
            self.mostrar_aviso("Código inválido.")
            self.aviso_box_retirada.opacity = 1
            return
        if not quantidade or not quantidade.isdigit():
            self.mostrar_aviso("Informe a quantidade numérica.")
            self.aviso_box_retirada.opacity = 1
            return
        quantidade = int(quantidade)
        cursor = self.app.conexao.cursor()
        cursor.execute("SELECT quantidade FROM roupas WHERE id = ?", (codigo,))
        resultado = cursor.fetchone()
        if not resultado:
            self.mostrar_aviso("Peça não encontrada.")
            self.aviso_box_retirada.opacity = 1
            return
        quantidade_atual = resultado[0]
        if quantidade > quantidade_atual:
            self.mostrar_aviso("Quantidade insuficiente no estoque.")
            self.aviso_box_retirada.opacity = 1
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
        self.mostrar_aviso("Retirada realizada!")
        self.aviso_box_retirada.opacity = 1
        self.input_codigo_retirada.text = ""
        self.input_quantidade_retirada.text = ""


class EstoqueCompletoScreen(Screen):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        layout = BoxLayout(orientation="vertical", padding=35, spacing=10)
        btn_voltar = Button(
            text="Voltar",
            size_hint_y=None,
            height=80,
            font_size=28,
        )
        btn_voltar.bind(on_press=lambda x: setattr(self.app.sm, "current", "consulta"))
        self.resultado_layout = BoxLayout(
            orientation="vertical", spacing=10, size_hint_y=None
        )
        self.resultado_layout.bind(
            minimum_height=self.resultado_layout.setter("height")
        )
        layout.add_widget(
            Label(
                text="Estoque Completo",
                size_hint_y=200,
                height=70,
                font_size=20,
                halign="center",
                valign="middle",
            )
        )
        layout.add_widget(self.resultado_layout)
        layout.add_widget(btn_voltar)
        self.add_widget(layout)
        self.atualizar_estoque_completo()

    def atualizar_estoque_completo(self):
        cursor = self.app.conexao.cursor()
        cursor.execute(
            "SELECT id, grupo, quantidade, cor, tamanho, preco, foto, status FROM roupas"
        )
        roupas = cursor.fetchall()
        self.resultado_layout.clear_widgets()
        if not roupas:
            self.resultado_layout.add_widget(
                Label(text="Nenhum item no estoque.", size_hint_y=None, height=30)
            )
            return
        for codigo, grupo, quantidade, cor, tamanho, preco, foto, status in roupas:
            preco_str = f"R$ {preco:.2f}" if preco is not None else "N/A"
            # Deixe o tamanho sempre em maiúsculo
            info = f"{codigo} ({grupo})\nQtde: {quantidade} | Cor: {cor} | Tam: {tamanho.upper()}\nPreço: {preco_str} | Status: {status}"

            linha = BoxLayout(orientation="horizontal", size_hint_y=None, height=140)
            # Fundo branco para o retângulo do item
            with linha.canvas.before:
                Color(1, 1, 1, 1)
                linha.bg_rect = RoundedRectangle(
                    pos=linha.pos, size=linha.size, radius=[12]
                )

            def update_bg_rect(instance, value):
                linha.bg_rect.pos = linha.pos
                linha.bg_rect.size = linha.size

            linha.bind(pos=update_bg_rect, size=update_bg_rect)

            foto_layout = BoxLayout(size_hint_x=0.48)
            if foto:
                try:
                    img = CoreImage(io.BytesIO(foto), ext="png")
                    img_widget = ClickableImage(
                        texture=img.texture, size_hint_y=None, height=130
                    )
                    img_widget.bind(
                        on_press=lambda inst, f=foto: self.abrir_imagem_popup(f)
                    )
                    foto_layout.add_widget(img_widget)
                except Exception:
                    foto_layout.add_widget(
                        Label(text="Erro na\nimagem", size_hint_y=None, height=130)
                    )
            else:
                foto_layout.add_widget(
                    Label(text="Sem foto", size_hint_y=None, height=130)
                )

            info_label = Label(
                text=info,
                halign="left",
                valign="middle",
                size_hint_x=0.52,
                font_size=24,  # aumenta fonte
                color=(0.1, 0.1, 0.1, 1),
                bold=True,
            )
            info_label.bind(size=info_label.setter("text_size"))

            linha.add_widget(foto_layout)
            linha.add_widget(info_label)
            self.resultado_layout.add_widget(linha)
            # Remover a linha duplicada abaixo para evitar o erro de "already has a parent"
            # linha.add_widget(info_label)
            # self.resultado_layout.add_widget(linha)

    def abrir_imagem_popup(self, foto_bytes):
        if not foto_bytes:
            return
        try:
            img = CoreImage(io.BytesIO(foto_bytes), ext="png")
            popup_img = KivyImage(
                texture=img.texture, allow_stretch=True, keep_ratio=True
            )
            popup = Popup(
                title="Visualização da Imagem",
                content=popup_img,
                size_hint=(0.95, 0.95),
                auto_dismiss=True,
            )
            popup.open()
        except Exception:
            pass


class EstoqueApp(App):
    def build(self):
        self.conexao = sqlite3.connect(CAMINHO_DATA)
        self.criar_tabela()
        self.sm = ScreenManager()
        self.sm.add_widget(MenuScreen(self, name="menu"))
        self.sm.add_widget(CadastroScreen(self, name="cadastro"))
        self.sm.add_widget(ConsultaScreen(self, name="consulta"))
        self.sm.add_widget(RetiradaScreen(self, name="retirada"))
        self.sm.add_widget(EstoqueCompletoScreen(self, name="estoque_completo"))
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
            cursor.execute("ALTER TABLE roupas ADD COLUMN preco REAL")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("ALTER TABLE roupas ADD COLUMN foto BLOB")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute(
                "ALTER TABLE roupas ADD COLUMN status TEXT DEFAULT 'DISPONÍVEL'"
            )
        except sqlite3.OperationalError:
            pass
        self.conexao.commit()

    def on_stop(self):
        self.conexao.close()


if __name__ == "__main__":
    EstoqueApp().run()
