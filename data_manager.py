import json
import os


class DataManager:
    """Carga y almacena en memoria todas las bases de datos estáticas del juego."""

    def __init__(self):
        self.enemies_db = {}
        self.items_db = {}
        self.cargar_todo()

    def cargar_json(self, ruta: str) -> dict:
        """Lee un archivo JSON y devuelve su contenido."""
        if not os.path.exists(ruta):
            print(f"⚠️ Crítico: Base de datos {ruta} no encontrada.")
            return {}

        with open(ruta, "r", encoding="utf-8") as archivo:
            return json.load(archivo)

    def cargar_todo(self):
        """Carga todos los archivos de la carpeta data."""
        self.enemies_db = self.cargar_json("data/enemies.json")
        self.items_db = self.cargar_json("data/items.json")
        self.zones_db = self.cargar_json("data/zones.json")
        print("📁 Bases de datos cargadas exitosamente.")


# Instancia global para importar en otros archivos
db = DataManager()
