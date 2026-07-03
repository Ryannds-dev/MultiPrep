# Historique des évolutions de MultiPrep

Ce document explique les commits du projet dans l’ordre chronologique. Il précise le besoin ou le problème rencontré, la solution apportée et son effet concret.

## 3 juillet 2026 — MultiPrep 2.0.0, Google Workspace et performances

### Passage de la version Outlook à la version Google Workspace

- **Besoin :** utiliser principalement MultiPrep avec Gmail dans un navigateur, alors que le glisser-déposer historique avait été conçu pour Outlook bureau.
- **Difficulté :** Gmail transmet certaines pièces jointes comme des objets virtuels Windows et non comme des chemins de fichiers. Qt ne sait pas toujours terminer seul le transfert asynchrone fourni par le navigateur.
- **Solution :** ajout d’un composant Windows natif intégré directement dans la grande zone de MultiPrep. Il récupère les flux virtuels du navigateur, les copie dans le dossier temporaire puis les remet au moteur d’import existant.
- **Résultat :** les PDF, images et documents Word provenant de Gmail peuvent être déposés dans MultiPrep sans fenêtre d’import séparée. Le composant reste disponible en arrière-plan et se réactive pour plusieurs imports successifs.

### Collage des images présentes dans le corps d’un mail

- **Problème réglé :** la couche native Gmail interceptait `Ctrl+V` et le clic droit avant l’interface Qt ; de plus, Gmail peut copier une image sous forme de bitmap, de HTML, de données Base64 ou d’URL.
- **Solution :** gestion de `Ctrl+V` et du menu **Coller** dans les deux couches de l’application, avec lecture des formats image Windows/Qt, HTML, Base64 et URL distante.
- **Résultat :** une image copiée depuis le corps d’un message Gmail peut être ajoutée au montage, que la grille soit vide ou contienne déjà des pages.

### Import Word et identité MultiPrep 2.0.0

- **Besoin :** accepter les documents `.doc` et `.docx` en plus des PDF et images.
- **Solution :** conversion locale via Microsoft Word en conservant la mise en page, puis intégration du PDF produit dans le même flux que les autres documents.
- **Résultat :** les documents Word sont importables par le bouton, le glisser-déposer local ou Gmail.
- **Identité visuelle :** création du mode Gmail blanc/jaune actif par défaut, conservation du mode classique bleu, logos distincts et version applicative portée à `2.0.0`.

### Refonte complète des performances d’import

- **Problème réglé :** chaque page créait auparavant un widget Qt complet et sa miniature était calculée pendant le chargement. Le temps, la mémoire et les ralentissements augmentaient fortement avec le nombre de pages.
- **Première difficulté :** déplacer uniquement le calcul des miniatures dans un thread rendait la fenêtre plus réactive, mais la création de centaines de widgets restait coûteuse.
- **Solution finale :**
  - création immédiate des modèles de pages sans calculer leurs aperçus ;
  - remplacement des widgets individuels par un delegate graphique léger qui dessine les cartes à la demande ;
  - calcul des miniatures hors du thread graphique, par lots et avec jusqu’à quatre traitements parallèles ;
  - ouverture groupée des PDF afin de ne pas rouvrir le même document pour chaque page ;
  - ajout incrémental des nouvelles pages sans reconstruire toute la grille ;
  - suppression des parcours complets de la grille lors d’une sélection ou d’un changement de thème ;
  - génération différée des miniatures des images collées/importées.
- **Mesures de validation :** environ 10 à 12 ms pour injecter 500 pages dans la grille et environ 0,63 seconde pour générer 120 miniatures sur le poste de développement.
- **Résultat :** les modes classique et Gmail partagent désormais le même moteur rapide ; l’interface reste utilisable pendant la production des aperçus.

## 2 mai 2026 — Création du socle

### `44e43b0` — Ajout du flux d’assemblage PDF et normalisation des noms

- **Besoin :** préparer un dossier PDF unique à partir de plusieurs documents et produire un nom de fichier homogène.
- **Solution :** création de l’application PySide6, des modèles de pages, du service PDF, des réglages de date et de l’interface principale.
- **Résultat :** l’utilisateur peut importer des PDF, organiser leurs pages, ajouter des séparateurs et générer un fichier final nommé selon les informations du dossier.

### `e7f6f62` — Import des pièces jointes Outlook par glisser-déposer

- **Problème réglé :** une pièce jointe glissée depuis Outlook n’est pas un fichier local classique. Windows la transmet comme un fichier virtuel avec un nom et un contenu séparés.
- **Solution :** lecture des formats Windows `FileGroupDescriptor` et `FileContents`, puis copie temporaire de la pièce jointe avant son import.
- **Résultat :** les PDF peuvent être déposés directement depuis Outlook bureau dans MultiPrep.

