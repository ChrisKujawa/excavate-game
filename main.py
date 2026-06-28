import asyncio
import pygame
import constants as C
from game import Game


async def main():
    pygame.init()
    pygame.display.set_caption(C.TITLE)
    # pygame.SCALED: SDL renders the game at 800x600 and scales to the actual
    # window/screen size internally.  display.get_surface() always returns an
    # 800x600 surface so game code never needs to know about screen resolution.
    flags = pygame.SCALED if not C.IS_WEB else 0
    screen = pygame.display.set_mode((C.SCREEN_WIDTH, C.SCREEN_HEIGHT), flags, 32)
    # Fill immediately so the default green pygbag canvas is never visible
    screen.fill((10, 10, 30))
    pygame.display.flip()

    game = Game()
    await game.run()

    pygame.quit()


asyncio.run(main())
