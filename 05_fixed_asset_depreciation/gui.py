"""固定資産 減価償却台帳ツール GUI アプリ。"""

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import main

matplotlib.rcParams["font.family"] = "Yu Gothic"


class LedgerApp(tk.Tk):
    """固定資産 減価償却台帳ツール のメインウィンドウ。"""

    def __init__(self):
        super().__init__()
        self.title(main.APP_TITLE)
        self.geometry("1180x720")
        self._df = None
        self._build_ui()
        self._load_default()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self) -> None:
        plt.close("all")
        self.destroy()

    def _build_ui(self) -> None:
        toolbar = ttk.Frame(self, padding=6)
        toolbar.pack(fill=tk.X)

        ttk.Button(toolbar, text="📂 CSVを開く", command=self._open_file).pack(side=tk.LEFT, padx=4)
        ttk.Button(toolbar, text="🔄 サンプル読込", command=self._load_default).pack(side=tk.LEFT, padx=4)
        ttk.Button(toolbar, text="💾 結果を保存", command=self._save).pack(side=tk.LEFT, padx=4)

        self._status_var = tk.StringVar(value="サンプルデータを読み込み中...")
        ttk.Label(toolbar, textvariable=self._status_var, foreground="gray").pack(side=tk.LEFT, padx=12)

        self._summary_frame = ttk.Frame(self, padding=(8, 2))
        self._summary_frame.pack(fill=tk.X)

        pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        pane.pack(fill=tk.BOTH, expand=True, padx=8, pady=6)

        left = ttk.Frame(pane)
        pane.add(left, weight=3)

        self._tree = ttk.Treeview(left, show="headings", height=24)
        vsb = ttk.Scrollbar(left, orient=tk.VERTICAL, command=self._tree.yview)
        hsb = ttk.Scrollbar(left, orient=tk.HORIZONTAL, command=self._tree.xview)
        self._tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self._tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        left.grid_rowconfigure(0, weight=1)
        left.grid_columnconfigure(0, weight=1)

        right = ttk.Frame(pane)
        pane.add(right, weight=2)

        self._fig, self._ax = plt.subplots(figsize=(5.4, 5.2))
        self._canvas = FigureCanvasTkAgg(self._fig, master=right)
        self._canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _load_default(self) -> None:
        self._load(main.default_data_path())

    def _open_file(self) -> None:
        path = filedialog.askopenfilename(
            initialdir=str(main.DATA_DIR),
            title="CSVを選択",
            filetypes=[("CSV files", "*.csv")],
        )
        if path:
            self._load(Path(path))

    def _load(self, path: Path) -> None:
        try:
            self._df = main.analyze(path)
        except Exception as exc:
            messagebox.showerror("読み込みエラー", str(exc))
            return
        self._status_var.set(f"読み込み完了: {path.name} ({len(self._df)} 件)")
        self._refresh_summary()
        self._refresh_tree()
        self._refresh_chart()

    def _refresh_summary(self) -> None:
        for child in self._summary_frame.winfo_children():
            child.destroy()
        summary = main.get_summary(self._df)
        for key, value in summary.items():
            card = ttk.Frame(self._summary_frame, padding=8, relief=tk.GROOVE)
            card.pack(side=tk.LEFT, padx=4, pady=2)
            ttk.Label(card, text=key, foreground="gray").pack(anchor=tk.W)
            ttk.Label(card, text=str(value), font=("Yu Gothic", 12, "bold")).pack(anchor=tk.W)

    def _refresh_tree(self) -> None:
        self._tree.delete(*self._tree.get_children())
        columns = list(self._df.columns)
        self._tree["columns"] = columns
        for col in columns:
            self._tree.heading(col, text=col)
            self._tree.column(col, width=120, anchor=tk.CENTER, stretch=True)
        for _, row in self._df.iterrows():
            values = []
            for value in row.tolist():
                if hasattr(value, "strftime"):
                    values.append(value.strftime("%Y-%m-%d"))
                elif isinstance(value, float):
                    values.append(f"{value:,.2f}")
                else:
                    values.append(str(value))
            self._tree.insert("", tk.END, values=values)

    def _refresh_chart(self) -> None:
        chart = main.get_chart_data(self._df)
        self._ax.clear()
        kind = chart.get("kind", "barh")
        labels = chart.get("labels", [])
        values = chart.get("values", [])
        colors = chart.get("colors")

        if kind == "pie":
            self._ax.pie(values, labels=labels, autopct="%1.0f%%", startangle=90)
        elif kind == "line":
            self._ax.plot(labels, values, marker="o", color=chart.get("line_color", "#1f77b4"))
            self._ax.tick_params(axis="x", rotation=45)
        elif kind == "bar":
            self._ax.bar(labels, values, color=colors)
            self._ax.tick_params(axis="x", rotation=45)
        else:
            self._ax.barh(labels, values, color=colors)

        self._ax.set_title(chart.get("title", main.APP_TITLE))
        if chart.get("xlabel"):
            self._ax.set_xlabel(chart["xlabel"])
        if chart.get("ylabel"):
            self._ax.set_ylabel(chart["ylabel"])
        self._fig.tight_layout()
        self._canvas.draw()

    def _save(self) -> None:
        if self._df is None:
            messagebox.showwarning("保存エラー", "保存対象のデータがありません")
            return
        try:
            out = main.save_results(self._df)
        except Exception as exc:
            messagebox.showerror("保存エラー", str(exc))
            return
        messagebox.showinfo("保存完了", f"保存しました:\n{out}")


if __name__ == "__main__":
    app = LedgerApp()
    app.mainloop()
