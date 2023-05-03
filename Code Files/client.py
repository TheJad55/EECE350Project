import socket
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import threading

# the class is to create a user interface
# every root is a window
# every label is a text 
# every entry is a box asking for input
# every label or entry should be put in a pack 
# we can modify the size color alignment of each pack

class GameGUI:
    def __init__(self, root):
        self.root = root
        # opens a window
        self.root.title("Matching Number Game")
        self.root.geometry("500x500")

        # Load the GIF
        self.frames = []
        self.gif = Image.open("img/he.gif")
        for frame in range(self.gif.n_frames):
            self.gif.seek(frame)
            self.frames.append(ImageTk.PhotoImage(self.gif))

        # Create a label for the GIF and add it to the window
        self.label = tk.Label(self.root, image=self.frames[0])
        self.label.pack()

        # Start the animation
        self.animate(0)

        # lbl_name is "Enter your name label"
        self.lbl_name = tk.Label(self.root, text="Enter your name:")
        self.lbl_name.pack()
        self.entry_name = tk.Entry(self.root)
        self.entry_name.pack()

        # connect button
        self.btn_connect = tk.Button(self.root, text="Connect", command=self.connect_to_server)
        self.btn_connect.pack()

        # pack_forget will close the pack
        self.frame_game = tk.Frame(self.root)
        self.frame_game.pack_forget()

        # the random number
        self.lbl_random_number = tk.Label(self.frame_game, text="")
        self.lbl_random_number.pack()

        # "Type the number:"
        self.lbl_guess = tk.Label(self.frame_game, text="Type the number:")
        self.lbl_guess.pack()

        # The user input for number
        self.entry_guess = tk.Entry(self.frame_game)
        self.entry_guess.pack()

        # send button
        self.btn_guess = tk.Button(self.frame_game, text="Send", command=self.send_guess)
        self.btn_guess.pack()

        # result label
        self.lbl_result = tk.Label(self.frame_game, text="")
        self.lbl_result.pack()

        # final result label
        self.lbl_final_result = tk.Label(self.frame_game, text="")
        self.lbl_final_result.pack()

        # overall scores table
        self.treeview_overall_scores = ttk.Treeview(self.frame_game, columns=("Player", "Score"), show="headings")
        self.treeview_overall_scores.column("Player", width=50, anchor="center")
        self.treeview_overall_scores.column("Score", width=50, anchor="center")
        self.treeview_overall_scores.heading("Player", text="Player")
        self.treeview_overall_scores.heading("Score", text="Score")
        self.treeview_overall_scores.pack_forget()



        # create a thread for receiving messages from the server
        self.recv_thread = threading.Thread(target=self.receive_messages)

        # bind socket close method to WM_DELETE_WINDOW event of tkinter window
        self.root.protocol("WM_DELETE_WINDOW", self.close_connection)

    # function to animate gif
    def animate(self, index):
        self.label.configure(image=self.frames[index])
        index = (index + 1) % len(self.frames)
        self.root.after(50, self.animate, index)

    def connect_to_server(self):
        # specify the server's IP address and port number
        SERVER_IP = '127.0.0.1'
        SERVER_PORT = 12345

        # create a TCP socket
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # connect to the server
        self.client_socket.connect((SERVER_IP, SERVER_PORT))

        # send the player name to the server
        name = self.entry_name.get()
        self.client_socket.send(name.encode())

        # receive the welcome message from the server
        # random number, name and welcome message all appear in the same position
        # thats why we have to close each after finishing
        welcome_message = self.client_socket.recv(1024)
        self.lbl_random_number.config(text=welcome_message.decode())
        self.lbl_random_number.pack_forget()

        # show the game UI
        self.frame_game.pack()
        self.btn_connect.pack_forget()
        self.lbl_name.pack_forget()
        self.entry_name.pack_forget()

        # start the thread for receiving messages
        self.recv_thread.start()

    def send_guess(self):
        guess = self.entry_guess.get()
        self.client_socket.send(guess.encode())

    def receive_messages(self):
        while True:
            # add error detection of client side
            try:
                message = self.client_socket.recv(1024).decode()
            except ConnectionResetError:
                # handle disconnection from server
                self.lbl_result.config(text="Game has ended due to a disconnection")
                break
            if not message:
                break
            elif message.startswith("Random number is"):
                self.lbl_random_number.config(text=message)
            elif message.startswith("Round"):
                self.lbl_result.config(text=message)
            elif message.startswith("Game over"):
                self.lbl_final_result.config(text=message)
                self.close_connection()
                break
            elif message.startswith("Player disconnected"):
                self.lbl_result.config(text=message)
                break
            elif message.startswith("Overall Scores:"):
                self.treeview_overall_scores.delete(*self.treeview_overall_scores.get_children())
                scores = message.split("\n")[1:-1]  # Exclude the first and last lines
                for score_line in scores:
                    player, score = score_line.split(": ")
                    self.treeview_overall_scores.insert("", "end", values=(player, score))
                self.treeview_overall_scores.pack()


            else:
                self.lbl_final_result.config(text=message)


    def close_connection(self):
        # close the socket connection
        self.client_socket.close()
        self.root.destroy()

    def run(self):
        self.root.mainloop()




if __name__ == "__main__":
    root = tk.Tk()
    gui = GameGUI(root)
    gui.run()
