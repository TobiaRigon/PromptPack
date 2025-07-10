Crea un'applicazione Python con interfaccia grafica usando PySimpleGUI, chiamata "PromptPack".

Obiettivo: generare un file `.md` o `.txt` contenente il contenuto di file sorgente, utile come prompt AI.

Funzionalità richieste:

1. Interfaccia iniziale con:

   - Campo per selezionare una **cartella di partenza (progetto)**
   - Campo multiselezione per scegliere le **estensioni di file da includere** (default: .php, .js, .ts, .html, .css)
   - Campo multiselezione per indicare **cartelle da escludere** (es. vendor, node_modules, .git, ecc.)
   - Campo multiselezione per **file da escludere** (es. .env, README.md, ecc.)
   - Scelta tra **formato output**: `.md` o `.txt`
   - Checkbox per opzioni di formattazione:
     - Includere nomi file come intestazioni (`## path/to/file`)
     - Usare blocchi di codice (` ```lang ... ``` `) se formato Markdown
   - Pulsante per **selezionare la cartella di destinazione**
   - Pulsante "Genera"

2. Quando si clicca su "Genera":

   - L'app scandisce i file ricorsivamente dalla cartella sorgente
   - Filtra in base a estensioni, esclusioni e regole definite
   - Costruisce un file di output contenente:
     - Header con nome progetto e data (`YYYYMMDD`)
     - Per ogni file: percorso relativo + contenuto
     - Se output è `.md`, usa blocchi di codice con linguaggio rilevato da estensione
     - Se output è `.txt`, il contenuto è grezzo, senza markdown

3. Il file risultante viene salvato nella cartella destinazione, con nome:  
   `nomeprogetto-YYYYMMDD.md` o `.txt`

4. Mostrare un popup finale con il messaggio: "File generato in: [percorso completo]"

Requisiti tecnici:

- Usa solo librerie standard + PySimpleGUI
- Compatibile con PyInstaller per essere compilato come eseguibile Windows
- Usa `pathlib` per la gestione dei percorsi
