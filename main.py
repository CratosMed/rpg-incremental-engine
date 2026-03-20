import pygame
import sys
import random
import asyncio

# =====================================================================
# IMPORTACIÓN DE MÓDULOS DEL MOTOR (ARQUITECTURA MODULAR)
# =====================================================================
from constants import *
from ui_effects import VisualEffectsManager
from clases import Player, Enemy, Item
from loot import generar_arma_aleatoria
from save_system import guardar_partida, cargar_partida
from sound_manager import SoundManager
from data_manager import db
from asset_manager import AssetManager
from ui_renderer import UIRenderer  # --- NUESTRO NUEVO MOTOR GRÁFICO ---

# =====================================================================
# INICIALIZACIÓN DE PYGAME Y PANTALLA
# =====================================================================
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("RPG Profesional - Motor Data-Driven")


def cargar_fondo(ruta):
    """Intenta cargar el fondo de la zona dinámicamente. Si falla, pone un fondo negro seguro."""
    try:
        if ruta:
            img = pygame.image.load(ruta).convert()
            return pygame.transform.scale(img, (WIDTH, HEIGHT))
    except Exception as e:
        print(f"⚠️ Error cargando fondo {ruta}: {e}")

    bg = pygame.Surface((WIDTH, HEIGHT))
    bg.fill(BLACK)
    return bg


def generar_gema_aleatoria():
    """Selecciona una gema aleatoria de la base de datos y crea el objeto Item."""
    lista_gemas = db.items_db.get("gemas", [])
    if not lista_gemas:
        return Item("Roca Inútil", "Común", 1, "Basura", {})

    gema_data = random.choice(lista_gemas)

    stats_gema = {}
    for clave, valor in gema_data.items():
        if clave not in ["id", "nombre", "tipo", "valor"]:
            stats_gema[clave] = valor

    return Item(
        nombre=gema_data["nombre"],
        rareza="Mágico",
        valor_base=gema_data.get("valor", 50),
        tipo="Gema",
        stats=stats_gema,
    )


def refrescar_tienda():
    """Genera 5 objetos aleatorios para el inventario del comerciante."""
    items = []
    for _ in range(5):
        if random.randint(1, 100) <= 20:
            items.append(generar_gema_aleatoria())
        else:
            items.append(generar_arma_aleatoria())
    return items


