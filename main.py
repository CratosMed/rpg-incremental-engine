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
from asset_manager import AssetManager  # Nuestro nuevo gestor dinámico de imágenes

# =====================================================================
# INICIALIZACIÓN DE PYGAME Y PANTALLA
# =====================================================================
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("RPG Profesional - Motor Data-Driven")

# Fuentes globales
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


# =====================================================================
# NÚCLEO PRINCIPAL (MAIN LOOP)
# =====================================================================
async def main():
    # --- 1. CARGA DE PARTIDA ---
    heroe = cargar_partida()
    if heroe is None:
        heroe = Player("Guerrero")
        heroe.equipar(Item("Espada Oxidada", "Común", 5, "Arma", {"daño": 5}))

    # --- 2. VARIABLES DE ESTADO Y PROGRESIÓN ---
    cd_heroe = COOLDOWN_HEROE
    enemigos_derrotados = 0
    nivel_oleada = 1
    es_jefe_actual = False

    # --- 3. CONTROL MACRO DE ZONAS (BIOMAS) ---
    clave_zona_actual = "zona_1"
    datos_zona_actual = db.zones_db.get(clave_zona_actual, {})
    jefe_derrotados_en_zona = 0
    fondo = cargar_fondo(datos_zona_actual.get("fondo_path", ""))

    def generar_enemigo(es_jefe=False):
        """Genera un enemigo leyendo la base de datos JSON y le asigna su ruta de sprites."""
        zona_db_id = datos_zona_actual.get("id", "zona_1_bosque")
        datos_zona_enemigos = db.enemies_db.get(zona_db_id, {})

        lista_enemigos = (
            datos_zona_enemigos.get("jefes", [])
            if es_jefe
            else datos_zona_enemigos.get("comunes", [])
        )

        if not lista_enemigos:
            # Fallback en caso de JSON vacío o mal configurado
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
        # Inyectamos la ruta de la carpeta de imágenes que dicta el JSON
        enemigo_obj.sprite_folder = datos.get("sprite_folder", "")
        return enemigo_obj

    # --- 4. INICIALIZACIÓN DE GESTORES (MANAGERS) ---
    enemigo_actual = generar_enemigo(es_jefe_actual)
    vfx = VisualEffectsManager()
    audio = SoundManager()
    assets = AssetManager()  # Instanciamos la caché de imágenes

    # Cargamos dinámicamente los gráficos iniciales
    frames_h = assets.cargar_heroe()
    frames_g = assets.obtener_frames_enemigo(enemigo_actual.sprite_folder)

    # Variables de control de bucle y tiempo
    t_ataque_h, t_ataque_e = 0, 0
    f_g, f_h = 0, 0
    t_anim = 0
    running, in_inventory = True, False
    mensaje_accion, mensaje_botin = "¡Combate!", ""

    # =================================================================
    # GAME LOOP PRINCIPAL
    # =================================================================
    while running:
        tiempo_actual = pygame.time.get_ticks()

        # --- A. ACTUALIZACIÓN DE ANIMACIONES ---
        if tiempo_actual - t_anim > VEL_ANIMACION:
            # Usamos len() para evitar desbordamientos si una carpeta tiene más o menos frames
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
                if event.key == pygame.K_s and not in_inventory:
                    guardar_partida(heroe)
                    mensaje_accion = "¡Partida Guardada!"

                if event.key == pygame.K_i:
                    in_inventory = not in_inventory

                # LÓGICA DE INVENTARIO
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
                            if pygame.key.get_mods() & pygame.KMOD_SHIFT:  # Equipar
                                item = heroe.inventario.pop(idx)
                                actual = heroe.equipamiento.get(item.tipo)
                                if actual:
                                    heroe.inventario.append(actual)
                                heroe.equipamiento[item.tipo] = item
                            else:  # Vender
                                heroe.oro += heroe.inventario.pop(idx).valor_base

                    elif event.key == pygame.K_h:  # Herrería
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

        # --- C. LÓGICA DE COMBATE AUTOMÁTICO ---
        if not in_inventory:
            # 1. Calculamos la VELOCIDAD DE ATAQUE dinámica
            # Restamos el bono al cooldown base. El 'max(200, ...)' evita que el héroe ataque a la velocidad de la luz y rompa el juego.
            cd_actual_heroe = max(200, cd_heroe - heroe.obtener_bono_velocidad())

            # Turno de Ataque del Héroe
            if tiempo_actual - t_ataque_h > cd_actual_heroe:
                dmg = heroe.obtener_daño_total()

                if random.randint(1, 100) <= heroe.crit_chance:
                    dmg *= 2
                    mensaje_accion = "¡GOLPE CRÍTICO!"
                    audio.play("critico")
                else:
                    audio.play("ataque_heroe")

                # Aplicamos daño al enemigo
                enemigo_actual.recibir_daño(dmg)
                vfx.añadir_daño(550, 80, dmg, "enemigo")

                # 2. Aplicamos ROBO DE VIDA
                robo = heroe.obtener_robo_vida_total()
                if robo > 0:
                    cura = int(dmg * robo)
                    if cura > 0:
                        # Curamos sin pasarnos de la vida máxima
                        heroe.hp_actual = min(heroe.hp_max, heroe.hp_actual + cura)
                        # Reutilizamos los números flotantes para mostrar la curación
                        vfx.añadir_daño(100, 80, cura, "heroe")

                t_ataque_h = tiempo_actual

                # --- RESOLUCIÓN TRAS MUERTE DEL ENEMIGO ---
                if not enemigo_actual.esta_vivo():
                    heroe.oro += enemigo_actual.oro_recompensa
                    if heroe.ganar_exp(enemigo_actual.exp_recompensa):
                        heroe.puntos_talento += 1
                        audio.play("nivel_up")

                    if random.randint(1, 100) <= CHANCE_DROP_ITEM:
                        nuevo_botin = generar_arma_aleatoria()
                        heroe.inventario.append(nuevo_botin)
                        mensaje_botin = f"Botín: {nuevo_botin.nombre}"
                        audio.play("botin")

                    # Gestión de Zonas y Oleadas
                    enemigos_derrotados += 1

                    if es_jefe_actual:
                        jefe_derrotados_en_zona += 1
                        jefes_requeridos = datos_zona_actual.get(
                            "jefes_para_avanzar", 5
                        )

                        # Transición de Bioma
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

                    # Generamos el siguiente enemigo y leemos sus gráficos dinámicamente
                    es_jefe_actual = enemigos_derrotados % ENEMIGOS_PARA_JEFE == 0
                    enemigo_actual = generar_enemigo(es_jefe_actual)

                    frames_g = assets.obtener_frames_enemigo(
                        enemigo_actual.sprite_folder
                    )
                    f_g = 0  # Reiniciamos la animación del nuevo enemigo

            # Turno de Ataque del Enemigo
            elif tiempo_actual - t_ataque_e > COOLDOWN_ENEMIGO:
                # 3. Aplicamos EVASIÓN
                probabilidad_esquivar = heroe.obtener_evasion_total()

                # Tirada de dados de 1 a 100
                if random.randint(1, 100) <= probabilidad_esquivar:
                    mensaje_accion = "¡ESQUIVADO!"
                else:
                    heroe.hp_actual -= enemigo_actual.daño
                    vfx.añadir_daño(100, 80, enemigo_actual.daño, "heroe")
                    audio.play("recibir_daño")

                t_ataque_e = tiempo_actual
        # --- D. RENDERIZADO (DIBUJO EN PANTALLA) ---
        screen.blit(fondo, (0, 0))

        # Dibujo de Sprites (Solo si hay frames válidos cargados)
        if vfx.flash_heroe % 2 == 0 and frames_h:
            screen.blit(frames_h[f_h], (50, 50))
        if vfx.flash_enemigo % 2 == 0 and frames_g:
            screen.blit(frames_g[f_g], (500, 50))

        # Cooldown Visual
        cd_actual_heroe = max(200, cd_heroe - heroe.obtener_bono_velocidad())
        prog_h = min(1.0, (tiempo_actual - t_ataque_h) / cd_actual_heroe)
        pygame.draw.rect(screen, GOLD, (50, 40, int(150 * prog_h), 5))

        prog_e = min(1.0, (tiempo_actual - t_ataque_e) / COOLDOWN_ENEMIGO)
        pygame.draw.rect(screen, RED, (500, 40, int(150 * prog_e), 5))

        # Textos Superiores
        screen.blit(
            font_normal.render(f"{heroe.nombre} (Nv. {heroe.nivel})", True, WHITE),
            (50, 170),
        )
        screen.blit(
            font_normal.render(f"{enemigo_actual.nombre}", True, WHITE), (500, 170)
        )

        # Barras de Vida
        dibujar_barra_vida(screen, 50, 200, heroe.hp_actual, heroe.hp_max, font_pequena)
        dibujar_barra_vida(
            screen,
            500,
            200,
            enemigo_actual.hp_actual,
            enemigo_actual.hp_max,
            font_pequena,
        )

        vfx.update_y_draw(screen)

        # Textos Inferiores (Oro, EXP, Zonas)
        screen.blit(font_normal.render(f"Oro: {heroe.oro}", True, GOLD), (50, 240))
        screen.blit(
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
        screen.blit(txt_zona, (WIDTH - txt_zona.get_width() - 20, 20))

        screen.blit(
            font_normal.render(mensaje_accion, True, WHITE), (WIDTH // 2 - 100, 450)
        )
        if mensaje_botin:
            color_b = GOLD if "ÉPICO" in mensaje_botin else WHITE
            screen.blit(
                font_normal.render(mensaje_botin, True, color_b),
                (WIDTH // 2 - 100, 490),
            )

        # --- E. RENDERIZADO DEL INVENTARIO (OVERLAY) ---
        if in_inventory:
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(220)
            overlay.fill(BLACK)
            screen.blit(overlay, (0, 0))

            screen.blit(
                font_grande.render("MOCHILA Y PROGRESIÓN", True, GOLD),
                (WIDTH // 2 - 200, 50),
            )
            screen.blit(
                font_normal.render(
                    "Presiona [1-9] Vender | [SHIFT]+[1-9] Equipar",
                    True,
                    (150, 150, 150),
                ),
                (100, 110),
            )

            y_off = 160
            if len(heroe.inventario) == 0:
                screen.blit(
                    font_normal.render("Mochila vacía.", True, (100, 100, 100)),
                    (100, y_off),
                )
            for i, item in enumerate(heroe.inventario[:9]):
                color_r = (
                    GOLD
                    if item.rareza == "Raro"
                    else BLUE_INFO if item.rareza == "Mágico" else WHITE
                )
                txt = font_normal.render(
                    f"{i+1}. {item.nombre} ({item.valor_base} Oro)", True, color_r
                )
                screen.blit(txt, (100, y_off))
                y_off += 40

            # Herrería
            pygame.draw.rect(screen, GRAY_UI, (450, 150, 320, 220))
            pygame.draw.rect(screen, WHITE, (450, 150, 320, 220), 2)
            screen.blit(font_normal.render("HERRERÍA", True, GOLD), (550, 170))

            arma = heroe.equipamiento.get("Arma")
            if arma:
                screen.blit(
                    font_normal.render(
                        f"Eq: {arma.nombre} (+{arma.nivel_mejora})", True, WHITE
                    ),
                    (465, 210),
                )
                screen.blit(
                    font_normal.render(
                        f"Daño actual: {arma.stats.get('daño', 0)}", True, GREEN
                    ),
                    (465, 250),
                )
                costo = 100 + (arma.nivel_mejora * 50)
                color_c = GOLD if heroe.oro >= costo else RED
                screen.blit(
                    font_normal.render(f"Mejorar: {costo} Oro [H]", True, color_c),
                    (465, 300),
                )
            else:
                screen.blit(
                    font_normal.render("Sin arma equipada.", True, RED), (465, 220)
                )

            # Talentos
            pygame.draw.rect(screen, (20, 20, 40), (450, 390, 320, 150))
            pygame.draw.rect(screen, BLUE_INFO, (450, 390, 320, 150), 2)

            color_t = GOLD if heroe.puntos_talento > 0 else (100, 100, 100)
            screen.blit(
                font_normal.render(
                    f"PUNTOS DE TALENTO: {heroe.puntos_talento}", True, color_t
                ),
                (465, 410),
            )

            if heroe.puntos_talento > 0:
                screen.blit(
                    font_normal.render("[F] +5% Daño Crítico", True, WHITE), (465, 450)
                )
                screen.blit(
                    font_normal.render("[G] +10% Vel. Ataque", True, WHITE), (465, 490)
                )
            else:
                screen.blit(
                    font_normal.render(
                        "Sube de nivel para ganar puntos", True, (120, 120, 120)
                    ),
                    (465, 460),
                )

        pygame.display.flip()
        await asyncio.sleep(0)  # Necesario para compatibilidad web futura con Pygbag

    pygame.quit()


if __name__ == "__main__":
    asyncio.run(main())
