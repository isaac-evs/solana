# Primero importamos todas las herramientas que vamos a necesitar
import os
import base58
from tkinter import *
from tkinter import filedialog, messagebox, ttk
import ipfshttpclient
from solana.rpc.api import Client
from solders.keypair import Keypair
from solders.system_program import TransferParams, transfer
from solana.transaction import Transaction
from datetime import datetime
import shutil
import webbrowser

# Configuración - SOLO GATEWAY LOCAL
SOLANA_RPC = "https://api.devnet.solana.com"
IPFS_TIMEOUT = 30
LOCAL_IPFS_GATEWAY = "http://localhost:8080/ipfs/"  # Solo usamos local

class SolanaIPFSApp:
    def __init__(self, root):
        self.root = root
        self.root.title("IPFS + Solana Uploader - Gateway Local")
        self.root.geometry("650x450")
        
        self.file_path = ""
        self.cid = ""
        self.save_path = os.path.join(os.environ["USERPROFILE"], "Desktop")
        
        self.setup_ui()

    def setup_ui(self):
        # Título principal
        Label(self.root, text="IPFS + Solana Manager", font=("Arial", 14, "bold")).pack(pady=10)

        # === SECCIÓN SUBIR ARCHIVOS A IPFS ===
        upload_frame = LabelFrame(self.root, text="Subir Archivos a IPFS", font=("Arial", 10, "bold"))
        upload_frame.pack(fill="x", padx=10, pady=5)
        
        # Selector de archivos
        file_frame = Frame(upload_frame)
        file_frame.pack(fill="x", padx=5, pady=5)
        
        Button(file_frame, text="📁 Seleccionar archivo", command=self.select_file).pack(side=LEFT)
        self.file_label = Label(file_frame, text="Ningún archivo seleccionado", fg="gray", width=40, anchor="w")
        self.file_label.pack(side=LEFT, padx=10)

        # Botón para subir a IPFS
        Button(upload_frame, text="🚀 Subir a IPFS", command=self.upload_to_ipfs, 
               bg="#22C55E", fg="white", font=("Arial", 10, "bold")).pack(pady=10)

        # === SECCIÓN CLAVE PRIVADA SEGURA ===
        key_frame = LabelFrame(self.root, text="Clave Privada Segura", font=("Arial", 10, "bold"))
        key_frame.pack(fill="x", padx=10, pady=5)
        
        Label(key_frame, text="Clave privada Solana:", font=("Arial", 9)).pack(anchor="w", padx=5)
        
        # Frame para campo de clave y botón de visibilidad
        key_input_frame = Frame(key_frame)
        key_input_frame.pack(fill="x", padx=5, pady=2)
        
        # Campo de clave con asteriscos (Password)
        self.priv_key_entry = Entry(key_input_frame, width=60, show="•", font=("Courier", 9))
        self.priv_key_entry.pack(side=LEFT, fill="x", expand=True)
        
        # Botón para mostrar/ocultar clave
        self.show_key_btn = Button(key_input_frame, text="👁️", command=self.toggle_key_visibility,
                                 width=3, font=("Arial", 8))
        self.show_key_btn.pack(side=RIGHT, padx=(5,0))
        
        # Botón para verificar wallet (NO muestra dirección)
        Button(key_frame, text="✅ Verificar Wallet", command=self.verify_wallet,
               bg="#3B82F6", fg="white", font=("Arial", 9)).pack(pady=5)

        # === SECCIÓN REGISTRO EN SOLANA ===
        Button(self.root, text="🔗 Registrar en Solana", command=self.register_on_solana,
               bg="#9945FF", fg="white", font=("Arial", 10, "bold")).pack(pady=10)

        # === SECCIÓN ACCEDER A CONTENIDO IPFS ===
        access_frame = LabelFrame(self.root, text="Acceder a Contenido IPFS", font=("Arial", 10, "bold"))
        access_frame.pack(fill="x", padx=10, pady=5)
        
        # Frame para entrada de CID
        cid_frame = Frame(access_frame)
        cid_frame.pack(fill="x", padx=5, pady=5)
        
        Label(cid_frame, text="CID de IPFS:", font=("Arial", 9)).pack(side=LEFT)
        self.cid_entry = Entry(cid_frame, width=50, font=("Courier", 9))
        self.cid_entry.pack(side=LEFT, padx=5, fill="x", expand=True)
        
        # Botón para pegar último CID
        Button(cid_frame, text="📋 Pegar CID", command=self.paste_last_cid,
               font=("Arial", 7)).pack(side=RIGHT, padx=2)
        
        # Info del gateway
        gateway_info = Frame(access_frame)
        gateway_info.pack(fill="x", padx=5, pady=2)
        Label(gateway_info, text=f"Gateway: {LOCAL_IPFS_GATEWAY}", 
              fg="blue", font=("Courier", 8)).pack()
        
        # Botón para abrir en navegador
        Button(access_frame, text="🌐 Abrir en Navegador", command=self.open_ipfs_in_browser,
               bg="#EC4899", fg="white", font=("Arial", 10, "bold")).pack(pady=10)

        # === SECCIÓN DESCARGAR ARCHIVOS IPFS ===
        download_frame = LabelFrame(self.root, text="Descargar desde IPFS", font=("Arial", 10, "bold"))
        download_frame.pack(fill="x", padx=10, pady=5)
        
        Button(download_frame, text="📥 Descargar Archivo Local", command=self.download_from_ipfs,
               bg="#F59E0B", fg="white", font=("Arial", 10, "bold")).pack(pady=10)
        
        # Etiqueta para mostrar estado de descarga
        self.download_status = Label(download_frame, text="", fg="gray", font=("Arial", 8))
        self.download_status.pack(pady=2)

        # === BARRA DE ESTADO ===
        self.status_bar = Label(self.root, text=f"Listo | Gateway: {LOCAL_IPFS_GATEWAY}", bd=1, relief=SUNKEN, anchor=W)
        self.status_bar.pack(side=BOTTOM, fill=X)

    def toggle_key_visibility(self):
        """Alternar entre mostrar y ocultar la clave privada"""
        if self.priv_key_entry.cget('show') == '':
            self.priv_key_entry.config(show='•')
            self.show_key_btn.config(text='👁️')
        else:
            self.priv_key_entry.config(show='')
            self.show_key_btn.config(text='🙈')

    def verify_wallet(self):
        """Verificar que la clave privada es válida (NO muestra dirección)"""
        priv_key = self.priv_key_entry.get().strip()
        if not priv_key:
            messagebox.showwarning("Verificación", "Ingresa tu clave privada primero")
            return
        
        try:
            clean_key = priv_key.replace("\n", "").replace(" ", "")
            keypair = Keypair.from_base58_string(clean_key)
            client = Client(SOLANA_RPC)
            balance = client.get_balance(keypair.pubkey())
            
            # MENSAJE MODIFICADO - No muestra la dirección pública
            messagebox.showinfo("✅ Wallet Válida", 
                              f"¡Wallet verificada correctamente!\n\n"
                              f"Saldo: {balance.value / 1e9:.6f} SOL\n"
                              f"Red: Devnet\n"
                              f"Estado: ✅ Conectada y válida")
            
        except Exception as e:
            messagebox.showerror("❌ Wallet Inválida", 
                               f"Clave privada incorrecta:\n{str(e)}")

    def paste_last_cid(self):
        """Pegar el último CID en el campo"""
        if self.cid:
            self.cid_entry.delete(0, END)
            self.cid_entry.insert(0, self.cid)
            self.status_bar.config(text="CID pegado desde última subida")
        else:
            messagebox.showinfo("Info", "No hay CID reciente para pegar")

    def open_ipfs_in_browser(self):
        """Abrir el contenido IPFS en el navegador usando GATEWAY LOCAL"""
        cid = self.cid_entry.get().strip()
        if not cid:
            messagebox.showwarning("Advertencia", "Ingresa un CID de IPFS")
            return

        ipfs_url = f"{LOCAL_IPFS_GATEWAY}{cid}"
        
        try:
            self.status_bar.config(text=f"Abriendo: {ipfs_url}")
            webbrowser.open(ipfs_url)
            
            # Guardar registro del acceso
            access_file = os.path.join(self.save_path, f"IPFS_ACCESS_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
            with open(access_file, "w", encoding="utf-8") as f:
                f.write(f"CID: {cid}\n")
                f.write(f"URL Local: {ipfs_url}\n")
                f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            messagebox.showinfo("✅ Abriendo Navegador", 
                              f"Accediendo a contenido IPFS:\n\n"
                              f"📄 CID: {cid}\n"
                              f"🌐 Gateway: Local\n"
                              f"🔗 URL: {ipfs_url}")
            
        except Exception as e:
            messagebox.showerror("❌ Error", 
                               f"No se pudo abrir el enlace:\n{str(e)}\n\n"
                               f"URL: {ipfs_url}")

    def select_file(self):
        """Seleccionar archivo para subir a IPFS"""
        self.file_path = filedialog.askopenfilename(
            title="Seleccionar archivo",
            filetypes=[("PDF files", "*.pdf"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if self.file_path:
            filename = os.path.basename(self.file_path)
            self.file_label.config(text=filename)
            self.status_bar.config(text=f"Archivo seleccionado: {filename}")

    def upload_to_ipfs(self):
        """Subir archivo a IPFS"""
        if not self.file_path:
            messagebox.showwarning("Advertencia", "Selecciona un archivo primero")
            return

        try:
            self.status_bar.config(text="Subiendo a IPFS...")
            
            with ipfshttpclient.connect(timeout=IPFS_TIMEOUT) as ipfs:
                res = ipfs.add(self.file_path)
                self.cid = res["Hash"]
                
                # URL LOCAL para el archivo
                local_ipfs_url = f"{LOCAL_IPFS_GATEWAY}{self.cid}"
                
                # Guardar información en el path seleccionado
                info_file = os.path.join(self.save_path, f"IPFS_CID_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
                
                with open(info_file, "w", encoding="utf-8") as f:
                    f.write(f"CID: {self.cid}\n")
                    f.write(f"Archivo: {os.path.basename(self.file_path)}\n")
                    f.write(f"URL Local: {local_ipfs_url}\n")
                    f.write(f"Path Original: {self.file_path}\n")
                    f.write(f"Path Guardado: {info_file}\n")
                    f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                
                # Poner el CID en el campo de descarga
                self.cid_entry.delete(0, END)
                self.cid_entry.insert(0, self.cid)
                
                self.status_bar.config(text=f"Subido exitosamente - CID: {self.cid}")
                
                messagebox.showinfo("✅ Éxito", 
                                  f"Archivo subido a IPFS\n\n"
                                  f"📄 CID: {self.cid}\n"
                                  f"🔗 URL Local: {local_ipfs_url}\n"
                                  f"📁 Guardado en: {info_file}")
                                  
        except Exception as e:
            self.status_bar.config(text="Error al subir a IPFS")
            messagebox.showerror("❌ Error IPFS", f"No se pudo subir el archivo:\n{str(e)}")

    def download_from_ipfs(self):
        """Descargar archivo desde IPFS usando CID"""
        cid = self.cid_entry.get().strip()
        if not cid:
            messagebox.showwarning("Advertencia", "Ingresa un CID de IPFS")
            return

        try:
            self.status_bar.config(text=f"Descargando CID: {cid}...")
            self.download_status.config(text="Conectando a IPFS local...")
            
            # Seleccionar carpeta de destino
            download_dir = filedialog.askdirectory(title="Seleccionar carpeta para descargar")
            if not download_dir:
                return
            
            with ipfshttpclient.connect(timeout=IPFS_TIMEOUT) as ipfs:
                self.download_status.config(text="Descargando archivo...")
                
                # Descargar el archivo
                ipfs.get(cid, target=download_dir)
                
                # La descarga crea una carpeta con el CID, mover el archivo
                cid_folder = os.path.join(download_dir, cid)
                if os.path.exists(cid_folder):
                    downloaded_files = os.listdir(cid_folder)
                    
                    if downloaded_files:
                        original_file = os.path.join(cid_folder, downloaded_files[0])
                        final_path = os.path.join(download_dir, downloaded_files[0])
                        
                        # Mover a la carpeta principal
                        shutil.move(original_file, final_path)
                        # Eliminar carpeta vacía
                        os.rmdir(cid_folder)
                        
                        # URL local del archivo descargado
                        local_url = f"{LOCAL_IPFS_GATEWAY}{cid}"
                        
                        self.download_status.config(text=f"Descargado: {downloaded_files[0]}")
                        self.status_bar.config(text=f"Descarga completada: {final_path}")
                        
                        # Guardar registro de la descarga
                        download_info_file = os.path.join(download_dir, f"DOWNLOAD_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
                        with open(download_info_file, "w", encoding="utf-8") as f:
                            f.write(f"CID Descargado: {cid}\n")
                            f.write(f"Archivo: {downloaded_files[0]}\n")
                            f.write(f"Path Local: {final_path}\n")
                            f.write(f"URL Local: {local_url}\n")
                            f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                        
                        messagebox.showinfo("✅ Descarga Exitosa",
                                          f"Archivo descargado:\n\n"
                                          f"📄 Archivo: {downloaded_files[0]}\n"
                                          f"📁 Ubicación: {final_path}\n"
                                          f"🔗 URL Local: {local_url}")
                    else:
                        self.download_status.config(text="Error: Carpeta vacía")
                else:
                    self.download_status.config(text="Error: No se creó carpeta de descarga")
                    
        except Exception as e:
            self.download_status.config(text="Error en descarga")
            self.status_bar.config(text="Error al descargar de IPFS")
            messagebox.showerror("❌ Error Descarga", 
                               f"No se pudo descargar el archivo:\n{str(e)}")

    def register_on_solana(self):
        """Registrar transacción en Solana"""
        if not self.cid:
            messagebox.showwarning("Error", "Primero sube el archivo a IPFS")
            return

        priv_key = self.priv_key_entry.get().strip()
        if not priv_key:
            messagebox.showerror("Error", "Ingresa tu clave privada")
            return

        try:
            private_key_combined = priv_key.replace("\n", "").replace(" ", "")
            keypair = Keypair.from_base58_string(private_key_combined)
            client = Client(SOLANA_RPC)
            
            version = client.get_version()
            if not version:
                messagebox.showerror("Error", "No se puede conectar a Solana")
                return

            latest_blockhash = client.get_latest_blockhash()
            if not latest_blockhash or not latest_blockhash.value:
                messagebox.showerror("Error", "No se pudo obtener blockhash")
                return
                
            recent_blockhash = latest_blockhash.value.blockhash

            transaction = Transaction(
                recent_blockhash=recent_blockhash,
                instructions=[
                    transfer(
                        TransferParams(
                            from_pubkey=keypair.pubkey(),
                            to_pubkey=keypair.pubkey(),
                            lamports=1000
                        )
                    )
                ]
            )

            tx_signature = client.send_transaction(transaction, keypair)
            
            if not tx_signature or not tx_signature.value:
                messagebox.showerror("Error", "No se recibió confirmación")
                return

            tx_url = f"https://explorer.solana.com/tx/{tx_signature.value}?cluster=devnet"
            
            # URL local para el CID
            local_ipfs_url = f"{LOCAL_IPFS_GATEWAY}{self.cid}"
            
            # Guardar registro en el path seleccionado
            tx_info_file = os.path.join(self.save_path, f"Solana_TX_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
            with open(tx_info_file, "w", encoding="utf-8") as f:
                f.write(f"CID en IPFS: {self.cid}\n")
                f.write(f"URL Local IPFS: {local_ipfs_url}\n")
                f.write(f"Transacción: {tx_url}\n")
                f.write(f"Path: {tx_info_file}\n")
                f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

            self.status_bar.config(text=f"Transacción registrada | URL Local: {local_ipfs_url}")
            messagebox.showinfo("✅ Éxito", 
                              f"Registro completado en Solana Devnet\n\n"
                              f"📄 CID: {self.cid}\n"
                              f"🔗 URL Local: {local_ipfs_url}\n"
                              f"📊 Transacción: {tx_url}")

        except Exception as e:
            self.status_bar.config(text="Error en transacción Solana")
            messagebox.showerror("❌ Error Solana", 
                               f"Fallo al registrar:\n{str(e)}")

    def open_save_path(self):
        """Abrir la carpeta de guardado en el explorador de archivos"""
        try:
            os.startfile(self.save_path)
        except:
            messagebox.showerror("Error", f"No se pudo abrir: {self.save_path}")

# Punto de entrada
if __name__ == "__main__":
    root = Tk()
    app = SolanaIPFSApp(root)
    root.mainloop()