# =====================================================================
# NÚCLEO PRINCIPAL (MAIN LOOP)
# =====================================================================
async def main():
    # --- 1. CARGA DE PARTIDA ---
    heroe = cargar_partida()
    if heroe is None:
        heroe = Player("Guerrero")
        heroe.equipar(
            Item("Espada Oxidada", "Común", 5, "Arma", {"daño": 5, "sockets": 1})
        )

    # --- 2. VARIABLES DE ESTADO Y PROGRESIÓN ---
    cd_heroe = COOLDOWN_HEROE
    enemigos_derrotados = 0
    nivel_oleada = 1
    es_jefe_actual = False

    # Estados de la UI
    running, in_inventory, in_shop = True, False, False
    inventario_tienda = refrescar_tienda()

    # --- 3. CONTROL MACRO DE ZONAS (BIOMAS) ---
    clave_zona_actual = "zona_1"
    datos_zona_actual = db.zones_db.get(clave_zona_actual, {})
    jefe_derrotados_en_zona = 0
    fondo = cargar_fondo(datos_zona_actual.get("fondo_path", ""))

    def generar_enemigo(es_jefe=False):
        zona_db_id = datos_zona_actual.get("id", "zona_1_bosque")
        datos_zona_enemigos = db.enemies_db.get(zona_db_id, {})

        lista_enemigos = (
            datos_zona_enemigos.get("jefes", [])
            if es_jefe
            else datos_zona_enemigos.get("comunes", [])
        )

        if not lista_enemigos:
            enemigo_obj = Enemy("Error del Sistema", 10, 1, 1, 1)
            enemigo_obj.sprite_folder = ""
            return enemigo_obj

        datos = random.choice(lista_enemigos)
        multi = nivel_oleada
        nombre = f"{datos['nombre']} (JEFE)" if es_jefe else datos["nombre"]

        enemigo_obj = Enemy(
            nombre,
            int(datos["hp_base"] * multi),
            int(datos["daño_base"] * multi),
            datos["exp"] * nivel_oleada,
            datos["oro"] * nivel_oleada,
        )
        enemigo_obj.sprite_folder = datos.get("sprite_folder", "")
        return enemigo_obj

    # --- 4. INICIALIZACIÓN DE GESTORES (MANAGERS) ---
    enemigo_actual = generar_enemigo(es_jefe_actual)
    vfx = VisualEffectsManager()
    audio = SoundManager()
    assets = AssetManager()
    ui = UIRenderer(screen)  # Inicializamos nuestro nuevo renderer

    frames_h = assets.cargar_heroe()
    frames_g = assets.obtener_frames_enemigo(enemigo_actual.sprite_folder)

    t_ataque_h, t_ataque_e = 0, 0
    f_g, f_h = 0, 0
    t_anim = 0
    mensaje_accion, mensaje_botin = "¡Combate!", ""

    # =================================================================
    # GAME LOOP PRINCIPAL
    # =================================================================
    while running:
        tiempo_actual = pygame.time.get_ticks()

        # --- A. ACTUALIZACIÓN DE ANIMACIONES ---
        if tiempo_actual - t_anim > VEL_ANIMACION:
            if frames_g:
                f_g = (f_g + 1) % len(frames_g)
            if frames_h:
                f_h = (f_h + 1) % len(frames_h)
            t_anim = tiempo_actual

        # --- B. GESTIÓN DE EVENTOS (INPUT) ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                guardar_partida(heroe)
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_s and not in_inventory and not in_shop:
                    guardar_partida(heroe)
                    mensaje_accion = "¡Partida Guardada!"

                if event.key == pygame.K_i:
                    in_inventory = not in_inventory
                    if in_inventory:
                        in_shop = False

                if event.key == pygame.K_c:
                    in_shop = not in_shop
                    if in_shop:
                        in_inventory = False

                # --- LÓGICA DE INVENTARIO ---
                if in_inventory:
                    if heroe.puntos_talento > 0:
                        if event.key == pygame.K_f:
                            heroe.crit_chance += 5
                            heroe.puntos_talento -= 1
                        elif event.key == pygame.K_g:
                            cd_heroe = int(cd_heroe * 0.9)
                            heroe.puntos_talento -= 1

                    if pygame.K_1 <= event.key <= pygame.K_9:
                        idx = event.key - pygame.K_1
                        if idx < len(heroe.inventario):
                            if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                                item_seleccionado = heroe.inventario[idx]
                                if item_seleccionado.tipo == "Gema":
                                    arma = heroe.equipamiento.get("Arma")
                                    if arma:
                                        if len(arma.gemas_equipadas) < arma.sockets:
                                            gema_a_equipar = heroe.inventario.pop(idx)
                                            arma.gemas_equipadas.append(gema_a_equipar)
                                            mensaje_accion = (
                                                f"¡{gema_a_equipar.nombre} engarzada!"
                                            )
                                            audio.play("equipar")
                                        else:
                                            mensaje_accion = "Arma sin huecos libres."
                                    else:
                                        mensaje_accion = "Equipa un arma primero."
                                else:
                                    item = heroe.inventario.pop(idx)
                                    actual = heroe.equipamiento.get(item.tipo)
                                    if actual:
                                        heroe.inventario.append(actual)
                                    heroe.equipamiento[item.tipo] = item
                                    mensaje_accion = f"¡{item.nombre} equipado!"
                            else:
                                item_vendido = heroe.inventario.pop(idx)
                                heroe.oro += item_vendido.valor_base
                                mensaje_accion = (
                                    f"Vendido: +{item_vendido.valor_base} oro"
                                )

                    elif event.key == pygame.K_h:
                        arma = heroe.equipamiento.get("Arma")
                        if arma:
                            costo = 100 + (arma.nivel_mejora * 50)
                            if heroe.oro >= costo:
                                heroe.oro -= costo
                                if random.randint(1, 100) <= PROB_EXITO_HERRERIA:
                                    arma.nivel_mejora += 1
                                    arma.stats["daño"] = (
                                        int(arma.stats["daño"] * 1.2) + 2
                                    )
                                    mensaje_accion = "¡Mejora Exitosa!"
                                else:
                                    mensaje_accion = "Falló la mejora..."

                # --- LÓGICA DE LA TIENDA ---
                if in_shop:
                    if pygame.K_1 <= event.key <= pygame.K_5:
                        idx = event.key - pygame.K_1
                        if idx < len(inventario_tienda):
                            item_compra = inventario_tienda[idx]
                            precio = item_compra.valor_base * 3

                            if heroe.oro >= precio:
                                if len(heroe.inventario) < 9:
                                    heroe.oro -= precio
                                    heroe.inventario.append(inventario_tienda.pop(idx))
                                    mensaje_accion = (
                                        f"¡Compraste: {item_compra.nombre}!"
                                    )
                                    audio.play("botin")
                                else:
                                    mensaje_accion = "Tu mochila está llena."
                            else:
                                mensaje_accion = "No tienes suficiente oro."

                    elif event.key == pygame.K_r:
                        costo_refresh = 50
                        if heroe.oro >= costo_refresh:
                            heroe.oro -= costo_refresh
                            inventario_tienda = refrescar_tienda()
                            mensaje_accion = "¡El comerciante trajo nueva mercancía!"
                        else:
                            mensaje_accion = "Necesitas 50 de oro para refrescar."
            # --- NUEVO: CONTROLES CON EL RATÓN ---
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 1 significa "Clic Izquierdo"
                    mx, my = pygame.mouse.get_pos()  # Obtenemos coordenadas (X, Y)

                    # 1. CLICS EN EL INVENTARIO
                    if in_inventory:
                        # Detectar clic en la lista de objetos (x: 100 a 400, y: empieza en 160)
                        if 100 <= mx <= 400 and 160 <= my < 160 + (
                            len(heroe.inventario) * 40
                        ):
                            # Matemáticas mágicas para saber qué índice tocamos
                            idx = (my - 160) // 40

                            # Si mantenemos SHIFT mientras hacemos clic: Equipar/Engarzar
                            if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                                item_seleccionado = heroe.inventario[idx]
                                if item_seleccionado.tipo == "Gema":
                                    arma = heroe.equipamiento.get("Arma")
                                    if (
                                        arma
                                        and len(arma.gemas_equipadas) < arma.sockets
                                    ):
                                        gema = heroe.inventario.pop(idx)
                                        arma.gemas_equipadas.append(gema)
                                        mensaje_accion = f"¡{gema.nombre} engarzada!"
                                        audio.play("equipar")
                                    else:
                                        mensaje_accion = (
                                            "Arma sin huecos o no equipada."
                                        )
                                else:
                                    item = heroe.inventario.pop(idx)
                                    actual = heroe.equipamiento.get(item.tipo)
                                    if actual:
                                        heroe.inventario.append(actual)
                                    heroe.equipamiento[item.tipo] = item
                                    mensaje_accion = f"¡{item.nombre} equipado!"

                            # Si hacemos un clic normal: Vender
                            else:
                                item_vendido = heroe.inventario.pop(idx)
                                heroe.oro += item_vendido.valor_base
                                mensaje_accion = (
                                    f"Vendido: +{item_vendido.valor_base} oro"
                                )

                        # Detectar clic en el botón "Mejorar" de la Herrería (x: 465-665, y: 310-340)
                        elif 465 <= mx <= 665 and 310 <= my <= 340:
                            arma = heroe.equipamiento.get("Arma")
                            if arma:
                                costo = 100 + (arma.nivel_mejora * 50)
                                if heroe.oro >= costo:
                                    heroe.oro -= costo
                                    if random.randint(1, 100) <= PROB_EXITO_HERRERIA:
                                        arma.nivel_mejora += 1
                                        arma.stats["daño"] = (
                                            int(arma.stats["daño"] * 1.2) + 2
                                        )
                                        mensaje_accion = "¡Mejora Exitosa!"
                                    else:
                                        mensaje_accion = "Falló la mejora..."
        # --- C. LÓGICA DE COMBATE AUTOMÁTICO ---
        if not in_inventory and not in_shop:
            cd_actual_heroe = max(200, cd_heroe - heroe.obtener_bono_velocidad())

            if tiempo_actual - t_ataque_h > cd_actual_heroe:
                dmg = heroe.obtener_daño_total()

                if random.randint(1, 100) <= heroe.crit_chance:
                    dmg *= 2
                    mensaje_accion = "¡GOLPE CRÍTICO!"
                    audio.play("critico")
                else:
                    audio.play("ataque_heroe")

                enemigo_actual.recibir_daño(dmg)
                vfx.añadir_daño(550, 80, dmg, "enemigo")

                robo = heroe.obtener_robo_vida_total()
                if robo > 0:
                    cura = int(dmg * robo)
                    if cura > 0:
                        heroe.hp_actual = min(heroe.hp_max, heroe.hp_actual + cura)
                        vfx.añadir_daño(100, 80, cura, "heroe")

                t_ataque_h = tiempo_actual

                if not enemigo_actual.esta_vivo():
                    heroe.oro += enemigo_actual.oro_recompensa
                    if heroe.ganar_exp(enemigo_actual.exp_recompensa):
                        heroe.puntos_talento += 1
                        audio.play("nivel_up")

                    if random.randint(1, 100) <= CHANCE_DROP_ITEM:
                        if random.randint(1, 100) <= 30:
                            nuevo_botin = generar_gema_aleatoria()
                            mensaje_botin = f"¡Gema encontrada!: {nuevo_botin.nombre}"
                        else:
                            nuevo_botin = generar_arma_aleatoria()
                            mensaje_botin = f"Botín: {nuevo_botin.nombre}"

                        heroe.inventario.append(nuevo_botin)
                        audio.play("botin")

                    enemigos_derrotados += 1

                    if es_jefe_actual:
                        jefe_derrotados_en_zona += 1
                        jefes_requeridos = datos_zona_actual.get(
                            "jefes_para_avanzar", 5
                        )

                        if jefe_derrotados_en_zona >= jefes_requeridos:
                            num_zona = int(clave_zona_actual.split("_")[1])
                            siguiente_clave = f"zona_{num_zona + 1}"

                            if siguiente_clave in db.zones_db:
                                clave_zona_actual = siguiente_clave
                                datos_zona_actual = db.zones_db[clave_zona_actual]
                                jefe_derrotados_en_zona = 0
                                fondo = cargar_fondo(
                                    datos_zona_actual.get("fondo_path", "")
                                )
                                mensaje_accion = f"¡AVANZAS A: {datos_zona_actual.get('nombre', 'NUEVA ZONA')}!"
                            else:
                                mensaje_accion = "¡HAS LIMPIADO TODO EL MUNDO!"
                        else:
                            mensaje_accion = f"¡Jefe derrotado! ({jefe_derrotados_en_zona}/{jefes_requeridos} para avanzar)"
                            nivel_oleada += 1
                    else:
                        es_jefe_siguiente = (
                            enemigos_derrotados % ENEMIGOS_PARA_JEFE == 0
                        )
                        mensaje_accion = (
                            "¡UN JEFE HA APARECIDO!"
                            if es_jefe_siguiente
                            else f"¡Derrotado! ({enemigos_derrotados % ENEMIGOS_PARA_JEFE}/{ENEMIGOS_PARA_JEFE})"
                        )

                    es_jefe_actual = enemigos_derrotados % ENEMIGOS_PARA_JEFE == 0
                    enemigo_actual = generar_enemigo(es_jefe_actual)
                    frames_g = assets.obtener_frames_enemigo(
                        enemigo_actual.sprite_folder
                    )
                    f_g = 0

            elif tiempo_actual - t_ataque_e > COOLDOWN_ENEMIGO:
                probabilidad_esquivar = heroe.obtener_evasion_total()
                if random.randint(1, 100) <= probabilidad_esquivar:
                    mensaje_accion = "¡ESQUIVADO!"
                else:
                    heroe.hp_actual -= enemigo_actual.daño
                    vfx.añadir_daño(100, 80, enemigo_actual.daño, "heroe")
                    audio.play("recibir_daño")

                t_ataque_e = tiempo_actual

        # --- D. RENDERIZADO (DIBUJO EN PANTALLA) ---
        screen.blit(fondo, (0, 0))

        if vfx.flash_heroe % 2 == 0 and frames_h:
            screen.blit(frames_h[f_h], (50, 50))
        if vfx.flash_enemigo % 2 == 0 and frames_g:
            screen.blit(frames_g[f_g], (500, 50))

        # El UIRenderer se encarga de dibujar todo el texto y las barras
        cd_actual_heroe = max(200, cd_heroe - heroe.obtener_bono_velocidad())
        ui.dibujar_hud_combate(
            heroe,
            enemigo_actual,
            cd_actual_heroe,
            COOLDOWN_ENEMIGO,
            tiempo_actual,
            t_ataque_h,
            t_ataque_e,
            datos_zona_actual,
            jefe_derrotados_en_zona,
            mensaje_accion,
            mensaje_botin,
        )

        vfx.update_y_draw(screen)

        # Superposiciones de Menús
        if in_inventory:
            ui.dibujar_inventario(heroe)
        elif in_shop:
            ui.dibujar_tienda(heroe, inventario_tienda)

        pygame.display.flip()
        await asyncio.sleep(0)

    pygame.quit()


if __name__ == "__main__":
    asyncio.run(main())
