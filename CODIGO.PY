"""
================================================================
  JUEGO DE MEMORIA (parejas de cartas)
  Versión sencilla con interfaz gráfica usando Tkinter.
================================================================
"""
 
import tkinter as tk
from tkinter import messagebox
import random
import json
import os
 
ARCHIVO_ESTADISTICAS = "estadisticas_memoria.json"
 
# Temáticas disponibles: cada una necesita al menos 32 símbolos distintos
# (para poder armar el nivel Difícil de 8x8 = 32 parejas)
TEMATICAS = {
    "Animales": ["🐶", "🐱", "🐵", "🦁", "🐸", "🐷", "🐮", "🐰", "🐔", "🦊",
                 "🐻", "🐼", "🐨", "🐯", "🐺", "🐙", "🐢", "🦋", "🐝", "🐞",
                 "🦉", "🦖", "🐬", "🐳", "🦒", "🐘", "🦓", "🐫", "🦔", "🐊",
                 "🦚", "🦩"],
    "Frutas": ["🍎", "🍌", "🍇", "🍓", "🍍", "🍉", "🍒", "🍑", "🍋", "🥝",
               "🍈", "🍐", "🍊", "🥭", "🍏", "🥥", "🫐", "🍅", "🥕", "🌽",
               "🍆", "🥑", "🫒", "🍄", "🌶️", "🧄", "🧅", "🥔", "🍠", "🫑",
               "🥦", "🥬"],
    "Espacio": ["🚀", "🛰️", "🌎", "🌙", "⭐", "☄️", "🪐", "👽", "🌞", "🌟",
                "🌌", "🛸", "🌠", "🌑", "🌓", "🌔", "🌕", "🌖", "🌗", "🌘",
                "🔭", "🧑‍🚀", "🌍", "🌏", "💫", "✨", "🌈", "⚡", "🔥", "❄️",
                "🌪️", "🌊"],
}
 
# Nivel: tamaño del tablero y tiempo límite en segundos (None = sin límite)
NIVELES = {
    "Fácil (4x4)": {"filas": 4, "columnas": 4, "tiempo": None},
    "Medio (6x6)": {"filas": 6, "columnas": 6, "tiempo": 180},
    "Difícil (8x8)": {"filas": 8, "columnas": 8, "tiempo": 300},
}
 
 
def cargar_estadisticas():
    """Lee las estadísticas guardadas, o valores en cero si es la primera vez."""
    if os.path.exists(ARCHIVO_ESTADISTICAS):
        with open(ARCHIVO_ESTADISTICAS, "r", encoding="utf-8") as archivo:
            return json.load(archivo)
    return {
        "partidas_jugadas": 0,
        "partidas_ganadas": 0,
        "mejor_puntuacion": 0,
        "menos_movimientos": None,
    }
 
 
def guardar_estadisticas(estadisticas):
    with open(ARCHIVO_ESTADISTICAS, "w", encoding="utf-8") as archivo:
        json.dump(estadisticas, archivo, ensure_ascii=False, indent=2)
 
 
