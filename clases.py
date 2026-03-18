class Item:
    def __init__(
        self, nombre: str, rareza: str, valor_base: int, tipo: str, stats: dict = None
    ):
        # Propiedades básicas del objeto
        self.nombre = nombre
        self.rareza = rareza  # Ej: "Común", "Mágico", "Raro", "Único"
        self.valor_base = valor_base  # Cuánto oro te dan en la tienda por él
        self.tipo = tipo  # Ej: "Arma", "Armadura", "Material"

        # Las estadísticas serán un diccionario. Si no le pasamos nada, crea uno vacío {}
        self.stats = stats if stats is not None else {}

        # Nivel de mejora en la herrería (empieza en 0)
        self.nivel_mejora = 0

    def __str__(self) -> str:
        texto = f"[{self.rareza}] {self.nombre}"
        if self.nivel_mejora > 0:
            texto += f" (+{self.nivel_mejora})"

        texto += f" | Tipo: {self.tipo} | Valor: {self.valor_base} oro"

        if self.stats:
            texto += f" | Stats: {self.stats}"

        return texto


class Player:
    def __init__(self, nombre):
        self.nombre = nombre
        self.nivel = 1
        self.oro = 0
        self.puntos_talento = 0
        self.exp_actual = 0
        self.exp_necesaria = 100

        # Stats Base
        self.hp_max = 100
        self.hp_actual = 100
        self.daño_base = 10
        self.crit_chance = 5

        # --- NUEVAS ESTADÍSTICAS BASE ---
        self.evasion_base = 0  # Probabilidad de esquivar (0 a 100%)
        self.robo_vida_base = 0.0  # Porcentaje de daño que se cura (Ej: 0.1 = 10%)
        self.vel_ataque_base = 0  # Reducción del cooldown en milisegundos

        self.inventario = []
        self.equipamiento = {"Arma": None, "Armadura": None}

    def ganar_exp(self, cantidad):
        """Añade experiencia y maneja la subida de nivel."""
        self.exp_actual += cantidad
        subio_nivel = False
        while self.exp_actual >= self.exp_necesaria:
            self.exp_actual -= self.exp_necesaria
            self.nivel += 1
            self.exp_necesaria = int(self.exp_necesaria * 1.5)
            self.hp_max += 20
            self.hp_actual = self.hp_max
            self.daño_base += 2
            subio_nivel = True
        return subio_nivel

    def equipar(self, item):
        """Equipa un objeto en la ranura correspondiente."""
        if item.tipo in self.equipamiento:
            self.equipamiento[item.tipo] = item

    # =========================================================
    # CÁLCULO DINÁMICO DE ESTADÍSTICAS (Base + Equipamiento)
    # =========================================================
    def obtener_daño_total(self):
        daño = self.daño_base
        arma = self.equipamiento.get("Arma")
        if arma:
            daño += arma.stats.get("daño", 0)
        return daño

    def obtener_evasion_total(self):
        evasion = self.evasion_base
        for item in self.equipamiento.values():
            if item is not None:
                evasion += item.stats.get("evasion", 0)
        # Ponemos un tope máximo del 75% para que el jugador no sea inmortal
        return min(evasion, 75)

    def obtener_robo_vida_total(self):
        robo = self.robo_vida_base
        for item in self.equipamiento.values():
            if item is not None:
                robo += item.stats.get("robo_vida", 0.0)
        return robo

    def obtener_bono_velocidad(self):
        bono = self.vel_ataque_base
        for item in self.equipamiento.values():
            if item is not None:
                bono += item.stats.get("vel_ataque", 0)
        return bono


class Enemy:
    def __init__(
        self, nombre: str, hp: int, daño: int, exp_recompensa: int, oro_recompensa: int
    ):
        self.nombre = nombre
        self.hp_max = hp
        self.hp_actual = hp
        self.daño = daño
        self.exp_recompensa = exp_recompensa
        self.oro_recompensa = oro_recompensa

    def recibir_daño(self, cantidad: int):
        self.hp_actual = max(0, self.hp_actual - cantidad)
        print(
            f"💥 ¡Zasca! {self.nombre} recibe {cantidad} de daño. (HP: {self.hp_actual}/{self.hp_max})"
        )

    def esta_vivo(self) -> bool:
        return self.hp_actual > 0
