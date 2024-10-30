import pygame
from pygame import Vector2
from math import floor, ceil
from game_mode1 import GameMode1
from sys import exit as sys_exit
import settings
import UI
import database
from os.path import join as path_join

pygame.init()


class Grid:
    def __init__(self, color, tile_size, outer_size=1):
        self.color = color
        self.tile_width, self.tile_height = tile_size

        self.grid = {"VERTICALS": [], "HORIZONTALS": []}

        self.grid_width, self.grid_height = self.calculate_grid_size()

        self.line_width = self.grid_width * self.tile_width
        self.line_height = self.grid_height * self.tile_height

        self.min_x = -self.tile_width
        self.min_y = floor(-self.line_height * outer_size)

        self.max_x = ceil(self.line_width * (1 + outer_size))
        self.max_y = ceil(self.line_height * (1 + outer_size))

        self.calculate_grid()

        self.shift = pygame.Vector2(0, 0)

    def get_number_of_lines(self):
        return len(self.grid["VERTICALS"]) + len(self.grid["HORIZONTALS"])

    def calculate_grid_size(self):
        return ceil(settings.WINDOW_SIZE[0] / self.tile_width), ceil(settings.WINDOW_SIZE[1] / self.tile_height)

    def calculate_grid(self):
        for column in range(self.min_x, self.max_x + self.tile_width, self.tile_width):
            for i in range(self.min_y, self.max_y, self.line_height):
                self.grid["VERTICALS"].append(((column, i), (column, i + self.line_height)))

        for row in range(self.min_y, self.max_y + self.tile_height, self.tile_height):
            for i in range(self.min_x, self.max_x, self.line_width):
                self.grid["HORIZONTALS"].append(((i, row), (i + self.line_width, row)))

    def update(self, shift):
        self.shift = shift

        shift_x_constrained = self.tile_width * (shift.x // self.tile_width)
        shift_y_constrained = self.tile_height * (shift.y // self.tile_height)

        for start, end in self.grid["VERTICALS"].copy():
            has_updated_pos = False
            new_start = start
            new_end = end

            if start[0] + shift_x_constrained < self.min_x:  # Going Right
                has_updated_pos = True
                new_start = (self.max_x - shift_x_constrained, new_start[1])
                new_end = (self.max_x - shift_x_constrained, new_end[1])

            if start[1] + shift_y_constrained < self.min_y:  # Going Down
                has_updated_pos = True
                new_start = (new_start[0], self.max_y - shift_y_constrained - self.line_height)
                new_end = (new_end[0], self.max_y - shift_y_constrained)

            elif end[1] + shift_y_constrained > self.max_y:  # Going Up
                has_updated_pos = True
                new_start = (new_start[0], self.min_y - shift_y_constrained)
                new_end = (new_end[0], self.min_y - shift_y_constrained + self.line_height)

            if has_updated_pos:
                self.grid["VERTICALS"].remove((start, end))
                self.grid["VERTICALS"].append((new_start, new_end))

        for start, end in self.grid["HORIZONTALS"].copy():
            has_updated_pos = False
            new_start = start
            new_end = end

            if start[1] + shift_y_constrained < self.min_y:  # Going Down
                has_updated_pos = True
                new_start = (start[0], self.max_y - shift_y_constrained)
                new_end = (end[0], self.max_y - shift_y_constrained)

            elif start[1] + shift_y_constrained > self.max_y:  # Going Up
                has_updated_pos = True
                new_start = (start[0], self.min_y - shift_y_constrained)
                new_end = (end[0], self.min_y - shift_y_constrained)

            if end[0] + shift_x_constrained <= self.min_x:  # Going Right
                has_updated_pos = True
                new_start = (self.max_x - shift_x_constrained - self.line_width, start[1])
                new_end = (self.max_x - shift_x_constrained, end[1])

            if has_updated_pos:
                self.grid["HORIZONTALS"].remove((start, end))
                self.grid["HORIZONTALS"].append((new_start, new_end))

    def draw(self, screen):
        for start, end in (*self.grid["HORIZONTALS"], *self.grid["VERTICALS"]):
            pygame.draw.line(screen, self.color, start + self.shift, end + self.shift)

    def convert_pos_to_coordinates(self, pos):  # (1, 1) -> (Tile Width, Tile Height)
        return pos[0] * self.tile_width + self.shift.x, pos[1] * self.tile_height + self.shift.y

    def convert_local_coordinates_to_pos(self, coordinates):  # (Tile Width, Tile Height) -> (1, 1) | Local Coordinates
        return int((coordinates[0] - self.shift.x) // self.tile_width), int(
            (coordinates[1] - self.shift.y) // self.tile_height)

    def convert_world_coordinates_to_pos(self, coordinates):  # (Tile Width, Tile Height) -> (1, 1) | World Coordinates
        return int(coordinates[0] // self.tile_width), int(coordinates[1] // self.tile_height)

    def reset(self):
        self.shift.x, self.shift.y = 0, 0
        self.calculate_grid()


class Game:
    SCREEN_SLIDING_SPEED = 5

    def __init__(self):
        settings.SCREEN = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        settings.WINDOW_SIZE = settings.SCREEN.get_size()
        pygame.display.set_caption(settings.WINDOW_CAPTION)

        if settings.WINDOW_LOGO.get_size() != (0, 0):
            pygame.display.set_icon(settings.WINDOW_LOGO)

        self.clock = pygame.time.Clock()
        self.shift = Vector2(0, 0)

        n_vertical_tiles = 10
        self.grid = Grid("GRAY", (settings.WINDOW_SIZE[1] // n_vertical_tiles, settings.WINDOW_SIZE[1] // n_vertical_tiles))

        self.game_mode1 = GameMode1(self.grid, "EASY")
        settings.game_state = "SIGN IN"

        self.main_menu_ui = pygame.sprite.Group()
        self.main_menu_ui.add(UI.Button(None, (settings.WINDOW_SIZE[0] // 2, settings.WINDOW_SIZE[1] // 2 - 150),
                                        lambda: self.main_menu_choose_difficulty("EASY"), color="#394a50",
                                        text_color=(255, 255, 255), text="EASY", width=300, height=70))
        self.main_menu_ui.add(UI.Button(None, (settings.WINDOW_SIZE[0] // 2, settings.WINDOW_SIZE[1] // 2 - 20),
                                        lambda: self.main_menu_choose_difficulty("NORMAL"), color="#394a50",
                                        text_color=(255, 255, 255), text="NORMAL", width=300, height=70))
        self.main_menu_ui.add(UI.Button(None, (settings.WINDOW_SIZE[0] // 2, settings.WINDOW_SIZE[1] // 2 + 110),
                                        lambda: self.main_menu_choose_difficulty("HARD"), color="#394a50",
                                        text_color=(255, 255, 255), text="HARD", width=300, height=70))

        self.leaderboard_easy = UI.Table((settings.WINDOW_SIZE[0] // 5, settings.WINDOW_SIZE[1] // 2 - 95), title="EASY Mode Leaderboard", title_bg_color="#a8ca58",
                                         bg_color="#d0da91", font_size=25, has_outline=True, cell_width=125,
                                         cell_height=40, row_n=4, column_labels=["Player Name", "Score"], data=database.get_high_scores("EASY", 3))
        self.leaderboard_normal = UI.Table((settings.WINDOW_SIZE[0] // 1.25, settings.WINDOW_SIZE[1] // 2 - 95), title="NORMAL Mode Leaderboard", title_bg_color="#73bed3",
                                           bg_color="#a4dddb", font_size=25, has_outline=True, cell_width=125,
                                           cell_height=40, row_n=4, column_labels=["Player Name", "Score"], data=database.get_high_scores("NORMAL", 3))
        self.leaderboard_hard = UI.Table((settings.WINDOW_SIZE[0] // 1.25, settings.WINDOW_SIZE[1] // 2 + 130), title="HARD Mode Leaderboard", title_bg_color="#cf573c",
                                         bg_color="#da863e", font_size=25, has_outline=True, cell_width=125,
                                         cell_height=40, row_n=4, column_labels=["Player Name", "Score"], data=database.get_high_scores("HARD", 3))

        self.update_leaderboard()

        self.main_menu_ui.add(self.leaderboard_easy)
        self.main_menu_ui.add(self.leaderboard_normal)
        self.main_menu_ui.add(self.leaderboard_hard)

        self.main_menu_ui.add(UI.CircleButton(None, (settings.WINDOW_SIZE[0] // 5, settings.WINDOW_SIZE[1] // 2 + 130), lambda: self.log_out(), 60,
                                              text="LOG OUT", font_size=30, color=(220, 60, 60), has_outline=True))

        self.main_menu_ui.add(UI.CircleButton(None, (settings.WINDOW_SIZE[0] - 80, 80), lambda: self.quit_game(), 45,
                                              text="LEAVE", font_size=30, color="#d7b594", has_outline=True))

        self.sign_in_ui = pygame.sprite.Group()

        self.sign_in_ui.add(UI.CircleButton(None, (settings.WINDOW_SIZE[0] - 80, 80), lambda: self.quit_game(), 45,
                                            text="LEAVE", font_size=30, color="#d7b594", has_outline=True))

        self.player_name_input_field = UI.InputField((settings.WINDOW_SIZE[0] // 2, settings.WINDOW_SIZE[1] // 2 - 60), width=325, has_outline=True)
        self.player_password_input_field = UI.InputField((settings.WINDOW_SIZE[0] // 2, settings.WINDOW_SIZE[1] // 2 + 60), width=325, has_outline=True)

        self.sign_in_ui.add(self.player_name_input_field)
        self.sign_in_ui.add(self.player_password_input_field)

        self.sign_in_ui.add(UI.Button(None, (settings.WINDOW_SIZE[0] / 2, settings.WINDOW_SIZE[1] // 2 + 140),
                                      lambda: self.sign_in(), width=260, color="#819796", text_color="#090a14", text="SIGN IN/UP"))

        self.sign_in_error = ""

        self.main_menu_music = pygame.mixer.Sound(path_join("Music", "Fake Spring.wav"))
        self.main_menu_music.set_volume(0.85)
        self.is_main_menu_music_playing = False

    def update_leaderboard(self):
        self.leaderboard_easy.reinit_data(database.get_high_scores("EASY", 3))
        self.leaderboard_normal.reinit_data(database.get_high_scores("NORMAL", 3))
        self.leaderboard_hard.reinit_data(database.get_high_scores("HARD", 3))

    def log_out(self):
        settings.user = None
        settings.user_password = None

        self.player_name_input_field.text = ""
        self.player_name_input_field.prepare_image()
        self.player_password_input_field.text = ""
        self.player_password_input_field.prepare_image()

        settings.game_state = "SIGN IN"

    def sign_in_draw(self):
        settings.SCREEN.fill("#ebede9")
        UI.put_text(settings.SCREEN, font_size=75, is_underlined=True, color="#090a14",
                    pos=(settings.WINDOW_SIZE[0] // 2, settings.WINDOW_SIZE[1] // 2 - 350), anchor="MIDTOP", text="MUSCLE SURVIVORS")

        UI.put_text(settings.SCREEN, color="#090a14", font_size=35, pos=(settings.WINDOW_SIZE[0] // 2, settings.WINDOW_SIZE[1] // 2 - 250), anchor="MIDTOP", text="WELCOME! Please SIGN IN/UP to play the game!")
        UI.put_text(settings.SCREEN, color="#090a14", font_size=30, pos=(self.player_name_input_field.rect.left, self.player_name_input_field.rect.top-25), anchor="MIDLEFT", text="Player Name:")
        UI.put_text(settings.SCREEN, color="#090a14", font_size=30, pos=(self.player_password_input_field.rect.left, self.player_password_input_field.rect.top-25), anchor="MIDLEFT", text="Player Password:")

        self.sign_in_ui.draw(settings.SCREEN)

        UI.put_text(settings.SCREEN, font_size=30, pos=(settings.WINDOW_SIZE[0] // 2, settings.WINDOW_SIZE[1] // 2 + 250),
                    anchor="MIDTOP", text=self.sign_in_error, color="RED")

    def sign_in(self):
        name = self.player_name_input_field.text.strip()
        password = self.player_password_input_field.text.strip()

        if not name or not password:
            self.sign_in_error = "Please fill in ALL of the fields!"

            return

        result = database.insert_player(self.player_name_input_field.text, self.player_password_input_field.text)

        if result:
            settings.user = name
            settings.user_password = password

            self.sign_in_error = ""

            settings.game_state = "MAIN MENU"
        else:
            self.sign_in_error = "Account already EXISTS! WRONG PASSWORD!"

    def main_menu_choose_difficulty(self, difficulty):
        self.game_mode1.set_difficulty(difficulty)
        settings.game_state = "INTRO"

    def main_menu_draw(self):
        settings.SCREEN.fill("#ebede9")
        UI.put_text(settings.SCREEN, font_size=75, is_underlined=True,
                    pos=(settings.WINDOW_SIZE[0] / 2, settings.WINDOW_SIZE[1] // 2 - 350), anchor="MIDTOP", text="MUSCLE SURVIVORS")

        UI.put_text(settings.SCREEN, font_size=30, pos=(30, 30), is_italic=True, anchor="TOPLEFT", text=f"Hello, {settings.user}!")
        self.main_menu_ui.draw(settings.SCREEN)

    def middle_game_draw(self):
        settings.SCREEN.fill("#ebede9")

        self.grid.update(self.shift)
        self.grid.draw(settings.SCREEN)

        self.game_mode1.draw(settings.SCREEN)
        self.game_mode1.update()

    def main_loop(self):
        while True:
            self.event_loop()

            if settings.game_state == "SIGN IN":
                self.is_main_menu_music_playing = False

                self.sign_in_draw()

            elif settings.game_state == "MAIN MENU":
                if not self.is_main_menu_music_playing:
                    self.main_menu_music.play(-1)
                    self.is_main_menu_music_playing = True

                self.update_leaderboard()
                self.main_menu_draw()

            elif settings.game_state == "INTRO":
                self.is_main_menu_music_playing = False

                settings.game_state = self.game_mode1.intro_update()
                self.game_mode1.intro_draw(settings.SCREEN)

            elif settings.game_state == "MIDDLE GAME":
                self.is_main_menu_music_playing = False

                self.screen_sliding()
                self.move_around()

                self.middle_game_draw()

            elif settings.game_state == "GAME OVER":
                self.is_main_menu_music_playing = False

                self.game_mode1.game_over_draw(settings.SCREEN)

            if not self.is_main_menu_music_playing:
                self.main_menu_music.stop()

            pygame.display.update()
            self.clock.tick(settings.FPS)  # Limits the FPS

    def get_hovered_cell(self):
        mouse_coordinates = pygame.mouse.get_pos()

        mouse_pos = self.grid.convert_local_coordinates_to_pos(mouse_coordinates)
        return mouse_pos

    def screen_sliding(self):
        self.shift += Vector2(-1, 0) * self.SCREEN_SLIDING_SPEED

    def move_around(self):
        self.shift += self.game_mode1.get_movement()

    def event_loop(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit_game()

            if settings.game_state == "SIGN IN":
                self.sign_in_ui.update(event)
            elif settings.game_state == "MAIN MENU":
                self.main_menu_ui.update(event)
            elif settings.game_state == "GAME OVER":
                self.game_mode1.game_over_update(event)

    def quit_game(self):
        self.game_mode1.close()
        pygame.quit()
        sys_exit()


if __name__ == "__main__":
    game = Game()
    game.main_loop()
