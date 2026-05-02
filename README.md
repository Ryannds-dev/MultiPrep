# MultiPrep

Application desktop Windows en Python/PySide6 pour preparer un PDF final a partir de plusieurs PDF importes.

## Fonctionnalites V1

- Import de PDF par bouton ou glisser-deposer.
- Affichage des pages en miniatures dans un espace principal.
- Reorganisation des pages par glisser-deposer entre les emplacements.
- Selection multiple avec `Shift` pour une plage et `Ctrl` pour ajouter/enlever une page.
- Reorganisation des pages selectionnees par glisser-deposer entre les emplacements.
- Pendant le glisser-deposer, la zone d'arrivee s'allume et affiche `DEPOSER ICI`.
- Suppression d'une page, de la selection, ou de toutes les pages avec `Suppr` / `Delete` ou clic droit.
- Couleur de bordure commune pour les pages provenant du meme PDF.
- Bouton `+` entre les pages pour inserer un separateur.
- Separateurs charges depuis le dossier local `separateurs/`.
- Fenetre de recherche et selection des separateurs.
- Champs `Nom`, `Prenom`, date `JJ / MM / AAAA`, suffixe `P`.
- Memorisation de la derniere date dans `settings.json`.
- Fusion dans l'ordre affiche avec export au format `AAAA-MM-JJ_NOM-Prenom_P.pdf`.
- Ecran resultat avec fichier PDF draggable vers une autre application Windows.

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

Les fichiers generes sont places dans :

```text
exports/
```

Si un fichier du meme nom existe deja, il est ecrase lors de la generation.