# ------------------ CLASE: JuegoMemoria ------------------
class JuegoMemoria:
    """Controla una partida: genera el tablero y maneja cada turno."""
 
    def __init__(self, ventana, volver_al_menu, nivel, tematica):
        self.ventana = ventana
        self.volver_al_menu = volver_al_menu
        self.filas = NIVELES[nivel]["filas"]
        self.columnas = NIVELES[nivel]["columnas"]
        self.tiempo_restante = NIVELES[nivel]["tiempo"]
 
        self.simbolos = self._generar_simbolos(tematica)
        self.botones = []
        self.reveladas = []        # índices de las cartas volteadas en el turno actual
        self.encontradas = set()   # índices ya emparejados (permanecen visibles)
        self.movimientos = 0
        self.puntuacion = 0
        self.vidas = 5
        self.bloqueado = False     # evita clics mientras se procesa una jugada
 
        self.frame = tk.Frame(ventana)
        self.frame.pack(padx=10, pady=10)
 
        self._crear_encabezado()
        self._crear_tablero()
 
        # Requisito: mostrar todas las cartas 5 segundos al iniciar la partida
        self._voltear_todas(mostrar=True)
        self.ventana.after(5000, lambda: self._voltear_todas(mostrar=False))
 
        if self.tiempo_restante is not None:
            self._actualizar_temporizador()
 
    # ---------- Preparación del tablero ----------
    def _generar_simbolos(self, tematica):
        total_parejas = (self.filas * self.columnas) // 2
        disponibles = TEMATICAS[tematica]
        elegidos = random.sample(disponibles, total_parejas)
        simbolos = elegidos * 2
        random.shuffle(simbolos)
        return simbolos
 
    def _crear_encabezado(self):
        info = tk.Frame(self.frame)
        info.pack(pady=(0, 10))
 
        self.label_puntuacion = tk.Label(info, text="Puntos: 0", font=("Arial", 11, "bold"))
        self.label_puntuacion.grid(row=0, column=0, padx=8)
 
        self.label_movimientos = tk.Label(info, text="Movimientos: 0", font=("Arial", 11))
        self.label_movimientos.grid(row=0, column=1, padx=8)
 
        self.label_vidas = tk.Label(info, text="Vidas: 5", font=("Arial", 11))
        self.label_vidas.grid(row=0, column=2, padx=8)
 
        self.label_tiempo = tk.Label(info, text="", font=("Arial", 11))
        self.label_tiempo.grid(row=0, column=3, padx=8)
 
    def _crear_tablero(self):
        tablero = tk.Frame(self.frame)
        tablero.pack()
 
        for indice in range(self.filas * self.columnas):
            boton = tk.Button(
                tablero, text="❓", width=3, height=1, font=("Arial", 16),
                command=lambda i=indice: self._click_carta(i),
            )
            fila, columna = divmod(indice, self.columnas)
            boton.grid(row=fila, column=columna, padx=2, pady=2)
            self.botones.append(boton)
 
    def _voltear_todas(self, mostrar):
        for i, boton in enumerate(self.botones):
            if i in self.encontradas:
                continue
            boton.config(text=self.simbolos[i] if mostrar else "❓")
 
    # ---------- Turnos de juego ----------
    def _click_carta(self, indice):
        if self.bloqueado or indice in self.encontradas or indice in self.reveladas:
            return  # clic inválido: ya está descubierta o el juego está procesando
 
        self.botones[indice].config(text=self.simbolos[indice])
        self.reveladas.append(indice)
 
        if len(self.reveladas) == 2:
            self.movimientos += 1
            self.label_movimientos.config(text=f"Movimientos: {self.movimientos}")
            self.bloqueado = True
            # Pequeña pausa para que el jugador alcance a ver la segunda carta
            self.ventana.after(700, self._revisar_pareja)
 
    def _revisar_pareja(self):
        i, j = self.reveladas
 
        if self.simbolos[i] == self.simbolos[j]:
            self.encontradas.update([i, j])
            self.puntuacion += 100
            self.botones[i].config(state="disabled")
            self.botones[j].config(state="disabled")
        else:
            self.puntuacion = max(0, self.puntuacion - 10)
            self.botones[i].config(text="❓")
            self.botones[j].config(text="❓")
            self.vidas -= 1
            self.label_vidas.config(text=f"Vidas: {self.vidas}")
 
        self.label_puntuacion.config(text=f"Puntos: {self.puntuacion}")
        self.reveladas = []
        self.bloqueado = False
 
        if len(self.encontradas) == len(self.simbolos):
            self._fin_partida(gano=True)
        elif self.vidas <= 0:
            self._fin_partida(gano=False)
 
    def _actualizar_temporizador(self):
        minutos, segundos = divmod(self.tiempo_restante, 60)
        self.label_tiempo.config(text=f"Tiempo: {minutos:02d}:{segundos:02d}")
 
        if self.tiempo_restante <= 0:
            self._fin_partida(gano=False)
            return
 
        self.tiempo_restante -= 1
        self.ventana.after(1000, self._actualizar_temporizador)
 
    # ---------- Fin de partida ----------
    def _fin_partida(self, gano):
        self.bloqueado = True
        for boton in self.botones:
            boton.config(state="disabled")
 
        estadisticas = cargar_estadisticas()
        estadisticas["partidas_jugadas"] += 1
        if gano:
            estadisticas["partidas_ganadas"] += 1
            estadisticas["mejor_puntuacion"] = max(estadisticas["mejor_puntuacion"], self.puntuacion)
            if estadisticas["menos_movimientos"] is None or self.movimientos < estadisticas["menos_movimientos"]:
                estadisticas["menos_movimientos"] = self.movimientos
        guardar_estadisticas(estadisticas)
 
        titulo = "🎉 ¡GANASTE!" if gano else "💀 Fin de la partida"
        messagebox.showinfo(
            titulo,
            f"Puntuación final: {self.puntuacion}\nMovimientos: {self.movimientos}",
        )
 
        self.frame.destroy()
        self.volver_al_menu()
 
 
