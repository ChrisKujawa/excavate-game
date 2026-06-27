import pygame
import constants as C
from game import Game


def main():
    pygame.init()
    pygame.display.set_caption(C.TITLE)
    pygame.display.set_mode((C.SCREEN_WIDTH, C.SCREEN_HEIGHT))

    game = Game()
    game.run()

    pygame.quit()


if __name__ == "__main__":
    main()
