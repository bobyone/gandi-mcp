<!--
SPDX-FileCopyrightText: 2026 bobyone
SPDX-License-Identifier: GPL-2.0-or-later
-->

# Politique de confidentialité (projet)

> Projet à faire valider par un professionnel du droit ; ne constitue pas un
> conseil juridique. Version 0.2 du 26 novembre 2026. **Cette version
> française fait foi** ; les autres langues en sont des traductions. Elle sera
> accessible depuis l'interface de la MCP App.
>
> Il n'y a pas de conditions générales d'utilisation : l'usage du logiciel est
> régi par sa licence, `GPL-2.0-or-later`.

## Qui traite vos données

`gandi-mcp` est un logiciel libre qui s'exécute sur votre propre ordinateur.
Ses auteurs ne collectent, ne reçoivent et ne conservent aucune de vos
données. Lorsque vous l'utilisez, vous (ou votre organisation) restez
responsable des données que vous traitez avec lui.

## Ce que le logiciel traite

- **Vos Personal Access Tokens Gandi** : conservés dans le trousseau de votre
  système d'exploitation, envoyés uniquement à l'API Gandi, jamais montrés au
  modèle d'IA. Vous les saisissez dans l'application ou sur une page
  temporaire de votre propre ordinateur, jamais dans la conversation.
- **Les réglages de vos comptes** (le nom que vous donnez à chaque compte, son
  environnement, son éventuelle lecture seule, le compte par défaut) :
  conservés dans un fichier de préférences sur votre ordinateur, sans aucun
  secret, et transmis au modèle d'IA lorsqu'il liste vos comptes.
- **L'identité Gandi associée à un jeton** (nom d'utilisateur et nom complet) :
  lue auprès de Gandi lorsque vous enregistrez un jeton, affichée pour vous,
  jamais conservée.
- **Vos données Gandi** (domaines et leurs contacts, enregistrements DNS,
  boîtes mail, certificats, hébergements, factures) : lues auprès de Gandi
  lorsqu'un outil en a besoin, conservées en mémoire uniquement, jamais
  écrites sur disque par le logiciel.

## Qui les reçoit

- **Gandi**, pour effectuer les opérations que vous demandez.
- **Le fournisseur de votre assistant d'IA** (par exemple Anthropic ou
  OpenAI) : les résultats des outils sont transmis au modèle que vous
  utilisez. Leur traitement relève de la politique de confidentialité de ce
  fournisseur et des réglages de votre client.

## Vos droits

Le logiciel ne conserve aucune copie de vos données Gandi. Pour supprimer un
jeton et les réglages de son compte, supprimez le compte dans le logiciel : il
efface les deux.
Exercez vos droits sur les données détenues par Gandi ou par votre
fournisseur d'IA directement auprès d'eux.

## Contact

Pour toute question sur cette politique : ouvrez une issue sur
<https://github.com/bobyone/gandi-mcp/issues>.
