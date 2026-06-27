import pygame
import constants as C


class UI:
    def __init__(self):
        self.font_large  = None
        self.font_medium = None
        self.font_small  = None

    def load_fonts(self):
        self.font_large  = pygame.font.SysFont("monospace", 36, bold=True)
        self.font_medium = pygame.font.SysFont("monospace", 22, bold=True)
        self.font_small  = pygame.font.SysFont("monospace", 16)

    def draw_hud(self, surface: pygame.Surface, player):
        """Zeichnet das HUD oben links."""
        pad = 8
        line_h = 24

        lines = [
            f"Tiefe:    {player.depth()} m",
            f"Punkte:   {player.points}",
            f"Spitzhacke: Lv {player.pickaxe_level}",
            f"Leben:    {'❤️ ' * player.hp}",
        ]

        # Hintergrund-Box
        box_w = 210
        box_h = pad * 2 + line_h * len(lines)
        box = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        box.fill((0, 0, 0, 160))
        surface.blit(box, (pad, pad))

        for i, text in enumerate(lines):
            surf = self.font_small.render(text, True, C.COLOR_HUD_TEXT)
            surface.blit(surf, (pad * 2, pad + i * line_h))

        # Feedback-Text (Mitte oben)
        if player.feedback_text:
            alpha = min(255, player.feedback_timer * 4)
            fb_surf = self.font_medium.render(player.feedback_text, True, C.COLOR_UPGRADE)
            fb_surf.set_alpha(alpha)
            x = (C.SCREEN_WIDTH - fb_surf.get_width()) // 2
            surface.blit(fb_surf, (x, 10))

    def draw_game_over(self, surface: pygame.Surface, points: int):
        overlay = pygame.Surface((C.SCREEN_WIDTH, C.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        title = self.font_large.render("GAME OVER", True, (220, 50, 50))
        sub   = self.font_medium.render(f"Punkte: {points}", True, C.COLOR_WHITE)
        hint  = self.font_small.render("Drücke R für Neustart", True, C.COLOR_HUD_TEXT)

        cx = C.SCREEN_WIDTH // 2
        cy = C.SCREEN_HEIGHT // 2
        surface.blit(title, (cx - title.get_width() // 2, cy - 70))
        surface.blit(sub,   (cx - sub.get_width()   // 2, cy - 10))
        surface.blit(hint,  (cx - hint.get_width()  // 2, cy + 40))

    def draw_win(self, surface: pygame.Surface, points: int):
        overlay = pygame.Surface((C.SCREEN_WIDTH, C.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        title = self.font_large.render("💎 GEWONNEN! 💎", True, (0, 230, 255))
        sub   = self.font_medium.render(f"Punkte: {points}", True, C.COLOR_WHITE)
        hint  = self.font_small.render("Drücke R für Neustart", True, C.COLOR_HUD_TEXT)

        cx = C.SCREEN_WIDTH // 2
        cy = C.SCREEN_HEIGHT // 2
        surface.blit(title, (cx - title.get_width() // 2, cy - 70))
        surface.blit(sub,   (cx - sub.get_width()   // 2, cy - 10))
        surface.blit(hint,  (cx - hint.get_width()  // 2, cy + 40))

    def draw_zone_name(self, surface: pygame.Surface, zone_name: str):
        """Zeigt den aktuellen Zonen-Namen unten rechts."""
        surf = self.font_small.render(f"Zone: {zone_name}", True, C.COLOR_HUD_TEXT)
        x = C.SCREEN_WIDTH - surf.get_width() - 10
        surface.blit(surf, (x, C.SCREEN_HEIGHT - 24))
