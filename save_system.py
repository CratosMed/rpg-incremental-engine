import json
import os
from clases import Player, Item

ARCHIVO_GUARDADO = "savegame.json"


def guardar_partida(heroe: Player):
    """
    Toma al héroe y convierte todos sus datos en un diccionario JSON
    para guardarlo en un archivo local.
    """
    # 1. Convertimos el Inventario (Lista de objetos Item) a diccionarios
    inventario_json = []
    for item in heroe.inventario:
        inventario_json.append(
            {
                "nombre": item.nombre,
                "rareza": item.rareza,
                "valor_base": item.valor_base,
                "tipo": item.tipo,
                "stats": item.stats,
                "nivel_mejora": item.nivel_mejora,
            }
        )

    # 2. Convertimos el Equipamiento (Diccionario de objetos Item) a diccionarios
    equipamiento_json = {}
    for ranura, item in heroe.equipamiento.items():
        if item is not None:
            equipamiento_json[ranura] = {
                "nombre": item.nombre,
                "rareza": item.rareza,
                "valor_base": item.valor_base,
                "tipo": item.tipo,
                "stats": item.stats,
                "nivel_mejora": item.nivel_mejora,
            }
        else:
            equipamiento_json[ranura] = None

    # 3. Creamos el diccionario principal con los datos del Héroe
    datos_guardado = {
        "nombre": heroe.nombre,
        "nivel": heroe.nivel,
        "oro": heroe.oro,
        "puntos_talento": heroe.puntos_talento,
        "crit_chance": heroe.crit_chance,
        "exp_actual": heroe.exp_actual,
        "exp_necesaria": heroe.exp_necesaria,
        "hp_max": heroe.hp_max,
        "hp_actual": heroe.hp_actual,
        "daño_base": heroe.daño_base,
        "inventario": inventario_json,
        "equipamiento": equipamiento_json,
    }

    # 4. Escribimos el archivo JSON
    try:
        with open(ARCHIVO_GUARDADO, "w", encoding="utf-8") as archivo:
            json.dump(datos_guardado, archivo, indent=4, ensure_ascii=False)
        print("💾 Partida guardada exitosamente.")
    except Exception as e:
        print(f"⚠️ Error al guardar: {e}")


def cargar_partida() -> Player | None:
    """
    Lee el archivo JSON (si existe) y reconstruye el objeto Player
    con todo su inventario y equipamiento.
    """
    if not os.path.exists(ARCHIVO_GUARDADO):
        print("📁 No se encontró partida guardada. Iniciando juego nuevo.")
        return None

    try:
        with open(ARCHIVO_GUARDADO, "r", encoding="utf-8") as archivo:
            datos = json.load(archivo)

        # 1. Reconstruimos el Héroe base
        heroe = Player(datos["nombre"])
        heroe.nivel = datos["nivel"]
        heroe.oro = datos["oro"]
        heroe.puntos_talento = datos["puntos_talento"]
        heroe.crit_chance = datos["crit_chance"]
        heroe.exp_actual = datos["exp_actual"]
        heroe.exp_necesaria = datos["exp_necesaria"]
        heroe.hp_max = datos["hp_max"]
        heroe.hp_actual = datos["hp_actual"]
        heroe.daño_base = datos["daño_base"]

        # 2. Reconstruimos el Inventario (De diccionarios a objetos Item)
        heroe.inventario = []
        for item_data in datos["inventario"]:
            nuevo_item = Item(
                nombre=item_data["nombre"],
                rareza=item_data["rareza"],
                valor_base=item_data["valor_base"],
                tipo=item_data["tipo"],
                stats=item_data["stats"],
            )
            nuevo_item.nivel_mejora = item_data["nivel_mejora"]
            heroe.inventario.append(nuevo_item)

        # 3. Reconstruimos el Equipamiento
        heroe.equipamiento = {"Arma": None, "Armadura": None}
        for ranura, item_data in datos["equipamiento"].items():
            if item_data is not None:
                nuevo_item = Item(
                    nombre=item_data["nombre"],
                    rareza=item_data["rareza"],
                    valor_base=item_data["valor_base"],
                    tipo=item_data["tipo"],
                    stats=item_data["stats"],
                )
                nuevo_item.nivel_mejora = item_data["nivel_mejora"]
                heroe.equipamiento[ranura] = nuevo_item

        print("💾 Partida cargada exitosamente.")
        return heroe

    except Exception as e:
        print(f"⚠️ Error al cargar la partida: {e}")
        return None
