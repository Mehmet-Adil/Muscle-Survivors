import pygame
import random
import database
from movement_analyser import MovementAnalyser
import UI
from miscellaneous import Timer
import settings
from os.path import join as path_join


class Player:
    def __init__(self, color, size, pos):
        self.color = color
        self.size = size
        self.pos = pos
        self.movement = pygame.Vector2(0, 0)

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, self.pos, self.size)


class Tile:
    def __init__(self, pos, color):
        self.pos = pos
        self.color = color


class GameMode1:
    MOVEMENT_SPEED = 10

    def __init__(self, grid, difficulty="EASY"):
        self.obstacles = []
        self.obstacle_summoned = []

        self.player = Player("#75a743", grid.tile_height / 2 * 0.6, (125, settings.WINDOW_SIZE[1]//2))

        self.grid = grid

        self.spawn_amount = 1
        self.difficulty = difficulty
        self.setup_difficulty()

        self.movement_analyser = MovementAnalyser()

        self.down_timer = Timer(3)
        self.up_timer = Timer(3)
        self.game_timer = Timer(has_sound=False)

        self.intro_check_text = "UP!"

        self.last_checked_frame_n = 0
        self.update_movement_every_n_frames = 3

        self.movement_image = None

        self.game_over_buttons = pygame.sprite.Group()
        self.game_over_buttons.add(UI.Button(None, (settings.WINDOW_SIZE[0]/2, settings.WINDOW_SIZE[1]/2 - 75),
                                             self.restart_game, height=75, width=350, font_size=55, text="PLAY AGAIN!"))
        self.game_over_buttons.add(UI.Button(None, (settings.WINDOW_SIZE[0]/2, settings.WINDOW_SIZE[1]/2 + 75),
                                             self.to_main_menu, height=75, width=350, font_size=55, text="MAIN MENU!"))

        self.middle_game_music = pygame.mixer.Sound(path_join("Music", "One Dream.wav"))
        self.middle_game_music.set_volume(0.3)
        self.death_sfx = pygame.mixer.Sound(path_join("Music", "Death Sound Effect.wav"))
        self.death_sfx.set_volume(0.25)

    def set_difficulty(self, difficulty):
        self.difficulty = difficulty
        self.setup_difficulty()

    def setup_difficulty(self):
        self.spawn_amount = {"EASY": 0.1, "NORMAL": 0.25, "HARD": 0.4}[self.difficulty.upper()]

    def intro_update(self):
        image = self.movement_analyser.get_positions()
        self.movement_image = self.movement_analyser.convert_cv2_img_to_pygame_img(image)

        self.up_timer.start()

        if self.up_timer.is_over():  # When counter reaches 0
            self.movement_analyser.get_up_positions()

            if not self.movement_analyser.up_shoulder_positions or not self.movement_analyser.up_elbow_positions:
                self.up_timer.reset()
                self.up_timer.start()
                return "INTRO"

            self.intro_check_text = "DOWN!"
            self.down_timer.start()

        if self.down_timer.is_over():  # When counter reaches 0
            self.movement_analyser.get_down_positions()

            if not self.movement_analyser.down_shoulder_positions or not self.movement_analyser.down_elbow_positions:
                self.down_timer.reset()
                self.down_timer.start()
                return "INTRO"

            self.movement_analyser.calculate_setup_means()
            self.game_timer.start()
            self.middle_game_music.play(-1)

            return "MIDDLE GAME"

        return "INTRO"

    def intro_draw(self, screen):
        screen.fill("#ebede9")

        UI.put_text(screen, text="MUSCLE SURVIVORS", font_size=75, pos=(settings.WINDOW_SIZE[0]/2, settings.WINDOW_SIZE[1] // 2 - 350), anchor="MIDTOP", is_underlined=True)
        UI.put_text(screen, text=self.intro_check_text, pos=(settings.WINDOW_SIZE[0]/2, settings.WINDOW_SIZE[1] // 2 - 250), anchor="MIDTOP", is_bold=True)

        timer_text = f"{self.up_timer.get_time(True) if self.intro_check_text == 'UP!' else self.down_timer.get_time(True)}s"
        UI.put_text(screen, text=timer_text, pos=(settings.WINDOW_SIZE[0]/2, settings.WINDOW_SIZE[1] // 2 - 200), anchor="MIDTOP")

        screen.blit(self.movement_image, self.movement_image.get_rect(center=(settings.WINDOW_SIZE[0] / 2, settings.WINDOW_SIZE[1] / 2 + 100)))
        pygame.display.update()

    def update(self):
        if self.check_collisions():
            self.middle_game_music.stop()
            self.death_sfx.play()

            settings.game_state = "GAME OVER"

            database.insert_score(settings.user, self.difficulty, self.game_timer.get_time())
            return

        self.generate_obstacles(self.generate_obstacle_positions(self.grid.convert_local_coordinates_to_pos(self.player.pos)))
        self.clear_obstacles()

    def draw(self, screen):
        self.player.draw(screen)

        for tile in self.obstacles:
            pygame.draw.rect(screen, tile.color, pygame.Rect(*self.grid.convert_pos_to_coordinates(tile.pos),
                                                             self.grid.tile_width, self.grid.tile_height))

        UI.put_text(screen, text=f"Time Survived: {self.game_timer.get_time()}s", pos=(30, 30), anchor="TOPLEFT")
        player_pos = self.grid.convert_local_coordinates_to_pos(self.player.pos)
        UI.put_text(screen, text=f"Position: {player_pos[0]}, {-player_pos[1]}",
                    pos=(30, 90), anchor="TOPLEFT")

    def game_over_update(self, event):
        self.game_over_buttons.update(event)

    def game_over_draw(self, screen):
        screen.fill((255, 75, 75))

        UI.put_text(screen, is_underlined=True, text="GAME OVER!", font_size=120, pos=(settings.WINDOW_SIZE[0]/2, settings.WINDOW_SIZE[1] // 2 - 350), anchor="MIDTOP")
        self.game_over_buttons.draw(screen)

    def generate_obstacle_positions(self, pos):
        line_n_tiles_y = self.grid.line_height // self.grid.tile_height
        line_n_tiles_x = self.grid.line_width // self.grid.tile_width

        pos = (pos[0] + line_n_tiles_x, pos[1])

        obstacles = [(pos[0], random.randint(pos[1] - round(line_n_tiles_y*3), pos[1] + round(line_n_tiles_y*3)))
                     for _ in range(0, random.randint(1, int((self.grid.max_y-self.grid.min_y) * self.spawn_amount // self.grid.tile_height)))]

        return obstacles

    def generate_obstacles(self, positions):
        if positions[0][0] in self.obstacle_summoned:
            return

        for position in positions:
            for obstacle in self.obstacles:
                if position == obstacle.pos:
                    break
            else:
                self.obstacles.append(Tile(position, (230, 10, 20)))

        self.obstacle_summoned.append(positions[0][0])

    def clear_obstacles(self):
        line_n_tiles_x = self.grid.line_width // self.grid.tile_width
        line_n_tiles_y = self.grid.line_height // self.grid.tile_height

        player_pos = self.grid.convert_local_coordinates_to_pos(self.player.pos)

        for obstacle in self.obstacles.copy():
            if obstacle.pos[0] < player_pos[0] - round(line_n_tiles_x * 3):
                try:
                    self.obstacle_summoned.remove(obstacle.pos[0])
                except ValueError:
                    pass

                self.obstacles.remove(obstacle)

            elif obstacle.pos[0] > player_pos[0] + round(line_n_tiles_x * 3):
                try:
                    self.obstacle_summoned.remove(obstacle.pos[0])
                except ValueError:
                    pass

                self.obstacles.remove(obstacle)

            elif obstacle.pos[1] < player_pos[1] - round(line_n_tiles_y * 3):
                try:
                    self.obstacle_summoned.remove(obstacle.pos[0])
                except ValueError:
                    pass

                self.obstacles.remove(obstacle)

            elif obstacle.pos[1] > player_pos[1] + round(line_n_tiles_y * 3):
                try:
                    self.obstacle_summoned.remove(obstacle.pos[0])
                except ValueError:
                    pass

                self.obstacles.remove(obstacle)

    def check_collisions(self):
        for obstacle in self.obstacles:
            # These are the conditions which suggest the PLAYER is NOT colliding with a TILE
            if self.player.pos[0] + self.player.size <= self.grid.convert_pos_to_coordinates(obstacle.pos)[0]:
                continue
            if self.player.pos[0] - self.player.size > self.grid.convert_pos_to_coordinates(obstacle.pos)[0] + self.grid.tile_width:
                continue
            if self.player.pos[1] + self.player.size <= self.grid.convert_pos_to_coordinates(obstacle.pos)[1]:
                continue
            if self.player.pos[1] - self.player.size > self.grid.convert_pos_to_coordinates(obstacle.pos)[1] + self.grid.tile_height:
                continue

            return True

    def restart_game(self):
        self.grid.reset()

        self.obstacles = []
        self.obstacle_summoned = []
        self.player = Player("#75a743", self.grid.tile_height / 2 * 0.6, (100, settings.WINDOW_SIZE[1]/2))

        self.movement_analyser.reset()

        self.down_timer.reset()
        self.up_timer.reset()
        self.game_timer.reset()

        self.intro_check_text = "UP!"

        self.last_checked_frame_n = 0
        self.update_movement_every_n_frames = 3

        self.movement_image = None

        settings.game_state = "INTRO"

    def to_main_menu(self):
        self.restart_game()

        settings.game_state = "MAIN MENU"

    def get_movement(self):
        self.last_checked_frame_n += 1
        if self.last_checked_frame_n <= self.update_movement_every_n_frames:
            return self.player.movement

        self.last_checked_frame_n = 0
        self.movement_analyser.get_positions()
        self.player.movement = pygame.Vector2(0, self.MOVEMENT_SPEED * self.movement_analyser.get_movement_percentage())

        return self.player.movement

    def close(self):
        self.movement_analyser.close_analyser()