## 3 mai 2026 — Ergonomie des pages et captures

### `0136f11` — Indicateur de réorganisation et insertion contextuelle des séparateurs

- **Problème réglé :** la destination d’une page déplacée était difficile à anticiper et l’ajout d’un séparateur manquait de précision.
- **Solution :** ajout d’un emplacement visuel pendant le déplacement et d’actions permettant d’insérer un séparateur avant ou après une page.
- **Résultat :** la composition du document devient plus lisible et plus rapide.

### `4724610` — Collage d’images et amélioration des libellés

- **Besoin :** intégrer une capture présente dans un mail sans devoir l’enregistrer manuellement.
- **Solution :** prise en charge de `Ctrl+V` et du menu Coller, conversion de l’image du presse-papiers en page PDF et amélioration du contraste des libellés.
- **Résultat :** une capture copiée depuis un message peut être ajoutée directement au montage.

### `592679c` — Correction de l’icône de l’exécutable

- **Problème réglé :** l’icône de l’application n’était pas correctement appliquée dans la version Windows produite par PyInstaller.
- **Solution :** ajout de la configuration PyInstaller et intégration explicite de l’icône.
- **Résultat :** l’exécutable distribué possède l’identité visuelle de MultiPrep.

### `a283e06` — Découpage de l’application en modules

- **Problème réglé :** la fenêtre, la logique PDF et la grille étaient regroupées dans de gros fichiers difficiles à maintenir.
- **Solution :** séparation en dossiers `ui`, `services`, `models` et `utils`, avec des responsabilités mieux isolées.
- **Résultat :** les évolutions et corrections ultérieures peuvent être apportées plus sûrement, sans modifier toute l’application.

## 6 mai 2026 — Formats d’image, aperçu et rotation

### `e160b5d` — Fichiers temporaires locaux, JPG/PNG et noms Outlook nettoyés

- **Problèmes réglés :** les images ne pouvaient pas être importées comme documents, les fichiers temporaires étaient moins faciles à localiser et certains noms Outlook contenaient des chemins ou caractères indésirables.
- **Solution :** ajout de l’import JPG/PNG, centralisation du cache dans `temp/`, sécurisation des noms de pièces jointes et amélioration des libellés de miniatures.
- **Résultat :** MultiPrep accepte davantage de sources et gère plus proprement ses fichiers intermédiaires.

### `33cace2` — Aperçu haute résolution redimensionnable

- **Besoin :** vérifier le contenu d’une page sans ouvrir le document d’origine.
- **Solution :** ajout d’un panneau d’aperçu détaillé qui suit la page sélectionnée et peut être redimensionné.
- **Résultat :** le contrôle du montage peut être effectué directement dans l’application.

### `f74f3d2` — Rotation individuelle des pages

- **Problème réglé :** une page scannée dans le mauvais sens restait incorrecte dans le PDF exporté.
- **Solution :** ajout des rotations gauche/droite dans l’interface, affichage immédiat dans l’aperçu et application de la rotation lors de la fusion.
- **Résultat :** l’orientation peut être corrigée page par page avant l’export.

### `dbedc05` — Reconstruction de l’exécutable avec aperçu et rotation

- **But :** rendre les deux fonctionnalités précédentes disponibles dans la version Windows distribuée.
- **Résultat :** aucun changement métier supplémentaire ; l’exécutable est synchronisé avec le code source.

## 7 mai 2026 — Nettoyage du lancement

### `3258e6f` — Suppression d’un point d’entrée redondant

- **Problème réglé :** deux fichiers pouvaient lancer l’application, ce qui créait une ambiguïté pour le développement et la compilation.
- **Solution :** conservation de `run.py` comme point d’entrée unique, mise à jour des prérequis et reconstruction de l’exécutable.
- **Résultat :** le lancement et la procédure de build sont plus simples.

## 8 mai 2026 — Documentation technique locale

### `bb81680` — Ajout du site de documentation technique

- **Besoin :** comprendre rapidement l’architecture et le rôle des différents fichiers.
- **Solution :** création d’une documentation HTML locale et retrait des fichiers intermédiaires PyInstaller du suivi Git.
- **Résultat :** le projet est plus facile à reprendre et le dépôt contient moins de déchets de compilation.

## 10 mai 2026 — Documentation, fluidité et distribution

### `55b4f75` — Mise à jour des spécifications et nettoyage

- **Problème réglé :** des caches Python compilés et du code devenu inutile encombraient encore le dépôt.
- **Solution :** suppression des `__pycache__`, simplification de certains éléments et ajout des spécifications aux formats PDF et Word.
- **Résultat :** le dépôt est plus propre et sa documentation correspond mieux à l’application.

