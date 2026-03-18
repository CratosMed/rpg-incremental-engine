import pygame
from constants import WHITE, RED


class DamageText:
    """Clase para gestionar los números de daño flotantes en pantalla."""

    def __init__(self, x: int, y: int, texto: str, color: tuple[int, int, int] = WHITE):
        self.x = x
        self.y = y
        self.texto = texto
        self.color = color
        self.vida = 60  # El texto durará 60 fotogramas (aprox 1 segundo)
        self.font = pygame.font.Font(None, 36)

    def update(self):
        """Mueve el texto hacia arriba y reduce su tiempo de vida."""
        self.y -= 1  # Sube lentamente
        self.vida -= 1

    def draw(self, pantalla: pygame.Surface):
        """Dibuja el texto con un efecto de transparencia (alpha) basado en su vida."""
        if self.vida > 0:
            surf = self.font.render(self.texto, True, self.color)
            # Opcional: Podrías añadir lógica de transparencia aquí
            pantalla.blit(surf, (self.x, self.y))


class VisualEffectsManager:
    def __init__(self):
        self.efectos_activos = []
        # --- NUEVO: Control de parpadeo ---
        self.flash_heroe = 0
        self.flash_enemigo = 0

    def añadir_daño(self, x: int, y: int, cantidad: int, objetivo: str):
        self.efectos_activos.append(DamageText(x, y, f"-{cantidad}", RED))
        # Iniciamos el flash (parpadeo) por 5 frames
        if objetivo == "heroe":
            self.flash_heroe = 5
        else:
            self.flash_enemigo = 5

    def update_y_draw(self, pantalla: pygame.Surface):
        for efecto in self.efectos_activos[:]:
            efecto.update()
            efecto.draw(pantalla)
            if efecto.vida <= 0:
                self.efectos_activos.remove(efecto)

        # Reducimos los contadores de flash en cada ciclo
        if self.flash_heroe > 0:
            self.flash_heroe -= 1
        if self.flash_enemigo > 0:
            self.flash_enemigo -= 1
