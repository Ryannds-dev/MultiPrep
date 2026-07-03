<p align="center">
  <img src="https://raw.githubusercontent.com/Ryannds-dev/MultiPrep/master/assets/multiprep-logo-2.png" alt="Logo MultiPrep 2.0.0" width="180">
</p>

# MultiPrep 2.0.0 — Google Workspace

MultiPrep 2.0.0 est une évolution majeure pensée pour accompagner le passage des applications de bureau à Google Workspace. Le mode Gmail devient l’expérience par défaut, sans supprimer le mode classique ni la compatibilité avec Outlook bureau.

## Nouveautés principales

### Gmail directement dans MultiPrep

- glisser-déposer des pièces jointes Gmail depuis un navigateur ;
- prise en charge des PDF, documents Word, JPG et PNG ;
- récupération native des fichiers virtuels et transferts asynchrones Windows ;
- imports successifs sans redémarrer l’application ;
- aucune fenêtre d’import séparée ;
- compatibilité avec les navigateurs Windows utilisant ces mécanismes, sans dépendance à Google Chrome.

### Images dans le corps des mails

- copie d’une image affichée dans le corps du message Gmail ;
- collage avec `Ctrl+V` ou clic droit → **Coller** ;
- prise en charge des bitmaps, images Qt, HTML/Base64 et URL d’image ;
- collage possible lorsque la grille est vide ou contient déjà des pages.

### Mode classique conservé

- import depuis l’Explorateur Windows et le Bureau ;
- import depuis les applications de bureau exposant un vrai fichier, dont Outlook bureau ;
- Outlook reste une source compatible parmi d’autres.

### Word et performances

- import des fichiers `.doc` et `.docx` via Microsoft Word ;
- grille légère sans widget complet par page ;
- miniatures générées en arrière-plan et par lots parallèles ;
- ajout incrémental des nouveaux documents ;
- référence mesurée : 500 pages injectées en 10–12 ms et 120 miniatures en environ 0,63 seconde sur le poste de développement.

## Identité visuelle

- nouvelle identité Google Workspace blanche et jaune `#F9AB00` ;
- nouveau logo MultiPrep 2.0.0 ;
- mode classique bleu historique conservé ;
- version 2.0.0 affichée dans l’interface, les documentations et les propriétés Windows de l’exécutable.

## Assets

- `MultiPrep.exe` : exécutable Windows autonome ;
- `MultiPrep-2.0.0-Windows.zip` : distribution complète avec les séparateurs ;
- `Specifications-techniques-MultiPrep-2.0.0.pdf` : spécifications techniques ;
- `multiprep-logo-2.png` : logo officiel 2.0.0.

## Prérequis

- Windows 10 ou Windows 11 ;
- Microsoft Word installé uniquement pour importer les fichiers `.doc` et `.docx`.

## Validation

- 8 tests automatisés réussis ;
- 77 PDF et 78 pages vérifiés ;
- 38 séparateurs synchronisés entre la source et la distribution ;
- métadonnées Windows `FileVersion` et `ProductVersion` définies à `2.0.0`.
