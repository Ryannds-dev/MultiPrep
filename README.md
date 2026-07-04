<p align="center">
  <img src="assets/multiprep-logo-2.png" alt="Logo MultiPrep 2.0.0" width="180">
</p>

<h1 align="center">MultiPrep 2.0.0</h1>

<p align="center"><strong>Édition Google Workspace · Windows</strong></p>

MultiPrep est une application Windows de préparation et d’assemblage de dossiers PDF. Elle importe des documents de plusieurs sources, affiche leurs pages, permet de les réorganiser et génère un PDF final avec un nom normalisé.

La version 2.0.0 est conçue en priorité pour Google Workspace tout en conservant le fonctionnement historique avec les fichiers locaux et les applications de bureau.

## Deux modes clairement séparés

### Mode Gmail — mode par défaut

Destiné à Gmail ouvert dans un navigateur :

- glisser-déposer des pièces jointes Gmail dans la grande zone jaune ;
- import des PDF, documents Word, JPG et PNG ;
- copie d’une image insérée dans le corps du message, puis `Ctrl+V` ou clic droit → **Coller** ;
- collage d’un fichier JPG/PNG copié depuis l’Explorateur Windows ;
- imports successifs sans redémarrer MultiPrep.

Le composant natif Windows intégré à MultiPrep prend en charge les fichiers virtuels et le transfert asynchrone utilisés par les navigateurs. Il ne dépend pas de Google Chrome : il fonctionne avec les navigateurs Windows compatibles avec ces mécanismes, notamment Microsoft Edge et les navigateurs Chromium.

### Mode classique

Destiné aux fichiers locaux et aux applications de bureau :

- bouton **Importer des fichiers** ;
- glisser-déposer depuis l’Explorateur Windows ou le Bureau ;
- glisser-déposer depuis une application de bureau qui expose un fichier compatible, dont Outlook bureau ;
- collage d’une capture ou d’une image locale.

Outlook n’est donc qu’un exemple de source compatible, pas une obligation.

## Formats pris en charge

- PDF : `.pdf`
- Microsoft Word : `.doc`, `.docx`
- Images : `.jpg`, `.jpeg`, `.png`

L’import Word utilise Microsoft Word installé sur le poste pour produire un PDF fidèle à la mise en page d’origine.

## Fonctions principales

- aperçu des pages sous forme de cartes ;
- rendu progressif et parallèle des miniatures ;
- sélection simple, multiple ou par plage ;
- réorganisation par glisser-déposer avec indicateur d’insertion ;
- suppression et rotation des pages ;
- insertion de séparateurs PDF ;
- aperçu détaillé redimensionnable ;
- mémorisation de la dernière date utilisée ;
- export au format `AAAA-MM-JJ_NOM-Prenom_P.pdf`.

## Performances de la version 2.0.0

La grille utilise un delegate graphique léger au lieu de créer un widget complet par page. Les modèles apparaissent immédiatement, puis les miniatures sont produites hors du thread graphique, par lots parallèles et mises en cache.

Mesures de référence sur le poste de développement :

- environ 10 à 12 ms pour injecter 500 pages dans la grille ;
- environ 0,63 seconde pour générer 120 miniatures d’un PDF réel.

## Architecture

```text
MultiPrep/
├── assets/                         Logos et composant natif Gmail
├── dist/MultiPrep.exe              Livrable Windows
├── multiprep/
│   ├── models/                     Modèles de données
│   ├── services/                   PDF, dépôt, Gmail, Word, presse-papiers
│   ├── ui/                         Fenêtres, grille, delegate et styles
│   └── utils/                      Chemins et couleurs
├── separateurs/                    Bibliothèque de séparateurs PDF
├── tests/                          Tests de non-régression
├── tools/GmailDropHelper.cs        Source du composant natif Windows
├── HISTORIQUE_COMMITS.md           Historique fonctionnel et technique
├── documentation_multiprep.min.html Documentation technique locale
├── Specifications techniques MultiPrep.docx
├── Specifications techniques MultiPrep.pdf
├── MultiPrep.spec                  Configuration PyInstaller
└── run.py                          Point d’entrée
```

Fichiers clés :

- `multiprep/ui/main_window.py` : fenêtre principale et gestion des modes ;
- `multiprep/ui/editor_view.py` : en-tête, formulaires et consignes ;
- `multiprep/ui/page_grid_list.py` : grille, sélection et glisser-déposer ;
- `multiprep/ui/page_card_delegate.py` : rendu léger des cartes ;
- `multiprep/services/drop_service.py` : formats locaux, Outlook et navigateur ;
- `multiprep/services/gmail_import_service.py` : cycle de vie du helper Gmail ;
- `multiprep/services/pdf_service.py` : conversion d’images et fusion PDF ;
- `multiprep/services/thumbnail_service.py` : miniatures différées et groupées.

## Installation pour le développement

Prérequis :

- Windows 10/11 ;
- Python 3.10 ou plus récent ;
- Microsoft Word pour importer `.doc` et `.docx`.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run.py
```

Dépendances PDF validées :

```text
PyMuPDF==1.26.7
pypdf==6.10.2
```

## Tests

```powershell
python -m unittest discover -s tests -v
```

## Compilation Windows

Compiler le helper natif :

```powershell
& 'C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe' `
  /nologo /target:winexe /optimize+ `
  /out:assets\GmailDropHelper.exe `
  /reference:System.Windows.Forms.dll `
  /reference:System.Drawing.dll `
  tools\GmailDropHelper.cs
```

Compiler l’application :

```powershell
python -m PyInstaller --noconfirm --clean `
  --workpath "$env:TEMP\multiprep-build" `
  --distpath dist MultiPrep.spec
```

Le livrable attendu est uniquement `dist/MultiPrep.exe` ; le dossier de travail PyInstaller est placé dans le répertoire temporaire Windows.

## Données locales

MultiPrep utilise :

- `settings.json` pour la dernière date ;
- `separateurs/` pour la bibliothèque de séparateurs ;
- `temp/` pour les miniatures, conversions et pièces jointes temporaires ;
- `exports/` pour les PDF générés.

Le cache temporaire est nettoyé au lancement et à la fermeture normale de l’application.
