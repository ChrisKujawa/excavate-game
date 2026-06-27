import pygame
import constants as C
import highscore as hs


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
            x = (surface.get_width() - fb_surf.get_width()) // 2
            surface.blit(fb_surf, (x, 10))

    def draw_game_over(self, surface: pygame.Surface, points: int):
        sw, sh = surface.get_width(), surface.get_height()
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        surface.blit(overlay, (0, 0))

        cx = sw // 2

        title = self.font_large.render("GAME OVER", True, (220, 50, 50))
        sub   = self.font_medium.render(f"Punkte: {points}", True, C.COLOR_WHITE)
        surface.blit(title, (cx - title.get_width() // 2, 60))
        surface.blit(sub,   (cx - sub.get_width()   // 2, 115))

        self._draw_highscore_table(surface, cx, 165)

        hint = self.font_small.render("Drücke R für Neustart", True, C.COLOR_HUD_TEXT)
        surface.blit(hint, (cx - hint.get_width() // 2, sh - 40))

    def draw_win(self, surface: pygame.Surface, points: int):
        sw, sh = surface.get_width(), surface.get_height()
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        surface.blit(overlay, (0, 0))

        cx = sw // 2

        title = self.font_large.render("💎 DIAMANT GEFUNDEN! 💎", True, (0, 230, 255))
        sub   = self.font_medium.render(f"Punkte: {points}", True, C.COLOR_WHITE)
        surface.blit(title, (cx - title.get_width() // 2, 60))
        surface.blit(sub,   (cx - sub.get_width()   // 2, 115))

        self._draw_highscore_table(surface, cx, 165)

        hint = self.font_small.render("Drücke R für Neustart", True, C.COLOR_HUD_TEXT)
        surface.blit(hint, (cx - hint.get_width() // 2, sh - 40))

    def _draw_highscore_table(self, surface: pygame.Surface, cx: int, y: int):
        """Gemeinsame Highscore-Tabelle für Game-Over und Win."""
        hs_title = self.font_medium.render("🏆 Bestenliste", True, C.COLOR_UPGRADE)
        surface.blit(hs_title, (cx - hs_title.get_width() // 2, y))
        scores = hs.load()
        if scores:
            for i, entry in enumerate(scores):
                line = f"{i+1}. {entry['name']:<12} {entry['points']:>6} Pkt"
                s = self.font_small.render(line, True, C.COLOR_WHITE)
                surface.blit(s, (cx - s.get_width() // 2, y + 38 + i * 24))
        else:
            none_s = self.font_small.render("Noch keine Einträge", True, (140, 140, 140))
            surface.blit(none_s, (cx - none_s.get_width() // 2, y + 38))

    def draw_zone_name(self, surface: pygame.Surface, zone_name: str):
        """Zeigt den aktuellen Zonen-Namen unten rechts."""
        surf = self.font_small.render(f"Zone: {zone_name}", True, C.COLOR_HUD_TEXT)
        x = surface.get_width() - surf.get_width() - 10
        surface.blit(surf, (x, surface.get_height() - 24))

    def draw_start_screen(self, surface: pygame.Surface):
        surface.fill((10, 10, 30))

        sw, sh = surface.get_width(), surface.get_height()
        cx = sw // 2

        # --- TEC Charakter links oben ---
        self._draw_tec_character(surface, 100, 110, scale=2)

        # --- Titel ---
        title = self.font_large.render("EXCAVATE!", True, (255, 215, 0))
        sub   = self.font_medium.render("Grab dich zum großen Diamanten!", True, C.COLOR_WHITE)
        hint  = self.font_small.render("Tippe oder drücke ENTER zum Starten", True, (180, 180, 180))

        surface.blit(title, (cx - title.get_width() // 2, 55))
        surface.blit(sub,   (cx - sub.get_width()   // 2, 105))

        # --- Steuerung ---
        controls = [
            "← →        Bewegen / Graben",
            "↑ / SPACE  Springen",
            "↓           Nach unten graben",
            "R           Neustart",
            "F11         Vollbild an/aus",
        ]
        ctrl_y = 155
        ctrl_title = self.font_small.render("── Steuerung ──", True, (180, 180, 255))
        surface.blit(ctrl_title, (cx - ctrl_title.get_width() // 2, ctrl_y))
        for i, line in enumerate(controls):
            s = self.font_small.render(line, True, (200, 200, 255))
            surface.blit(s, (cx - s.get_width() // 2, ctrl_y + 22 + i * 22))

        # --- Highscores ---
        scores = hs.load()
        hs_y = 310
        hs_title = self.font_medium.render("🏆 Bestenliste", True, C.COLOR_UPGRADE)
        surface.blit(hs_title, (cx - hs_title.get_width() // 2, hs_y))
        if scores:
            for i, entry in enumerate(scores):
                line = f"{i+1}. {entry['name']:<12} {entry['points']:>6} Pkt"
                s = self.font_small.render(line, True, C.COLOR_WHITE)
                surface.blit(s, (cx - s.get_width() // 2, hs_y + 35 + i * 22))
        else:
            none_s = self.font_small.render("Noch keine Einträge", True, (140, 140, 140))
            surface.blit(none_s, (cx - none_s.get_width() // 2, hs_y + 35))

        surface.blit(hint, (cx - hint.get_width() // 2, sh - 40))

    def _draw_tec_character(self, surface: pygame.Surface, cx: int, cy: int, scale: int = 1):
        """Zeichnet den TEC-Charakter als Mini-Figur."""
        w = C.PLAYER_WIDTH  * scale
        h = C.PLAYER_HEIGHT * scale
        x = cx - w // 2
        y = cy - h // 2

        # Körper
        body = pygame.Rect(x, y, w, h)
        pygame.draw.rect(surface, C.COLOR_PLAYER, body, border_radius=4 * scale)

        # Augen
        eye_y = y + 6 * scale
        pygame.draw.circle(surface, C.COLOR_BLACK, (x + 6 * scale, eye_y), 3 * scale)
        pygame.draw.circle(surface, C.COLOR_BLACK, (x + w - 6 * scale, eye_y), 3 * scale)

        # Name über dem Charakter
        name_surf = self.font_medium.render(C.PLAYER_NAME, True, C.COLOR_WHITE)
        surface.blit(name_surf, (cx - name_surf.get_width() // 2, y - name_surf.get_height() - 4))

        # Pickaxe-Symbol rechts vom Charakter
        tool_surf = self.font_medium.render("⛏", True, (200, 200, 200))
        surface.blit(tool_surf, (x + w + 6, cy - tool_surf.get_height() // 2))

    def draw_name_input(self, surface: pygame.Surface, name: str, points: int):
        """Eingabe-Screen für Highscore-Name."""
        sw, sh = surface.get_width(), surface.get_height()
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        surface.blit(overlay, (0, 0))

        cx = sw // 2
        cy = sh // 2

        title = self.font_large.render("NEUER HIGHSCORE!", True, C.COLOR_UPGRADE)
        pts   = self.font_medium.render(f"Punkte: {points}", True, C.COLOR_WHITE)
        prompt = self.font_medium.render("Dein Name:", True, C.COLOR_WHITE)
        name_surf = self.font_large.render(name + "_", True, (0, 230, 255))
        hint  = self.font_small.render("ENTER zum Speichern", True, (180, 180, 180))

        surface.blit(title,     (cx - title.get_width()     // 2, cy - 120))
        surface.blit(pts,       (cx - pts.get_width()       // 2, cy - 65))
        surface.blit(prompt,    (cx - prompt.get_width()    // 2, cy - 20))
        surface.blit(name_surf, (cx - name_surf.get_width() // 2, cy + 20))
        surface.blit(hint,      (cx - hint.get_width()      // 2, cy + 80))
