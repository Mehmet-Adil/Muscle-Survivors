import pygame
import numpy as np

pygame.font.init()


def put_text(surface: pygame.Surface, font_path: str = None, font_size: int = 50, pos: tuple = (0, 0),
             is_underlined: bool = False, is_bold: bool = False, is_italic: bool = False,
             text: str = "", color: tuple = (0, 0, 0), text_aa: bool = True, anchor: str = "center"):
    """
    This puts text on the screen.
    """

    text_font = pygame.font.Font(font_path, font_size)
    text_font.set_underline(is_underlined)
    text_font.set_bold(is_bold)
    text_font.set_italic(is_italic)

    text_surf = text_font.render(str(text), text_aa, color)
    text_rect = text_surf.get_rect(**{anchor.lower(): pos})
    surface.blit(text_surf, text_rect)

    return text_surf, text_rect


class Button(pygame.sprite.Sprite):
    def __init__(self, image: str, pos: tuple, action=lambda: None, width: int = 200, height: int = 50,
                 color: tuple = (255, 255, 255), hover_color: tuple = (0, 0, 0), font_path: str = None, font_size=50,
                 text: str = None, text_aa: bool = True, text_color: tuple = (0, 0, 0), anchor: str = "center"):

        super().__init__()

        self.action = action

        self.pos = pygame.Vector2(pos)

        if image:
            self.image = pygame.image.load(image).convert_alpha()
        else:
            # If there is no button image make a white button with a size of 200x50
            self.image = pygame.Surface((width, height))
            self.image.fill(color)

        self.rect = self.image.get_rect(**{anchor.lower(): pos})

        self.original_image = self.image

        self.hover_color_surf = pygame.Surface(self.rect.size)
        self.hover_color_surf.fill(hover_color)
        self.hover_color_surf.set_alpha(60)

        self.color = color

        self.is_hovering = False

        self.text = text
        self.font_path = font_path
        self.font_size = font_size
        self.text_aa = text_aa
        self.text_color = text_color

        if self.text:
            put_text(self.image, font_path=self.font_path, font_size=self.font_size, text_aa=self.text_aa,
                     color=self.text_color, text=self.text, pos=(self.rect.size[0] / 2, self.rect.size[1] / 2))

    def check_button_presses(self, event, offset: pygame.math.Vector2 = pygame.math.Vector2(0, 0)):
        """
        Checks if the button is pressed.
        """
        mouse_pos = pygame.mouse.get_pos()
        left, *_ = pygame.mouse.get_pressed()

        rect = self.rect.copy()
        rect.topleft += offset

        self.is_hovering = False

        if rect.collidepoint(mouse_pos):
            if event.type == pygame.MOUSEBUTTONDOWN and left:
                self.run_action()

            else:
                self.is_hovering = True

    def update(self, event, offset: pygame.math.Vector2 = pygame.math.Vector2(0, 0)):
        """
        This updates the button image.
        """

        self.check_button_presses(event, offset)

        self.image = self.original_image.copy()

        if self.is_hovering:
            self.image.blit(self.hover_color_surf, (0, 0))

        if self.text:
            put_text(self.image, font_path=self.font_path, font_size=self.font_size, text_aa=self.text_aa,
                     color=self.text_color, text=self.text, pos=(self.rect.size[0] / 2, self.rect.size[1] / 2))

    def run_action(self):
        """
        This runs the function the button is supposed to run.
        """

        self.action()


