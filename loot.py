import random
from clases import Item
from data_manager import db  # <--- Importamos nuestra "Base de Datos"


def generar_arma_aleatoria() -> Item:
    """
    Genera un arma procedimental consumiendo los datos estáticos del JSON.
    """
    # 1. Leemos las bases desde la base de datos cargada en memoria
    bases = db.items_db.get("bases_armas", [])
    if not bases:
        # Fallback de seguridad por si el JSON está vacío o mal escrito
        return Item("Palo Bugueado", "Común", 1, "Arma", {"daño": 1})

    base = random.choice(bases)
    nombre_final = base["nombre"]
    daño_final = base["daño"]
    valor_final = base["valor"]

    rareza = "Común"
    tiene_prefijo, tiene_sufijo = False, False

    # 2. Tirada de Suerte (Roll) para determinar RAREZA
    tirada = random.randint(1, 100)
    if tirada <= 10:
        rareza = "Épico"
        tiene_prefijo = True
        tiene_sufijo = True
    elif tirada <= 35:
        rareza = "Raro"
        if random.choice([True, False]):
            tiene_prefijo = True
        else:
            tiene_sufijo = True
    elif tirada <= 65:
        rareza = "Mágico"
        if random.choice([True, False]):
            tiene_prefijo = True
        else:
            tiene_sufijo = True

    # 3. Aplicar los modificadores leyendo de la base de datos
    prefijos_db = db.items_db.get("prefijos", [])
    sufijos_db = db.items_db.get("sufijos", [])

    if tiene_prefijo and prefijos_db:
        lista_pref = (
            prefijos_db[1:]
            if rareza != "Común" and len(prefijos_db) > 1
            else prefijos_db
        )
        pref = random.choice(lista_pref)
        nombre_final = f"{pref['nombre']} {nombre_final}"
        daño_final += pref["mod_daño"]
        valor_final = int(valor_final * pref["mod_valor"])

    if tiene_sufijo and sufijos_db:
        suf = random.choice(sufijos_db)
        nombre_final = f"{nombre_final} {suf['nombre']}"
        daño_final += suf["mod_daño"]
        valor_final = int(valor_final * suf["mod_valor"])

    daño_final = max(1, daño_final)

    return Item(
        nombre=nombre_final,
        rareza=rareza,
        valor_base=valor_final,
        tipo="Arma",
        stats={"daño": daño_final},
    )
