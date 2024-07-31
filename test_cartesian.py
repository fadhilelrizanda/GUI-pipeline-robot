import tkinter as tk


class CartesianCoordinateApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Cartesian Coordinate System")

        self.canvas = tk.Canvas(root, width=400, height=400, bg='white')
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.setup_coordinates()
        self.canvas.bind("<Button-1>", self.on_click)

        self.label = tk.Label(root, text="Click on the coordinate system")
        self.label.pack()

        # To keep track of the current point
        self.current_point = None

    def setup_coordinates(self):
        # Draw the x and y axes
        self.canvas.create_line(50, 350, 350, 350, fill='black')  # x-axis
        self.canvas.create_line(50, 50, 50, 350, fill='black')  # y-axis

        # Draw grid lines
        for i in range(-10, 11):
            x = 50 + i * 30
            y = 350 - i * 30
            self.canvas.create_line(x, 50, x, 350, dash=(4, 2), fill='grey')
            self.canvas.create_line(50, y, 350, y, dash=(4, 2), fill='grey')

        # Label the axes
        for i in range(11):
            x = 50 + i * 30
            y = 350 - i * 30
            self.canvas.create_text(x, 360, text=str(i), anchor='n')
            self.canvas.create_text(40, y, text=str(i), anchor='e')

    def on_click(self, event):
        x, y = event.x, event.y
        if 50 <= x <= 350 and 50 <= y <= 350:
            # Convert pixel coordinates to Cartesian coordinates
            cartesian_x = (x - 50) // 30
            cartesian_y = 10 - (y - 50) // 30
            self.label.config(
                text=f"Clicked at Cartesian coordinate: ({cartesian_x}, {cartesian_y})")

            # Clear the previous point if it exists
            if self.current_point:
                self.canvas.delete(self.current_point)

            # Draw the new point
            self.current_point = self.canvas.create_oval(
                x-5, y-5, x+5, y+5, fill='red')


if __name__ == "__main__":
    root = tk.Tk()
    app = CartesianCoordinateApp(root)
    root.mainloop()