class CircleButton(Button):
    def __init__(self, image, pos, action, radius=3, color=(255, 255, 255), hover_color=(0, 0, 0),
                 text="DEFAULT", font_size=50, has_outline=False):
        super().__init__(image, pos, action, color=color, hover_color=hover_color, text=text, font_size=font_size)

        self.radius = radius

        if image:
            self.image = pygame.image.load(image).convert_alpha()
        else:
            self.image = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
            pygame.draw.circle(self.image, self.color, (radius, radius), radius)

            if has_outline:
                pygame.draw.circle(self.image, "BLACK", (radius, radius), radius, width=2)

        self.original_image = self.image

        self.rect = self.image.get_rect(center=pos)

        self.hover_color_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.hover_color_surf, hover_color, (radius, radius), radius)
        self.hover_color_surf.set_alpha(60)

        if self.text:
            put_text(self.image, font_path=self.font_path, font_size=self.font_size, text_aa=self.text_aa,
                     color=self.text_color, text=self.text, pos=(self.rect.size[0] / 2, self.rect.size[1] / 2))

    def check_button_presses(self, event, offset: pygame.math.Vector2 = pygame.math.Vector2(0, 0)):
        """
        Checks if the button is pressed.
        """

        mouse_pos = pygame.mouse.get_pos()
        left, *_ = pygame.mouse.get_pressed()

        self.is_hovering = False

        if (self.pos + offset).distance_to(mouse_pos) <= self.radius:
            if event.type == pygame.MOUSEBUTTONDOWN and left:
                self.run_action()

            else:
                self.is_hovering = True


