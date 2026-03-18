import pygame
import os


class AssetManager:
    """Gestor dinámico de imágenes con sistema de caché."""

    def __init__(self):
        self.cache_enemigos = {}
        self.frames_heroe = []

    def cargar_heroe(self):
        """Carga la animación del héroe (estática por ahora)."""
        if not self.frames_heroe:
            try:
                hoja = pygame.image.load("assets/heroe/Idle.png").convert_alpha()
                ancho_f = hoja.get_width() // 6
                self.frames_heroe = [
                    pygame.transform.scale(
                        hoja.subsurface(
                            pygame.Rect(i * ancho_f, 0, ancho_f, hoja.get_height())
                        ),
                        (150, 150),
                    )
                    for i in range(6)
                ]
            except Exception as e:
                print(f"⚠️ Error cargando héroe: {e}")
                self.frames_heroe = [pygame.Surface((150, 150)) for _ in range(6)]
        return self.frames_heroe

    def obtener_frames_enemigo(self, carpeta_sprite: str):
        """
        Busca todos los PNG de una carpeta y los carga como frames de animación.
        Si ya los cargó antes, los devuelve de la memoria RAM instantáneamente.
        """
        # 1. Si ya está en memoria, lo devolvemos rápido
        if carpeta_sprite in self.cache_enemigos:
            return self.cache_enemigos[carpeta_sprite]

        # 2. Si no, lo leemos del disco duro
        frames = []
        try:
            if os.path.exists(carpeta_sprite):
                # Leemos todos los archivos que terminen en .png y los ordenamos alfabéticamente
                archivos = sorted(
                    [f for f in os.listdir(carpeta_sprite) if f.endswith(".png")]
                )
                for archivo in archivos:
                    ruta_completa = os.path.join(carpeta_sprite, archivo)
                    img = pygame.image.load(ruta_completa).convert_alpha()
                    frames.append(pygame.transform.scale(img, (150, 150)))

            if not frames:
                raise Exception(f"Carpeta vacía o inexistente: {carpeta_sprite}")

        except Exception as e:
            print(f"⚠️ Error de Asset: {e}")
            # Si falla, dibujamos un cuadrado rojo de error para que te des cuenta visualmente
            sup = pygame.Surface((150, 150))
            sup.fill((200, 0, 0))
            frames = [sup]

        # 3. Guardamos en la caché para el futuro y retornamos
        self.cache_enemigos[carpeta_sprite] = frames
        return frames
