import asyncio
import pygame
import constants as C
from game import Game


async def main():
    pygame.init()
    pygame.display.set_caption(C.TITLE)
    screen = pygame.display.set_mode((C.SCREEN_WIDTH, C.SCREEN_HEIGHT), 0, 32)
    # Fill immediately so the default green pygbag canvas is never visible
    screen.fill((10, 10, 30))
    pygame.display.flip()

    game = Game()
    await game.run()

    pygame.quit()


asyncio.run(main())