class Table(pygame.sprite.Sprite):
    def __init__(self, pos, title="", title_font_size=25, title_bg_color=(255, 255, 255), font_size=10,
                 text_color=(0, 0, 0), bg_color=(255, 255, 255), border_color=(0, 0, 0), has_outline=False,
                 cell_width=40, cell_height=20, row_n=2, col_n=2, data=(()), column_labels=None, anchor="center"):
        super().__init__()

        if data and (len(data) > row_n or len(data[0]) > col_n):
            raise Exception("Too Many Values For Table")

        self.data = np.full((row_n, col_n), "", dtype=np.object_)

        if column_labels:
            self.data[0, :len(column_labels)] = column_labels
            if data:
                self.data[1:len(data)+1, :len(data[0])] = data
        elif data:
            self.data[:len(data), :len(data[0])] = data

        self.n_rows = len(data) + bool(column_labels)  # +1 if column_labels is not empty
        self.column_labels = column_labels

        self.title = title
        self.title_font_size = title_font_size
        self.title_bg_color = title_bg_color

        self.col_n = col_n
        self.row_n = row_n

        self.cell_width = cell_width
        self.cell_height = cell_height

        self.has_outline = has_outline

        self.pos = pos

        self.bg_color = bg_color
        self.border_color = border_color
        self.text_color = text_color

        self.font_size = font_size

        self.table = pygame.Surface((self.cell_width * self.col_n + 2, self.cell_height * self.row_n + 2))
        if self.title:
            self.image = pygame.Surface((self.cell_width * self.col_n + 2, self.cell_height * self.row_n + title_font_size + 6))
        else:
            self.image = pygame.Surface((self.cell_width * self.col_n + 2, self.cell_height * self.row_n + 2))

        self.image.fill(self.title_bg_color)
        self.table.fill(self.bg_color)

        self.rect = self.image.get_rect(**{anchor.lower(): pos})

        self.generate_image()

    def generate_image(self):
        self.image.fill(self.title_bg_color)
        self.table.fill(self.bg_color)

        table_width = self.col_n * self.cell_width
        table_height = self.row_n * self.cell_height

        for x in range(self.cell_width, table_width, self.cell_width):
            pygame.draw.line(self.table, self.border_color, (x, 0), (x, table_height), 2)
        for y in range(self.cell_height, table_height, self.cell_height):
            pygame.draw.line(self.table, self.border_color, (0, y), (table_width, y), 2)

        for x in range(0, self.col_n):
            for y in range(0, self.row_n):
                pos = (x * self.cell_width + self.cell_width // 2, y * self.cell_height + self.cell_height // 2)

                if self.column_labels and y == 0:
                    put_text(self.table, pos=pos, text=self.data[y, x], font_size=self.font_size, is_bold=True)
                else:
                    put_text(self.table, pos=pos, text=self.data[y, x], font_size=self.font_size)

        self.image.blit(self.table, self.table.get_rect(midbottom=(self.image.get_width()//2, self.image.get_height())))

        if self.has_outline:
            if self.title:
                pygame.draw.line(self.image, self.border_color, (0, 0), (0, self.image.get_height()), 2)
                pygame.draw.line(self.image, self.border_color, (self.image.get_width()-2, 0), (self.image.get_width()-2, self.image.get_height()), 2)
                pygame.draw.line(self.image, self.border_color, (0, 0), (self.image.get_width(), 0), 2)
                pygame.draw.line(self.image, self.border_color, (0, self.title_font_size+4), (self.image.get_width(), self.title_font_size+4), 2)
                pygame.draw.line(self.image, self.border_color, (0, self.image.get_height()-2), (self.image.get_width(), self.image.get_height()-2), 2)
            else:
                pygame.draw.line(self.image, self.border_color, (0, 0), (0, table_height), 2)
                pygame.draw.line(self.image, self.border_color, (table_width, 0), (table_width, table_height+2), 2)
                pygame.draw.line(self.image, self.border_color, (0, 0), (table_width, 0), 2)
                pygame.draw.line(self.image, self.border_color, (0, table_height), (table_width+2, table_height), 2)

        put_text(self.image, pos=(self.image.get_width() // 2, self.title_font_size // 2 + 2), text=self.title, font_size=self.title_font_size)

    def update(self, *args):
        self.generate_image()

    def clear(self):
        self.data[:] = ""

        if self.column_labels:
            self.data[0, :len(self.column_labels)] = self.column_labels

    def append(self, row):
        self.data[self.n_rows] = row
        self.n_rows += 1

    def reinit_data(self, data):
        if not data:
            return

        if len(data) > self.row_n or len(data[0]) > self.col_n:
            raise Exception("Too Many Values For Table")

        self.data = np.full((self.row_n, self.col_n), "", dtype=np.object_)

        if self.column_labels:
            self.data[0, :len(self.column_labels)] = self.column_labels
            if data:
                self.data[1:len(data)+1, :len(data[0])] = data
        elif data:
            self.data[:len(data), :len(data[0])] = data

        self.n_rows = len(data) + bool(self.column_labels)  # +1 if column_labels is not empty


class InputField(pygame.sprite.Sprite):
    def __init__(self, pos, width=200, height=50, bg_color=(255, 255, 255), text_color=(0, 0, 0),
                 font_size=40, has_outline=True, text="", selected_bg_color=(0, 0, 0), anchor: str = "center"):
        super().__init__()

        self.width = width
        self.height = height

        self.has_outline = has_outline

        self.bg_color = bg_color
        self.selected_bg_color = selected_bg_color

        self.text_color = text_color
        self.font_size = font_size

        self.text = text

        self.pos = pos

        self.image = pygame.Surface((width, height))
        self.rect = self.image.get_rect(**{anchor.lower(): pos})

        self.selected_color_surf = pygame.Surface(self.rect.size)
        self.selected_color_surf.fill(self.selected_bg_color)
        self.selected_color_surf.set_alpha(40)

        self.is_selected = False

        self.prepare_image()

    def prepare_image(self):
        self.image.fill(self.bg_color)

        if self.is_selected:
            self.image.blit(self.selected_color_surf, (0, 0))

        _, text_rect = put_text(self.image, text=self.text, pos=(5, self.height // 2),
                                font_size=self.font_size, color=self.text_color, anchor="midleft")

        pygame.draw.line(self.image, self.text_color, (text_rect.right+5, 5), (text_rect.right+5, self.height-5), 2)

        if self.has_outline:
            pygame.draw.rect(self.image, "BLACK", self.image.get_rect(), 2)

    def update(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(pygame.mouse.get_pos()):
                self.is_selected = True
            else:
                self.is_selected = False

            self.prepare_image()

        if self.is_selected and event.type == pygame.KEYDOWN:
            if event.key == ord("\b"):
                self.text = self.text[:-1]
            else:
                self.text += event.unicode

            self.prepare_image()
