# ui.py

import tkinter as tk
from tkinter import ttk, messagebox

from db import (
    get_connection,
    load_incidents,
    insert_resolved,
    delete_incident
)


class FeedbackUI:

    def __init__(self, root):
        self.root = root
        self.root.title("Feedback UI")

        self.conn = get_connection()
        self.temp_data = load_incidents(self.conn)
        self.selected = None

        # ---------- SELECT ----------
        tk.Label(root, text="Select Incident").pack()

        self.combo = ttk.Combobox(root, width=80)
        self.combo.pack()
        self.combo.bind("<<ComboboxSelected>>", self.load_selected)

        # ---------- DESCRIPTION ----------
        self.desc = tk.Label(root, text="", wraplength=600)
        self.desc.pack(pady=10)

        # ---------- PREDICTION ----------
        self.pred = tk.Label(root, text="")
        self.pred.pack(pady=10)

        # ---------- CORRECT / WRONG ----------
        self.var = tk.StringVar(value="yes")

        tk.Radiobutton(root, text="Correct", variable=self.var, value="yes", command=self.toggle).pack()
        tk.Radiobutton(root, text="Wrong", variable=self.var, value="no", command=self.toggle).pack()

        # ---------- CORRECTION FIELDS ----------
        self.category = tk.Entry(root)
        self.urgency = tk.Entry(root)
        self.impact = tk.Entry(root)
        self.priority = tk.Entry(root)

        # ---------- SOLUTION ----------
        tk.Label(root, text="Solution").pack()
        self.solution = tk.Text(root, height=5, width=70)
        self.solution.pack(pady=5)

        # ---------- BUTTONS ----------
        tk.Button(root, text="Submit", command=self.submit).pack(pady=5)
        tk.Button(root, text="Finish", command=self.finish).pack(pady=5)

        self.refresh()

    # ---------- REFRESH ----------
    def refresh(self):

        self.temp_data = load_incidents(self.conn)

        if not self.temp_data:
            messagebox.showinfo("Done", "No incidents to review")
            self.root.destroy()
            return

        values = [f"{i['id']} - {i['description'][:40]}" for i in self.temp_data]

        self.combo["values"] = values
        self.combo.current(0)

        self.load_selected(None)

    # ---------- LOAD INCIDENT ----------
    def load_selected(self, event):

        if not self.combo.get():
            return

        incident_id = self.combo.get().split(" - ")[0]

        self.selected = next(
            (i for i in self.temp_data if str(i["id"]) == str(incident_id)),
            None
        )

        if not self.selected:
            return

        self.desc.config(text=self.selected["description"])

        self.pred.config(text=str({
            "category": self.selected["category"],
            "urgency": self.selected["urgency"],
            "impact": self.selected["impact"],
            "priority": self.selected["priority"]
        }))

        # 🔥 carregar solução existente
        self.solution.delete("1.0", tk.END)
        if self.selected.get("solution"):
            self.solution.insert("1.0", self.selected["solution"])

    # ---------- TOGGLE ----------
    def toggle(self):

        if self.var.get() == "no":
            self.category.pack()
            self.urgency.pack()
            self.impact.pack()
            self.priority.pack()
        else:
            self.category.pack_forget()
            self.urgency.pack_forget()
            self.impact.pack_forget()
            self.priority.pack_forget()

    # ---------- SUBMIT ----------
    def submit(self):

        if not self.selected:
            return

        solution_text = self.solution.get("1.0", tk.END).strip()
        solution_text = solution_text if solution_text else None

        # ---------- CORRECT ----------
        if self.var.get() == "yes":

            final = {
                "category": self.selected["category"],
                "urgency": self.selected["urgency"],
                "impact": self.selected["impact"],
                "priority": self.selected["priority"]
            }

        # ---------- WRONG ----------
        else:

            if not all([
                self.category.get(),
                self.urgency.get(),
                self.impact.get(),
                self.priority.get()
            ]):
                messagebox.showerror("Error", "Fill all classification fields")
                return

            if not solution_text:
                messagebox.showerror("Error", "Solution is required when wrong")
                return

            final = {
                "category": self.category.get(),
                "urgency": self.urgency.get(),
                "impact": self.impact.get(),
                "priority": self.priority.get()
            }

        # ---------- SAVE ----------
        insert_resolved(self.conn, {
            "description": self.selected["description"],
            "category": final["category"],
            "urgency": final["urgency"],
            "impact": final["impact"],
            "priority": final["priority"],
            "solution": solution_text
        })

        delete_incident(self.conn, self.selected["id"])

        self.refresh()

    # ---------- CLOSE ----------
    def finish(self):
        self.conn.close()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = FeedbackUI(root)
    root.mainloop()