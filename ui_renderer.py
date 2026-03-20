import pygame
from constants import *

# =====================================================================
# INICIALIZACIÓN DE FUENTES GLOBALES
# =====================================================================
pygame.font.init()
font_grande = pygame.font.Font(None, 48)
font_normal = pygame.font.Font(None, 32)
font_pequena = pygame.font.Font(None, 24)


def dibujar_barra_vida(pantalla, x, y, hp_actual, hp_max, fuente):
    """Dibuja una barra de vida con fondo, frente dinámico, borde y texto numérico centrado."""
    hp_mostrar = max(0, hp_actual)
    porcentaje = hp_mostrar / hp_max if hp_max > 0 else 0

    pygame.draw.rect(pantalla, (50, 50, 50), (x, y, 200, 25))
    color = GREEN if x < 400 else RED
    pygame.draw.rect(pantalla, color, (x, y, int(200 * porcentaje), 25))
    pygame.draw.rect(pantalla, WHITE, (x, y, 200, 25), 2)

    texto_hp = fuente.render(f"{int(hp_mostrar)} / {int(hp_max)}", True, WHITE)
    rect_texto = texto_hp.get_rect(center=(x + 100, y + 12))
    pantalla.blit(texto_hp, rect_texto)


class UIRenderer:
    """Clase encargada de dibujar toda la interfaz gráfica del juego."""

    def __init__(self, screen):
        self.screen = screen

    def dibujar_hud_combate(
        self,
        heroe,
        enemigo_actual,
        cd_actual_heroe,
        cd_enemigo,
        tiempo_actual,
        t_ataque_h,
        t_ataque_e,
        datos_zona_actual,
        jefe_derrotados_en_zona,
        mensaje_accion,
        mensaje_botin,
    ):

        # Cooldown Visual
        prog_h = min(1.0, (tiempo_actual - t_ataque_h) / cd_actual_heroe)
        pygame.draw.rect(self.screen, GOLD, (50, 40, int(150 * prog_h), 5))

        prog_e = min(1.0, (tiempo_actual - t_ataque_e) / cd_enemigo)
        pygame.draw.rect(self.screen, RED, (500, 40, int(150 * prog_e), 5))

        # Textos Superiores
        self.screen.blit(
            font_normal.render(f"{heroe.nombre} (Nv. {heroe.nivel})", True, WHITE),
            (50, 170),
        )
        self.screen.blit(
            font_normal.render(f"{enemigo_actual.nombre}", True, WHITE), (500, 170)
        )

        # Barras de Vida
        dibujar_barra_vida(
            self.screen, 50, 200, heroe.hp_actual, heroe.hp_max, font_pequena
        )
        dibujar_barra_vida(
            self.screen,
            500,
            200,
            enemigo_actual.hp_actual,
            enemigo_actual.hp_max,
            font_pequena,
        )

        # Textos Inferiores
        self.screen.blit(font_normal.render(f"Oro: {heroe.oro}", True, GOLD), (50, 240))
        self.screen.blit(
            font_normal.render(
                f"EXP: {heroe.exp_actual} / {heroe.exp_necesaria}", True, BLUE_INFO
            ),
            (50, 275),
        )

        txt_zona = font_pequena.render(
            f"Zona: {datos_zona_actual.get('nombre', 'Desconocida')} | Jefes: {jefe_derrotados_en_zona}/{datos_zona_actual.get('jefes_para_avanzar', 5)}",
            True,
            (200, 200, 200),
        )
        self.screen.blit(txt_zona, (WIDTH - txt_zona.get_width() - 20, 20))

        # Mensajes de Acción y Botín
        self.screen.blit(
            font_normal.render(mensaje_accion, True, WHITE), (WIDTH // 2 - 100, 450)
        )
        if mensaje_botin:
            color_b = GOLD if "ÉPICO" in mensaje_botin else WHITE
            self.screen.blit(
                font_normal.render(mensaje_botin, True, color_b),
                (WIDTH // 2 - 100, 490),
            )

    def dibujar_inventario(self, heroe):
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(220)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))

        self.screen.blit(
            font_grande.render("MOCHILA Y PROGRESIÓN", True, GOLD),
            (WIDTH // 2 - 200, 50),
        )
        self.screen.blit(
            font_normal.render(
                "Presiona [1-9] Vender | [SHIFT]+[1-9] Equipar o Engarzar",
                True,
                (150, 150, 150),
            ),
            (50, 110),
        )

        y_off = 160
        if len(heroe.inventario) == 0:
            self.screen.blit(
                font_normal.render("Mochila vacía.", True, (100, 100, 100)),
                (100, y_off),
            )
        for i, item in enumerate(heroe.inventario[:9]):
            color_r = (
                GOLD
                if item.rareza == "Raro"
                else BLUE_INFO if item.rareza == "Mágico" else WHITE
            )
            prefijo_texto = "(Gema) " if item.tipo == "Gema" else ""
            txt = font_normal.render(
                f"{i+1}. {prefijo_texto}{item.nombre} ({item.valor_base} Oro)",
                True,
                color_r,
            )
            self.screen.blit(txt, (100, y_off))
            y_off += 40

        # Herrería
        pygame.draw.rect(self.screen, GRAY_UI, (450, 150, 320, 220))
        pygame.draw.rect(self.screen, WHITE, (450, 150, 320, 220), 2)
        self.screen.blit(font_normal.render("HERRERÍA", True, GOLD), (550, 170))

        arma = heroe.equipamiento.get("Arma")
        if arma:
            self.screen.blit(
                font_normal.render(
                    f"Eq: {arma.nombre} (+{arma.nivel_mejora})", True, WHITE
                ),
                (465, 205),
            )
            self.screen.blit(
                font_normal.render(
                    f"Daño base: {arma.stats.get('daño', 0)}", True, GREEN
                ),
                (465, 235),
            )
            gemas_nombres = (
                ", ".join([g.nombre for g in arma.gemas_equipadas])
                if arma.gemas_equipadas
                else "Ninguna"
            )
            self.screen.blit(
                font_pequena.render(
                    f"Huecos ({len(arma.gemas_equipadas)}/{arma.sockets}): {gemas_nombres}",
                    True,
                    BLUE_INFO,
                ),
                (465, 265),
            )

            costo = 100 + (arma.nivel_mejora * 50)
            color_c = GOLD if heroe.oro >= costo else RED
            self.screen.blit(
                font_normal.render(f"Mejorar: {costo} Oro [H]", True, color_c),
                (465, 310),
            )
        else:
            self.screen.blit(
                font_normal.render("Sin arma equipada.", True, RED), (465, 220)
            )

        # Talentos
        pygame.draw.rect(self.screen, (20, 20, 40), (450, 390, 320, 150))
        pygame.draw.rect(self.screen, BLUE_INFO, (450, 390, 320, 150), 2)

        color_t = GOLD if heroe.puntos_talento > 0 else (100, 100, 100)
        self.screen.blit(
            font_normal.render(
                f"PUNTOS DE TALENTO: {heroe.puntos_talento}", True, color_t
            ),
            (465, 410),
        )

        if heroe.puntos_talento > 0:
            self.screen.blit(
                font_normal.render("[F] +5% Daño Crítico", True, WHITE), (465, 450)
            )
            self.screen.blit(
                font_normal.render("[G] +10% Vel. Ataque", True, WHITE), (465, 490)
            )
        else:
            self.screen.blit(
                font_normal.render(
                    "Sube de nivel para ganar puntos", True, (120, 120, 120)
                ),
                (465, 460),
            )

    def dibujar_tienda(self, heroe, inventario_tienda):
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(220)
        overlay.fill((20, 10, 10))
        self.screen.blit(overlay, (0, 0))

        self.screen.blit(
            font_grande.render("COMERCIANTE AMBULANTE", True, GOLD),
            (WIDTH // 2 - 220, 50),
        )
        self.screen.blit(
            font_normal.render(
                "Presiona [1-5] para Comprar | [R] Refrescar (50 Oro)",
                True,
                (150, 150, 150),
            ),
            (50, 110),
        )
        self.screen.blit(
            font_normal.render(f"Tu Oro: {heroe.oro}", True, GOLD), (600, 110)
        )

        y_off = 180
        if len(inventario_tienda) == 0:
            self.screen.blit(
                font_normal.render(
                    "El comerciante se quedó sin objetos.", True, (100, 100, 100)
                ),
                (100, y_off),
            )

        for i, item in enumerate(inventario_tienda):
            color_r = (
                GOLD
                if item.rareza == "Raro"
                else BLUE_INFO if item.rareza == "Mágico" else WHITE
            )
            prefijo = "(Gema) " if item.tipo == "Gema" else ""
            precio = item.valor_base * 3

            txt_nombre = font_normal.render(
                f"{i+1}. {prefijo}{item.nombre}", True, color_r
            )
            self.screen.blit(txt_nombre, (100, y_off))

            color_precio = GREEN if heroe.oro >= precio else RED
            txt_precio = font_normal.render(f"Precio: {precio} Oro", True, color_precio)
            self.screen.blit(txt_precio, (550, y_off))

            if item.tipo == "Arma":
                stat_txt = font_pequena.render(
                    f"Daño: {item.stats.get('daño', 0)} | Huecos: {item.sockets}",
                    True,
                    (200, 200, 200),
                )
                self.screen.blit(stat_txt, (140, y_off + 30))

            y_off += 60
