from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import ObjectProperty, NumericProperty, StringProperty
from kivy.storage.jsonstore import JsonStore
from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget

from kivymd.app import MDApp
from kivymd.uix.button import MDIconButton, MDButton, MDButtonText
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.dialog import (
    MDDialog,
    MDDialogHeadlineText,
    MDDialogSupportingText,
    MDDialogButtonContainer,
)
from kivymd.uix.textfield import MDTextField
from kivymd.uix.boxlayout import MDBoxLayout

Window.size = (360, 640)


class MenuScreen(Screen):
    userLevel = NumericProperty(0)
    current_xp = NumericProperty(0)
    max_xp = NumericProperty(100)
    selected_pet = StringProperty("pet1")
    pet_source = StringProperty("Pet/pet1/evolution1.png")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.task_texts = []
        self.loading = False
        self.add_task_dialog = None

    def on_kv_post(self, base_widget):
        app = MDApp.get_running_app()
        self.loading = True

        if app.store.exists("level"):
            self.userLevel = app.store.get("level")["value"]

        if app.store.exists("current_xp"):
            self.current_xp = app.store.get("current_xp")["value"]

        if app.store.exists("selected_pet"):
            self.selected_pet = app.store.get("selected_pet")["value"]

        if app.store.exists("tasks"):
            self.task_texts = app.store.get("tasks")["items"]
            for task_data in self.task_texts:
                self._create_task_card(
                    task_data['text'],
                    task_data['done'],
                    save=False,
                    difficulty=task_data.get('difficulty', 1)
                )

        self.loading = False
        self.update_pet_image()

    def update_pet_image(self):
        level = self.userLevel
        evolution = 1

        if level >= 5:
            evolution = 4
        elif level >= 3:
            evolution = 3
        elif level >= 1:
            evolution = 2

        self.pet_source = f'Pet/{self.selected_pet}/evolution{evolution}.png'

    def show_add_task_dialog(self):
        if self.add_task_dialog:
            self.add_task_dialog.open()
            return

        self.new_task_text = ""
        self.selected_difficulty = 1

        def set_difficulty(level):
            self.selected_difficulty = level
            for i in range(3):
                buttons[i].icon = "star" if i < level else "star-outline"

        task_input = MDTextField(
            halign='left',
            hint_text="Enter task name",
            mode="outlined",
            size_hint_x=1.5,
            pos_hint={'x': -1.1, 'y': 1.3},
        )

        buttons = [
            MDIconButton(
                icon="star-outline",
                theme_icon_color="Custom",
                icon_color=(1, 0.7, 0, 1),
                on_release=lambda btn, i=i: set_difficulty(i + 1),
            ) for i in range(3)
        ]

        star_row = MDBoxLayout(
            orientation="horizontal",
            spacing="12dp",
            size_hint=(1, None),
            pos_hint={'y': 3},
            height="50dp",
        )
        for btn in buttons:
            star_row.add_widget(btn)

        content = MDBoxLayout(
            orientation="vertical",
            spacing="16dp",
            padding=["12dp", "12dp", "12dp", "0dp"],
            adaptive_height=True,
        )
        content.add_widget(task_input)
        content.add_widget(star_row)

        self.add_task_dialog = MDDialog(
            content,
            MDDialogButtonContainer(
                MDButton(
                    MDButtonText(text="Cancel"),
                    style="text",
                    on_release=lambda x: self.add_task_dialog.dismiss(),
                ),
                MDButton(
                    MDButtonText(text="Add"),
                    style="text",
                    on_release=lambda x: (
                        self._create_task_card(
                            task_input.text.strip(),
                            False,
                            True,
                            self.selected_difficulty
                        ),
                        self.add_task_dialog.dismiss()
                    ),
                ),
                spacing="8dp",
            ),
        )

        self.add_task_dialog.open()

    def _create_task_card(self, task_text, done=False, save=True, difficulty=1):
        xp_reward = difficulty * 10
        task_list = self.ids.task_list

        task_card = MDCard(
            orientation="horizontal",
            size_hint_y=None,
            height="72dp",
            padding=("8dp", "8dp"),
            spacing="8dp",
            radius=[12],
            elevation=4,
        )

        checkbox = MDCheckbox(
            size_hint=(None, None),
            size=("32dp", "32dp"),
            pos_hint={'center_y': 0.5},
            active=done,
        )

        task_label = MDLabel(
            text=f"[s]{task_text}[/s]" if done else task_text,
            markup=done,
            font_style="Body",
            theme_text_color="Custom",
            halign="left",
            valign="middle",
            size_hint_y=None,
            height="24dp"
        )

        star_row = MDBoxLayout(
            orientation='horizontal',
            spacing="2dp",
            size_hint_y=None,
            height="18dp"
        )
        for i in range(3):
            icon_name = "star" if i < difficulty else "star-outline"
            star_icon = MDIconButton(
                icon=icon_name,
                disabled=True,
                size_hint=(None, None),
                size=("16dp", "16dp"),
                pos_hint={'center_y': 0.5}
            )
            star_row.add_widget(star_icon)

        text_and_stars = MDBoxLayout(
            orientation="vertical",
            spacing="4dp",
            size_hint_x=0.8,
        )
        text_and_stars.add_widget(task_label)
        text_and_stars.add_widget(star_row)

        delete_btn = MDIconButton(
            icon="trash-can",
            pos_hint={'center_y': 0.5},
            theme_text_color="Custom",
            on_release=lambda x: self._delete_task(task_card, task_text)
        )

        def toggle_strikethrough(instance, value):
            xp = next((t['xp'] for t in self.task_texts if t['text'] == task_text), xp_reward)
            if value:
                task_label.text = f"[s]{task_text}[/s]"
                task_label.markup = True
                self.add_xp(xp)
            else:
                task_label.text = task_text
                task_label.markup = False
                self.current_xp = max(0, self.current_xp - xp)
            if not self.loading:
                self._update_task_status(task_text, value)
                self.save_data()

        checkbox.bind(active=toggle_strikethrough)

        task_card.add_widget(checkbox)
        task_card.add_widget(text_and_stars)
        task_card.add_widget(delete_btn)
        task_list.add_widget(task_card)

        if save:
            self.task_texts.append({
                "text": task_text,
                "done": done,
                "difficulty": difficulty,
                "xp": xp_reward
            })
            if not self.loading:
                self.save_data()

    def add_xp(self, xp_amount):
        self.current_xp += xp_amount
        while self.current_xp >= self.max_xp:
            self.current_xp -= self.max_xp
            self.userLevel += 1
            self.update_pet_image()  # Add this line here to update pet evolution
        self.save_data()

    def _update_task_status(self, task_text, done):
        for task in self.task_texts:
            if task['text'] == task_text:
                task['done'] = done
                break

    def _delete_task(self, task_card, task_text):
        self.ids.task_list.remove_widget(task_card)
        self.task_texts = [t for t in self.task_texts if t['text'] != task_text]
        self.save_data()

    def save_data(self):
        app = MDApp.get_running_app()
        app.store.put("level", value=self.userLevel)
        app.store.put("current_xp", value=self.current_xp)
        app.store.put("selected_pet", value=self.selected_pet)
        app.store.put("tasks", items=self.task_texts)

    def reset_user_data(self):
        self.userLevel = 0
        self.current_xp = 0
        self.selected_pet = "pet1"
        self.task_texts = []
        self.ids.task_list.clear_widgets()
        app = MDApp.get_running_app()
        app.store.put("level", value=0)
        app.store.put("current_xp", value=0)
        app.store.put("selected_pet", value="pet1")
        app.store.put("tasks", items=[])
        self.update_pet_image()


