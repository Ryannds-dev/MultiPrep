# MultiPrep

Application desktop Windows en Python/PySide6 pour preparer un PDF final a partir de plusieurs PDF importes.

## Fonctionnalites V1

- Import de PDF, JPG et PNG par bouton ou glisser-deposer.
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

La grille de pages utilise `QListWidget` en `IconMode` avec un drag interne personnalise.
Ce choix garde une implementation robuste PySide6 avec selection multiple, ghost de drag, placeholder de position cible pendant le mouvement, restauration si le drag est annule et recuperation de l'ordre final via `get_ordered_pages()`.
Pour garder le deplacement fluide, la grille ne reconstruit pas toutes les miniatures au debut du drag : elle retire uniquement les pages selectionnees, deplace un placeholder, puis reconstruit l'affichage final une seule fois au drop.

## Structure du code

Fichiers a lire en premier :

- `run.py` : lance l'application.
- `multiprep/ui/main_window.py` : initialise la fenetre principale.
- `multiprep/ui/main_window_actions.py` : actions utilisateur principales.
- `multiprep/ui/page_board.py` : conteneur de la grille et menu clic droit.
- `multiprep/ui/page_grid_list.py` : liste draggable avec placeholder.
- `multiprep/services/pdf_service.py` : import PDF, captures, separateurs et fusion.

Dossiers :

- `multiprep/ui/` : composants visuels PySide6.
- `multiprep/services/` : logique metier sans interface.
- `multiprep/models/` : donnees partagees.
- `multiprep/utils/` : chemins et constantes utilitaires.

## Installation

Prerequis : Python 3.11 ou plus recent.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

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
