import asyncio
import pygame
import constants as C
from game import Game


async def main():
    pygame.init()
    pygame.display.set_caption(C.TITLE)
    pygame.display.set_mode((C.SCREEN_WIDTH, C.SCREEN_HEIGHT))

    game = Game()
    await game.run()

    pygame.quit()


asyncio.run(main())
