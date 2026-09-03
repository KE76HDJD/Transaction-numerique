# Analyse du Dataset de Transactions

## Source

Fichier : `data/source/PS_20174392719_1491204439457_log.csv`

## Volume

| Métrique | Valeur |
|----------|--------|
| Nombre de lignes | 6 362 620 |
| Nombre de colonnes | 11 |
| Steps uniques | 743 (≈ 31 jours) |

## Structure du dataset

| Colonne | Type | Description |
|---------|------|-------------|
| step | int64 | Unité de temps (1 step = 1 heure) |
| type | str | Type de transaction |
| amount | float64 | Montant de la transaction |
| nameOrig | str | Identifiant du client émetteur |
| oldbalanceOrg | float64 | Solde avant transaction (émetteur) |
| newbalanceOrig | float64 | Solde après transaction (émetteur) |
| nameDest | str | Identifiant du destinataire |
| oldbalanceDest | float64 | Solde avant transaction (destinataire) |
| newbalanceDest | float64 | Solde après transaction (destinataire) |
| isFraud | int64 | 1 si fraude, 0 sinon |
| isFlaggedFraud | int64 | 1 si transaction suspecte, 0 sinon |

## Qualité des données

| Critère | Résultat |
|---------|----------|
| Valeurs manquantes | Aucune |
| Doublons | Aucun |

## Types de transactions

| Type | Nombre | Pourcentage |
|------|--------|-------------|
| CASH_OUT | 2 237 500 | 35,2% |
| PAYMENT | 2 151 495 | 33,8% |
| CASH_IN | 1 399 284 | 22,0% |
| TRANSFER | 532 909 | 8,4% |
| DEBIT | 41 432 | 0,7% |

## Montants

| Métrique | Valeur |
|----------|--------|
| Minimum | 0,00 |
| Maximum | 92 445 516,64 |
| Moyenne | 179 861,90 |
| Médiane | 74 871,94 |

### Montants par type

| Type | Moyenne | Maximum |
|------|---------|---------|
| PAYMENT | 13 057,60 | 238 637,98 |
| TRANSFER | 910 647,01 | 92 445 516,64 |
| CASH_OUT | 176 273,96 | 10 000 000,00 |
| DEBIT | 5 483,67 | 569 077,51 |
| CASH_IN | 168 920,24 | 1 915 267,90 |

## Fraudes

| Catégorie | Nombre | Pourcentage |
|-----------|--------|-------------|
| Non-fraude | 6 354 407 | 99,87% |
| Fraude | 8 213 | 0,13% |

## Conversion step → temps réel

- Step 1 = Heure 1 du Jour 1
- Step 24 = Dernière heure du Jour 1
- Step 25 = Première heure du Jour 2
- Step 743 = Dernière heure du Jour 31

**Convention** : Date de référence = 2024-01-01 00:00:00

## Conclusions

1. Dataset **propre** : aucune valeur manquante, aucun doublon
2. **31 jours** de données, couvrant ~6,3 millions de transactions
3. Taux de fraude réaliste : **0,13%**
4. Les montants varient fortement selon le type de transaction
5. Idéal pour un pipeline batch avec découpage journalier