class ProfileScreen(Screen):
    main_layout = ObjectProperty()
    dialog = None
    theme_dialog = None

    def show_theme_dialog(self):
        if not self.theme_dialog:
            self.theme_dialog = MDDialog(
                MDDialogHeadlineText(
                    text="Select Theme",
                    halign="left",
                ),
                MDDialogButtonContainer(
                    MDButton(
                        MDButtonText(text="Light"),
                        style="text",
                        pos_hint={'center_x': 0.2},
                        on_release=lambda x: self.change_theme("Light", "Orange"),
                    ),
                    MDButton(
                        MDButtonText(text="Dark"),
                        style="text",
                        pos_hint={'center_x': 0.5},
                        on_release=lambda x: self.change_theme("Dark", "Orange"),
                    ),
                    MDButton(
                        MDButtonText(text="Colorblind"),
                        style="text",
                        pos_hint={'center_x': 0.5},
                        on_release=lambda x: self.change_theme("Light", "Red"),
                    ),
                    spacing="2dp",
                ),
            )
        self.theme_dialog.open()

    def show_pet_selection_dialog(self):
        if not hasattr(self, 'pet_dialog'):
            self.pet_dialog = MDDialog(
                MDDialogHeadlineText(
                    text="Select Pet",
                    halign="left",
                ),
                MDDialogButtonContainer(
                    MDButton(
                        MDButtonText(text="Blooey"),
                        style="text",
                        pos_hint={'center_x': 0.5},
                        on_release=lambda x: self.change_pet("pet1"),
                    ),
                    MDButton(
                        MDButtonText(text="Pinku"),
                        style="text",
                        on_release=lambda x: self.change_pet("pet2"),
                    ),
                    spacing="8dp",
                ),
            )
        self.pet_dialog.open()

    def change_theme(self, theme_style, color_palette):
        app = MDApp.get_running_app()
        app.switch_theme_style(theme_style, color_palette)

        if color_palette == "Red":  # Treat as colorblind mode
            for widget in self.walk():
                if isinstance(widget, (MDCard, MDButton)):
                    widget.line_color = [0, 0, 0, 1]
                    widget.line_width = 2

        self.theme_dialog.dismiss()

    def change_pet(self, pet_name):
        menu_screen = self.manager.get_screen('menu')
        menu_screen.selected_pet = pet_name
        menu_screen.update_pet_image()
        menu_screen.save_data()
        self.pet_dialog.dismiss()

    def show_reset_confirmation(self):
        if not self.dialog:
            self.dialog = MDDialog(
                MDDialogHeadlineText(
                    text="Reset Account?",
                    halign="left",
                ),
                MDDialogSupportingText(
                    text="Are you sure you want to reset your account? This action cannot be undone.",
                    halign="left",
                ),
                MDDialogButtonContainer(
                    Widget(),
                    MDButton(
                        MDButtonText(text="Cancel"),
                        style="text",
                        on_release=lambda x: self.dialog.dismiss(),
                    ),
                    MDButton(
                        MDButtonText(text="Reset"),
                        style="text",
                        on_release=self._confirm_reset,
                    ),
                    spacing="8dp",
                ),
            )
        self.dialog.open()

    def _confirm_reset(self, instance):
        self.dialog.dismiss()
        self.reset_data()

    def reset_data(self):
        menu_screen = self.manager.get_screen('menu')
        menu_screen.reset_user_data()


class DemoApp(MDApp):
    def build(self):
        self.store = JsonStore("user_data.json")
        self.theme_cls.theme_style_switch_animation = True
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Orange"
        self.screen = Builder.load_file("main.kv")
        return self.screen

    def switch_theme_style(self, theme_style, color_palette):
        self.theme_cls.theme_style = theme_style
        self.theme_cls.primary_palette = color_palette
        self.update_background_colors()

    def get_background_color(self):
        if self.theme_cls.theme_style == "Dark":
            return self.theme_cls.backgroundColor
        else:
            return [0.98, 0.98, 0.98, 1]

    def update_background_colors(self):
        self.screen.get_screen('menu').main_layout.md_bg_color = self.get_background_color()
        self.screen.get_screen('profile').main_layout.md_bg_color = self.get_background_color()


if __name__ == "__main__":
    DemoApp().run()