### `fad3e43` — Reconstruction de l’exécutable

- **But :** publier une version Windows alignée sur le code et la documentation nettoyés.
- **Résultat :** changement de distribution uniquement.

### `d149cf7` — Fluidification du déplacement des miniatures

- **Problème réglé :** la grille reconstruisait trop souvent ses éléments pendant un glisser-déposer, ce qui rendait le mouvement saccadé.
- **Solution :** déplacement léger d’un emplacement temporaire, puis reconstruction unique de la grille à la fin.
- **Résultat :** la réorganisation, y compris de plusieurs pages, est nettement plus fluide.

### `fddef3a` — Ajout des séparateurs à la distribution

- **Problème réglé :** l’exécutable seul ne suffisait pas si les PDF de séparation n’étaient pas copiés avec lui.
- **Solution :** ajout du dossier `dist/separateurs` à la version distribuée et suppression d’un ancien export de test.
- **Résultat :** le paquet Windows est immédiatement utilisable avec les séparateurs prévus.

## 1er juin 2026 — Stabilisation de la version 1.1.1

### `e1751f1` — Verrouillage des versions PDF

- **Problème réglé :** installer automatiquement les versions les plus récentes de PyMuPDF ou pypdf pouvait introduire une incompatibilité imprévisible.
- **Solution :** fixation de `PyMuPDF==1.26.7` et `pypdf==6.10.2`.
- **Résultat :** les installations et les builds deviennent reproductibles.

### `a1c527f` — Documentation des dépendances de la version 1.1.1

- **But :** expliquer les versions retenues et aligner la documentation, les spécifications et le numéro de version.
- **Résultat :** la procédure d’installation de la version 1.1.1 est explicite.

### `1d9fc11` — Reconstruction de l’exécutable 1.1.1

- **But :** produire l’exécutable avec les dépendances stabilisées.
- **Résultat :** la version distribuée correspond à la version 1.1.1 documentée.

### `d5d6e84` — Alignement du prérequis Python

- **Problème réglé :** la version de Python annoncée dans la documentation ne correspondait pas exactement à l’environnement utilisé pour construire l’application.
- **Solution :** correction du prérequis dans le README et les spécifications.
- **Résultat :** les indications d’installation correspondent à la réalité du build.

## 3 juillet 2026 — Compatibilité Google Workspace

### Correctif préparé avec ce document

- **Problème réglé :** Gmail et les navigateurs Chromium ne transmettent pas toujours un chemin de fichier comme Outlook ou le Bureau. Une pièce jointe peut être fournie via `DownloadURL` et une image du message via des données Qt, un type `image/png`/`image/jpeg` ou du HTML encodé.
- **Solution :** généralisation du service de dépôt pour reconnaître les fichiers virtuels Chromium, les images directes, les données d’image brutes et les images HTML intégrées, tout en conservant les chemins Outlook et fichiers locaux existants.
- **Sécurité :** MultiPrep n’essaie pas de télécharger arbitrairement une URL Gmail protégée avec les identifiants du navigateur ; il utilise uniquement le contenu réellement fourni lors du dépôt.
- **Validation :** cinq tests couvrent les fichiers locaux, les images Qt, les images HTML, les pièces jointes Chromium et la compatibilité Outlook.
- **Résultat :** le glisser-déposer est adapté au passage d’Outlook bureau vers Google Workspace dans les formats que le navigateur remet réellement à l’application.

## Repères

- Les commits `feat` ajoutent une fonctionnalité.
- Les commits `fix` corrigent un dysfonctionnement.
- Les commits `perf` améliorent les performances sans changer le résultat attendu.
- Les commits `refactor` réorganisent le code pour faciliter sa maintenance.
- Les commits `docs` modifient la documentation.
- Les commits `build` reconstruisent ou complètent la version Windows distribuée.
- Les commits `chore` effectuent un entretien technique.

## Évolution préparée — MultiPrep 2.0.0

- **Changement de flux :** le mode Gmail devient le mode de démarrage et présente directement les deux parcours adaptés à Google Workspace : dépôt des pièces jointes et collage des images présentes dans le corps du message.
- **Compatibilité :** une zone Windows native gère le transfert asynchrone utilisé par Microsoft Edge et les navigateurs compatibles pour les pièces jointes Gmail.
- **Mode classique :** un bouton dans l’en-tête permet de retrouver instantanément l’interface et le parcours d’import traditionnels.
- **Nouvelle identité :** palette blanc chaud et jaune doré, composants visuels modernisés et nouveau logo MP conservant le symbole historique des documents assemblés.
- **Formats :** ajout de l’import Word `.doc` et `.docx`, converti en PDF par Microsoft Word avant intégration au montage.