# ------------------ CLASE: Aplicacion (menús y navegación) ------------------
class Aplicacion:
    """Ventana principal: muestra el menú y cambia entre pantallas."""
 
    def __init__(self):
        self.ventana = tk.Tk()
        self.ventana.title("Juego de Memoria")
        self.mostrar_menu_principal()
        self.ventana.mainloop()
 
    def _limpiar_ventana(self):
        for widget in self.ventana.winfo_children():
            widget.destroy()
 
    def mostrar_menu_principal(self):
        self._limpiar_ventana()
        tk.Label(self.ventana, text="🎮 JUEGO DE MEMORIA", font=("Arial", 20, "bold")).pack(pady=30)
        tk.Button(self.ventana, text="Jugar", width=20, font=("Arial", 12),
                  command=self.mostrar_seleccion_nivel).pack(pady=8)
        tk.Button(self.ventana, text="Estadísticas", width=20, font=("Arial", 12),
                  command=self.mostrar_estadisticas).pack(pady=8)
        tk.Button(self.ventana, text="Salir", width=20, font=("Arial", 12),
                  command=self.ventana.destroy).pack(pady=8)
 
    def mostrar_seleccion_nivel(self):
        self._limpiar_ventana()
        tk.Label(self.ventana, text="Elige un nivel", font=("Arial", 16, "bold")).pack(pady=20)
        for nivel in NIVELES:
            tk.Button(self.ventana, text=nivel, width=20, font=("Arial", 12),
                      command=lambda n=nivel: self.mostrar_seleccion_tematica(n)).pack(pady=6)
        tk.Button(self.ventana, text="Volver", command=self.mostrar_menu_principal).pack(pady=20)
 
    def mostrar_seleccion_tematica(self, nivel):
        self._limpiar_ventana()
        tk.Label(self.ventana, text="Elige una temática", font=("Arial", 16, "bold")).pack(pady=20)
        for tematica in TEMATICAS:
            tk.Button(self.ventana, text=tematica, width=20, font=("Arial", 12),
                      command=lambda t=tematica: self.iniciar_juego(nivel, t)).pack(pady=6)
        tk.Button(self.ventana, text="Volver", command=self.mostrar_seleccion_nivel).pack(pady=20)
 
    def iniciar_juego(self, nivel, tematica):
        self._limpiar_ventana()
        JuegoMemoria(self.ventana, self.mostrar_menu_principal, nivel, tematica)
 
    def mostrar_estadisticas(self):
        self._limpiar_ventana()
        estadisticas = cargar_estadisticas()
 
        tk.Label(self.ventana, text="📊 Estadísticas", font=("Arial", 16, "bold")).pack(pady=20)
        tk.Label(self.ventana, text=f"Partidas jugadas: {estadisticas['partidas_jugadas']}",
                 font=("Arial", 12)).pack(pady=4)
        tk.Label(self.ventana, text=f"Partidas ganadas: {estadisticas['partidas_ganadas']}",
                 font=("Arial", 12)).pack(pady=4)
        tk.Label(self.ventana, text=f"Mejor puntuación: {estadisticas['mejor_puntuacion']}",
                 font=("Arial", 12)).pack(pady=4)
        movimientos_minimos = estadisticas["menos_movimientos"] or "—"
        tk.Label(self.ventana, text=f"Movimientos mínimos: {movimientos_minimos}",
                 font=("Arial", 12)).pack(pady=4)
 
        tk.Button(self.ventana, text="Volver", command=self.mostrar_menu_principal).pack(pady=20)
 
 
if __name__ == "__main__":
    Aplicacion()
 