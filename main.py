import customtkinter as ctk
from tkinter import messagebox
from collections import defaultdict
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import random

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


def is_connected(adj, vertices):
    if not vertices:
        return True

    start_vertex = next(iter(vertices))
    visited = set()
    stack = [start_vertex]

    while stack:
        v = stack.pop()
        if v not in visited:
            visited.add(v)
            stack.extend(adj[v] - visited)

    return len(visited) == len(vertices)


def find_triangles(edges):
    adj = defaultdict(set)
    vertices = set()

    for u, v in edges:
        adj[u].add(v)
        adj[v].add(u)
        vertices.add(u)
        vertices.add(v)

    connected = is_connected(adj, vertices)
    triangles = set()

    for u in adj:
        for v in adj[u]:
            if u < v:
                for w in adj[v]:
                    if v < w and u in adj[w]:
                        triangles.add((u, v, w))

    return list(triangles), connected


class TriangleFinderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Wyszukiwarka Trójkątów z Wizualizacją")
        self.geometry("1100x750")
        self.minsize(950, 650)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)

        self.current_edges = []
        self.current_triangles = []
        self.current_seed = 42

        self.layout_var = ctk.StringVar(value="Spring")
        self.show_labels_var = ctk.BooleanVar(value=True)

        self.left_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.left_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        self.lbl_title = ctk.CTkLabel(
            self.left_frame, text="Analiza Grafu",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.lbl_title.pack(pady=(0, 15))

        self.lbl_inst = ctk.CTkLabel(
            self.left_frame,
            text="Wprowadź krawędzie (np. '1 2'):",
            font=ctk.CTkFont(size=14)
        )
        self.lbl_inst.pack(pady=(0, 5))

        self.txt_edges = ctk.CTkTextbox(self.left_frame, height=150, font=ctk.CTkFont(family="Courier", size=14))
        self.txt_edges.pack(fill=ctk.X, pady=(0, 10))

        self.btn_random = ctk.CTkButton(
            self.left_frame, text="Generuj losowy graf",
            command=self.generate_random_graph,
            font=ctk.CTkFont(size=14, weight="bold"),
            height=35,
            corner_radius=8,
            fg_color="#D97706", hover_color="#B45309"
        )
        self.btn_random.pack(fill=ctk.X, pady=(0, 10))

        self.btn_clear = ctk.CTkButton(
            self.left_frame, text="Wyczyść wszystko",
            command=self.clear_all,
            font=ctk.CTkFont(size=14, weight="bold"),
            height=35,
            corner_radius=8,
            fg_color="#4B5563", hover_color="#374151"
        )
        self.btn_clear.pack(fill=ctk.X, pady=(0, 10))

        self.btn_run = ctk.CTkButton(
            self.left_frame, text="Znajdź i Rysuj",
            command=self.run_algorithm,
            font=ctk.CTkFont(size=15, weight="bold"),
            height=40,
            corner_radius=8
        )
        self.btn_run.pack(fill=ctk.X, pady=(0, 15))

        self.result_frame = ctk.CTkFrame(self.left_frame, corner_radius=10)
        self.result_frame.pack(fill=ctk.BOTH, expand=True)
        self.result_frame.grid_columnconfigure(0, weight=1)

        self.lbl_status = ctk.CTkLabel(
            self.result_frame, text="Status spójności",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.lbl_status.grid(row=0, column=0, padx=10, pady=(10, 5))

        self.txt_results = ctk.CTkTextbox(
            self.result_frame, font=ctk.CTkFont(size=13), state="disabled"
        )
        self.txt_results.grid(row=1, column=0, padx=15, pady=(5, 15), sticky="nsew")
        self.result_frame.grid_rowconfigure(1, weight=1)

        self.right_frame = ctk.CTkFrame(self)
        self.right_frame.grid(row=0, column=1, padx=(0, 20), pady=20, sticky="nsew")

        self.controls_frame = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        self.controls_frame.pack(fill=ctk.X, padx=10, pady=(10, 0))

        self.opt_layout = ctk.CTkOptionMenu(
            self.controls_frame,
            values=["Spring", "Circular", "Random"],
            variable=self.layout_var,
            command=self.redraw_graph,
            width=120
        )
        self.opt_layout.pack(side=ctk.LEFT, padx=(0, 10))

        self.btn_reroll = ctk.CTkButton(
            self.controls_frame,
            text="🔄",
            width=40,
            font=ctk.CTkFont(size=16),
            command=self.reroll_seed
        )
        self.btn_reroll.pack(side=ctk.LEFT, padx=(0, 10))

        self.chk_labels = ctk.CTkCheckBox(
            self.controls_frame,
            text="Pokaż etykiety",
            variable=self.show_labels_var,
            command=self.redraw_graph
        )
        self.chk_labels.pack(side=ctk.LEFT)

        self.figure, self.ax = plt.subplots(figsize=(6, 6))
        self.figure.patch.set_facecolor('#2b2b2b')
        self.ax.set_facecolor('#2b2b2b')
        self.canvas = FigureCanvasTkAgg(self.figure, self.right_frame)
        self.canvas.get_tk_widget().pack(fill=ctk.BOTH, expand=True, padx=10, pady=(10, 0))

        self.toolbar_frame = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        self.toolbar_frame.pack(fill=ctk.X, padx=10, pady=(0, 10))
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.toolbar_frame)
        self.toolbar.update()
        self.toolbar.pack(side=ctk.BOTTOM, fill=ctk.X)

    def run_algorithm(self):
        raw_text = self.txt_edges.get("1.0", ctk.END).strip()
        if not raw_text:
            messagebox.showwarning("Brak danych", "Proszę wprowadzić krawędzie grafu.")
            return

        edges = []
        for line_num, line in enumerate(raw_text.split('\n'), 1):
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) != 2:
                messagebox.showerror("Błąd", f"Błąd w linii {line_num}: '{line}'.\nWymagane są 2 węzły.")
                return
            edges.append((parts[0], parts[1]))

        triangles, connected = find_triangles(edges)

        self.current_edges = edges
        self.current_triangles = triangles

        if not connected:
            self.lbl_status.configure(text="⚠️ Graf NIE jest spójny!", text_color="#FF5252")
        else:
            self.lbl_status.configure(text="✅ Graf jest spójny.", text_color="#4CAF50")

        self.txt_results.configure(state="normal")
        self.txt_results.delete("1.0", ctk.END)
        self.txt_results.insert(ctk.END, f"Znalezione trójkąty ({len(triangles)}):\n\n")

        if triangles:
            for t in sorted(triangles):
                self.txt_results.insert(ctk.END, f" 🔹 {t[0]} - {t[1]} - {t[2]}\n")
        else:
            self.txt_results.insert(ctk.END, " Brak trójkątów.\n")

        self.txt_results.configure(state="disabled")

        self.draw_graph()

    def clear_all(self):
        self.txt_edges.delete("1.0", ctk.END)

        self.txt_results.configure(state="normal")
        self.txt_results.delete("1.0", ctk.END)
        self.txt_results.configure(state="disabled")

        self.lbl_status.configure(text="Status spójności", text_color=("gray10", "#DCE4EE"))

        self.current_edges = []
        self.current_triangles = []

        self.ax.clear()
        self.ax.axis('off')
        self.canvas.draw()

    def generate_random_graph(self):
        dialog = ctk.CTkInputDialog(text="Podaj liczbę wierzchołków (np. 5-15):", title="Losowy Graf")
        val = dialog.get_input()

        if not val or not val.isdigit():
            return

        n = int(val)
        if n < 3 or n > 50:
            messagebox.showwarning("Uwaga", "Zalecana liczba wierzchołków to od 3 do 50.")
            return

        self.txt_edges.delete("1.0", ctk.END)

        G = nx.gnp_random_graph(n, p=0.4)

        edges_text = ""
        for u, v in G.edges():
            edges_text += f"{u} {v}\n"

        self.txt_edges.insert(ctk.END, edges_text)
        self.run_algorithm()

    def reroll_seed(self):
        self.current_seed = random.randint(1, 100000)
        self.draw_graph()

    def redraw_graph(self, _=None):
        if self.current_edges:
            self.draw_graph()

    def draw_graph(self):
        self.ax.clear()
        self.ax.axis('off')

        if not self.current_edges:
            self.canvas.draw()
            return

        G = nx.Graph()
        G.add_edges_from(self.current_edges)

        triangle_edges = set()
        for t in self.current_triangles:
            triangle_edges.add(tuple(sorted([t[0], t[1]])))
            triangle_edges.add(tuple(sorted([t[1], t[2]])))
            triangle_edges.add(tuple(sorted([t[0], t[2]])))

        all_edges = set(tuple(sorted([u, v])) for u, v in self.current_edges)
        normal_edges = list(all_edges - triangle_edges)
        triangle_edges = list(triangle_edges)

        layout_type = self.layout_var.get()
        if layout_type == "Spring":
            pos = nx.spring_layout(G, seed=self.current_seed)
        elif layout_type == "Circular":
            pos = nx.circular_layout(G)
        else:
            pos = nx.random_layout(G, seed=self.current_seed)

        nx.draw_networkx_nodes(G, pos, ax=self.ax, node_color='#1f538d', node_size=500, edgecolors='white')

        if self.show_labels_var.get():
            nx.draw_networkx_labels(G, pos, ax=self.ax, font_color='white', font_weight='bold')

        nx.draw_networkx_edges(G, pos, ax=self.ax, edgelist=normal_edges, edge_color='#7a7a7a', width=2)
        nx.draw_networkx_edges(G, pos, ax=self.ax, edgelist=triangle_edges, edge_color='#FF5252', width=3.5)

        self.canvas.draw()


if __name__ == "__main__":
    app = TriangleFinderApp()
    app.mainloop()