# MultiPrep

Application desktop Windows en Python/PySide6 pour preparer un PDF final a partir de plusieurs PDF importes.

Version actuelle : `v2.0.0`.

## Fonctionnalites V1

- Import de PDF, documents Word (`.doc`/`.docx`), JPG et PNG par bouton ou glisser-deposer.
- Import direct des pieces jointes Gmail depuis le navigateur dans la zone jaune integree a MultiPrep.
- Mode Gmail actif par defaut avec une identite visuelle blanc/jaune et des consignes integrees.
- Bascule vers le mode classique depuis l'en-tete de l'application.
- Collage d'une capture d'ecran avec `Ctrl + V` ou clic droit puis `Coller`.
- Affichage des pages en miniatures dans un espace principal.
- Reorganisation des pages par glisser-deposer entre les emplacements.
- Selection multiple avec `Shift` pour une plage et `Ctrl` pour ajouter/enlever une page.
- Reorganisation des pages selectionnees par glisser-deposer entre les emplacements.
- Pendant le glisser-deposer, un ghost et un indicateur d'insertion montrent la position cible.
- Suppression d'une page, de la selection, ou de toutes les pages avec `Suppr` / `Delete` ou clic droit.
- Couleur de bordure commune pour les pages provenant du meme PDF.
- Insertion d'un separateur avant/apres une page via clic droit.
- Separateurs charges depuis le dossier local `separateurs/`.
- Fenetre de recherche et selection des separateurs.
- Champs `Nom`, `Prenom`, date `JJ / MM / AAAA`, suffixe `P`.
- Memorisation de la derniere date dans `settings.json`.
- Fusion dans l'ordre affiche avec export au format `AAAA-MM-JJ_NOM-Prenom_P.pdf`.
- Ecran resultat avec fichier PDF draggable vers une autre application Windows.

## Choix technique pour la grille

La grille utilise `QListWidget` en `IconMode` avec un delegate graphique leger : les cartes sont dessinees a la demande sans creer un widget complet par page.
Les miniatures sont generees hors du thread graphique, par lots paralleles, puis mises en cache. L'ajout de nouveaux documents est incremental et ne reconstruit pas les pages deja presentes.
Le drag interne conserve la selection multiple, le placeholder de position cible, la restauration en cas d'annulation et la recuperation de l'ordre final via `get_ordered_pages()`.

## Structure du code

Fichiers a lire en premier :

- `run.py` : lance l'application.
- `multiprep/ui/main_window.py` : initialise la fenetre principale.
- `multiprep/ui/main_window_actions.py` : actions utilisateur principales.
- `multiprep/ui/page_board.py` : conteneur de la grille et menu clic droit.
- `multiprep/ui/page_grid_list.py` : liste draggable avec placeholder.
- `multiprep/ui/page_card_delegate.py` : rendu leger des cartes sans widget par page.
- `multiprep/services/pdf_service.py` : import PDF, captures, separateurs et fusion.
- `multiprep/services/thumbnail_service.py` : miniatures differees, groupees et parallelisees.

Dossiers :

- `multiprep/ui/` : composants visuels PySide6.
- `multiprep/services/` : logique metier sans interface.
- `multiprep/models/` : donnees partagees.
- `multiprep/utils/` : chemins et constantes utilitaires.

## Installation

Prerequis : Python 3.10 ou plus recent.

Les versions de `PyMuPDF` et `pypdf` sont epinglees dans `requirements.txt` afin de rendre les installations reproductibles :

```text
PyMuPDF==1.26.7
pypdf==6.10.2
```

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

L'import Word utilise Microsoft Word installe sur le poste pour convertir le document en PDF tout en conservant sa mise en page.

Pour une piece jointe Gmail ouverte dans le navigateur, glissez-la directement dans la zone jaune du mode Gmail. Cette zone integree utilise le transfert asynchrone Windows du navigateur, y compris pour les PDF et documents Word. Aucune fenetre supplementaire ne s'ouvre.

Le navigateur ne remet pas toujours le contenu des images inserees directement dans le corps d'un message. Pour celles-ci, copiez l'image depuis Gmail puis utilisez `Ctrl+V` dans MultiPrep.

## Lancement

```powershell
python run.py
```

## Separateurs

Placez vos PDF de separation dans le dossier :

```text
separateurs/
```

Le dossier est cree automatiquement au premier usage si absent.

## Export

Les fichiers générés sont placés dans :

```text
exports/
```

Si un fichier du meme nom existe deja, il est ecrase lors de la generation.

## Fichiers temporaires

MultiPrep cree un dossier local `temp/` a cote de l'application.

```text
temp/
+-- cache/
+-- mail_attachments/
```

Ce dossier contient les miniatures, captures collees et pieces jointes Outlook extraites temporairement.
Il est nettoye au lancement et a la fermeture normale de l'application.
