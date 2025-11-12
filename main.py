# Primero importamos todas las herramientas que vamos a necesitar
# como si fuera nuestra caja de herramientas digital
import os  # Para trabajar con archivos y carpetas
from tkinter import *  # Para crear la ventana e interfaz gráfica
from tkinter import (  # Para seleccionar archivos y mostrar mensajes
    filedialog,
    messagebox,
)

import base58  # Para manejar claves de Solana
import ipfshttpclient  # Para conectarnos a IPFS
from solana.rpc.api import Client  # Para hablar con la blockchain de Solana
from solana.transaction import Transaction  # Para armar transacciones
from solders.keypair import Keypair  # Para manejar billeteras de Solana
from solders.system_program import TransferParams, transfer  # Para hacer transacciones

# Aquí configuramos nuestras direcciones y tiempos de espera
SOLANA_RPC = "https://api.devnet.solana.com"  # Usamos la red de pruebas de Solana
IPFS_TIMEOUT = 30  # Esperamos máximo 30 segundos al subir a IPFS


# Esta es la clase principal de nuestra aplicación
# Como el "cerebro" de todo el programa
class SolanaIPFSApp:
    def __init__(self, root):
        # Configuramos la ventana principal
        self.root = root
        self.root.title("IPFS + Solana Uploader v2.0")  # Título bonito
        self.root.geometry("550x300")  # Tamaño de la ventana

        # Variables para guardar información
        self.file_path = ""  # Donde guardamos la ruta del archivo
        self.cid = ""  # Aquí guardaremos el ID único de IPFS

        # Llamamos a la función que crea la interfaz
        self.setup_ui()

    def setup_ui(self):
        # Creamos todos los botones y textos de la interfaz

        # Título principal
        Label(self.root, text="IPFS + Solana", font=("Arial", 14, "bold")).pack(pady=10)

        # Marco para el selector de archivos
        file_frame = Frame(self.root)
        file_frame.pack(pady=10)

        # Botón para seleccionar archivo
        Button(file_frame, text=" Seleccionar archivo", command=self.select_file).pack(
            side=LEFT
        )

        # Etiqueta que muestra qué archivo tenemos seleccionado
        self.file_label = Label(
            file_frame,
            text="Un momento, ningún archivo seleccionado",
            fg="gray",
            width=40,
            anchor="w",
        )
        self.file_label.pack(side=LEFT, padx=10)

        # Botón para subir a IPFS (verde)
        Button(
            self.root,
            text="Subir a IPFS",
            command=self.upload_to_ipfs,
            fg="black",
            font=("Arial", 10, "bold"),
        ).pack(pady=10)

        # Campo para la clave privada
        Label(
            self.root, text="Clave privada Solana (base58):", font=("Arial", 10)
        ).pack(pady=5)
        self.priv_key_entry = Entry(self.root, width=70)
        self.priv_key_entry.pack()

        # Botón para registrar en Solana (morado)
        Button(
            self.root,
            text="Registrar en Solana",
            command=self.register_on_solana,
            bg="#9945FF",
            fg="white",
            font=("Arial", 10, "bold"),
        ).pack(pady=15)

    def select_file(self):
        # Abre una ventana para elegir archivos (solo PDF y TXT)
        self.file_path = filedialog.askopenfilename(
            filetypes=[("Archivos", "*.pdf *.txt")]
        )

        # Si seleccionamos un archivo, actualizamos la etiqueta
        if self.file_path:
            self.file_label.config(text=os.path.basename(self.file_path))

    def upload_to_ipfs(self):
        # Primero revisamos que hayamos seleccionado un archivo
        if not self.file_path:
            messagebox.showwarning("¡Cuidado!", "¡Selecciona un archivo primero!")
            return

        try:
            # Nos conectamos a IPFS (como conectar un pendrive)
            with ipfshttpclient.connect(timeout=IPFS_TIMEOUT) as ipfs:
                # Subimos el archivo y obtenemos su CID (como su huella digital)
                res = ipfs.add(self.file_path)
                self.cid = res["Hash"]

                # Guardamos la información en el escritorio
                desktop = os.path.join(os.environ["USERPROFILE"], "Desktop")
                with open(os.path.join(desktop, f"IPFS_CID.txt"), "w") as f:
                    f.write(f"CID: {self.cid}\n")
                    f.write(f"Enlace: https://ipfs.io/ipfs/{self.cid}\n")

                # Mostramos mensaje de éxito
                messagebox.showinfo("Éxito", f" Archivo subido a IPFS\nCID: {self.cid}")
        except Exception as e:
            # Si algo sale mal, mostramos el error
            messagebox.showerror("Error IPFS", f"No se pudo subir: {str(e)}")

    def register_on_solana(self):
        # Revisamos que ya hayamos subido el archivo a IPFS
        if not self.cid:
            messagebox.showwarning("Error", "Primero sube el archivo a IPFS")
            return

        # Obtenemos la clave privada que escribió el usuario
        priv_key = self.priv_key_entry.get().strip()
        if not priv_key:
            messagebox.showerror("Error", "Ingresa tu clave privada (base58)")
            return

        try:
            # Convertimos la clave privada a un formato que Solana entienda
            keypair = Keypair.from_base58_string(priv_key)

            # Nos conectamos a Solana
            client = Client(SOLANA_RPC)

            # Obtenemos información reciente de la blockchain
            recent_blockhash = client.get_latest_blockhash().value.blockhash

            # Preparamos la transacción (como llenar un formulario)
            transaction = Transaction(
                recent_blockhash=recent_blockhash,
                instructions=[
                    transfer(
                        TransferParams(
                            from_pubkey=keypair.pubkey(),  # Quién envía
                            to_pubkey=keypair.pubkey(),  # Quién recibe (en este caso, nosotros mismos)
                            lamports=0,  # Cantidad de SOL (0 porque solo queremos registrar datos)
                        )
                    )
                ],
            )

            # Enviamos la transacción a la blockchain
            tx_hash = client.send_transaction(transaction, keypair)

            # Creamos un enlace para ver la transacción
            tx_url = f"https://explorer.solana.com/tx/{tx_hash.value}?cluster=devnet"

            # Guardamos los detalles en el escritorio
            desktop = os.path.join(os.environ["USERPROFILE"], "Desktop")
            with open(os.path.join(desktop, "Solana_TX.txt"), "w") as f:
                f.write(f"CID en IPFS: {self.cid}\n")
                f.write(f"Transacción: {tx_url}\n")

            # Mostramos mensaje de éxito con el enlace
            messagebox.showinfo(
                "¡Éxito!",
                f"Registro completado en Solana Devnet\nVer transacción:\n{tx_url}",
            )
        except Exception as e:
            # Si algo falla, mostramos el error
            messagebox.showerror("Error Solana", f"Fallo al registrar: {str(e)}")


# Esto es como el botón de "encendido" del programa
if __name__ == "__main__":
    root = Tk()  # Creamos la ventana principal
    app = SolanaIPFSApp(root)  # Iniciamos nuestra aplicación
    root.mainloop()  # Y la dejamos corriendo
