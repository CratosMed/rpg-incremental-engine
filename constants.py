import pygame

# Dimensiones de la ventana
WIDTH: int = 800
HEIGHT: int = 600

# Paleta de Colores (Tipados como tuplas de 3 enteros)
BLACK: tuple[int, int, int] = (0, 0, 0)
WHITE: tuple[int, int, int] = (255, 255, 255)
RED: tuple[int, int, int] = (200, 50, 50)
GREEN: tuple[int, int, int] = (50, 200, 50)
GOLD: tuple[int, int, int] = (255, 215, 0)
BLUE_INFO: tuple[int, int, int] = (100, 200, 255)
GRAY_UI: tuple[int, int, int] = (30, 30, 30)

# Configuraciones de Balance (Fáciles de editar aquí)
PROB_EXITO_HERRERIA: int = 70
CHANCE_DROP_ITEM: int = 40
COOLDOWN_HEROE: int = 1000
COOLDOWN_ENEMIGO: int = 1500
VEL_ANIMACION: int = 100

# Sistema de Oleadas
ENEMIGOS_PARA_JEFE: int = 5
INCREMENTO_DIFICULTAD_POR_OLEADA: float = 1.2  # 20% más fuertes cada vez
