import pygame
import os


class SoundManager:
    """Gestor centralizado para los efectos de sonido del juego."""

    def __init__(self):
        # Inicializamos el mixer de Pygame (el motor de audio)
        pygame.mixer.init()
        self.sonidos = {}
        self._cargar_sonidos()

    def _cargar_sonidos(self):
        """Intenta cargar los archivos de audio. Si no existen, no rompe el juego."""
        # Define aquí los nombres de tus archivos
        rutas_esperadas = {
            "ataque_heroe": "assets/sounds/ataque.wav",
            "recibir_daño": "assets/sounds/golpe.wav",
            "botin": "assets/sounds/botin.wav",
            "nivel_up": "assets/sounds/nivel.wav",
            "critico": "assets/sounds/critico.mp3",
        }

        for nombre, ruta in rutas_esperadas.items():
            if os.path.exists(ruta):
                try:
                    sonido = pygame.mixer.Sound(ruta)
                    sonido.set_volume(0.5)  # Volumen al 50% para que no aturda
                    self.sonidos[nombre] = sonido
                except Exception as e:
                    print(f"⚠️ Error cargando sonido {ruta}: {e}")
            else:
                # Guardamos None para evitar errores al intentar reproducirlo
                self.sonidos[nombre] = None

    def play(self, nombre_sonido: str):
        """Reproduce un sonido si existe y está cargado."""
        sonido = self.sonidos.get(nombre_sonido)
        if sonido is not None:
            sonido.play()
