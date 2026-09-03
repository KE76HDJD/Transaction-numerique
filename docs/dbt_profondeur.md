# dbt en profondeur — Pourquoi c'est essentiel pour un Data Engineer

---

## 1. Le problème que dbt résout

### 1.1 Le chaos du code de transformation

**Avant dbt :**
```python
# transform.py — 500 lignes de Python
def transform_data():
    df = pd.read_csv("data.csv")
    df["date"] = pd.to_datetime(df["step"])
    df["amount_clean"] = df["amount"].fillna(0)
    df["is_fraud"] = df["is_fraud"].astype(int)
    # ... 200 lignes de plus ...
    df.to_sql("transactions_clean", engine)
```

**Problèmes :**
- Personne ne comprend ce que fait le script sans le lire entièrement
- Pas de tests intégrés
- Pas de documentation
- Si quelqu'un modifie une ligne, cassera-t-il autre chose ?
- Comment savoir quelles données dépendent de quoi ?

### 1.2 La solution dbt

**Avec dbt :**
```sql
-- stg_transactions.sql — 15 lignes de SQL
with source as (
    select * from {{ source('raw', 'transactions') }}
),
cleaned as (
    select
        id,
        step,
        type,
        amount,
        is_fraud
    from source
    where amount > 0
)
select * from cleaned
```

**Avantages :**
- Tout le monde lit le SQL (c'est la langue commune)
- Les tests sont dans le même fichier
- La documentation est générée automatiquement
- Le lineage montre les dépendances

---

## 2. Ce que dbt fait VRAIMENT

### 2.1 dbt n'est PAS un ETL

```
ETL = Extract + Transform + Load
     │         │         │
     │         │         └──► dbt ne fait PAS ça
     │         └──► dbt fait ça (TRANSFORM uniquement)
     └──► Autre outil fait ça (ingestion)
```

**dbt = "T" dans ELT**

```
ELT = Extract + Load + Transform
      │        │       │
      │        │       └──► dbt fait ça
      │        └──► Outil d'ingestion fait ça (Fivetran, Airbyte, script Python)
      └──► Source de données
```

### 2.2 Le mécanisme concret

```
1. Tu écris un fichier SQL (modèle)
2. dbt lit le fichier
3. dbt le transforme en requête SQL complète (en remplaçant {{ ref('...') }})
4. dbt exécute la requête sur PostgreSQL
5. dbt crée une vue ou une table
6. dbt teste les résultats
```

**Exemple concret :**

```sql
-- Tu écris :
select * from {{ ref('stg_transactions') }}

-- dbt génère :
select * from public_staging.stg_transactions
```

### 2.3 Les 3 types de materialisation

| Type | Ce que ça crée | Quand l'utiliser |
|------|----------------|------------------|
| **view** | Vue SQL (pas de données stockées) | Staging, données temporaires |
| **table** | Table physique avec données | Marts, données finales |
| **ephemeral** | CTE (Common Table Expression) | Intermediate, données intermédiaires |

---

## 3. Le pattern staging → intermediate → marts

### 3.1 Pourquoi ce pattern ?

C'est le **pipeline de nettoyage** des données :

```
STAGING (données brutes)
│  "Qu'est-ce qu'on a ?"
│  - Renommer les colonnes
│  - Filtrer les doublons
│  - Valider les types
│
INTERMEDIATE (transformations métier)
│  "Qu'est-ce qu'on peut en tirer ?"
│  - Agrégations
│  - Calculs
│  - Jointures
│
MARTS (données business-ready)
│  "Qu'est-ce que le business veut ?"
│  - Tables prêtes pour l'analyse
│  - Dashboard
│  - Reporting
```

### 3.2 Analogie avec la cuisine

```
STAGING = Les ingrédients bruts
│  Tomates, oignons, ail
│  (pas encore transformés)
│
INTERMEDIATE = La préparation
│  Tomates coupées, oignons émincés, ail pressé
│  (transformés mais pas encore un plat)
│
MARTS = Le plat servi
│  Ratatouille prête à manger
│  (le business peut consommer)
```

---

## 4. L'importance pour un Data Engineer

### 4.1 Ce qu'un Data Engineer fait

```
Data Engineer = "Celui qui construit les tuyaux"
│
├── Ingestion : amener les données de A à B
├── Transformation : nettoyer, agréger, enrichir
├── Stockage : organiser les données en base
├── Qualité : s'assurer que les données sont correctes
└── Monitoring : vérifier que tout fonctionne
```

### 4.2 Comment dbt s'intègre

```
Data Engineer
│
├── Ingestion → Fivetran, Airbyte, script Python (V1)
├── Transformation → dbt (V2)
├── Orchestration → Airflow (V3)
├── Monitoring → Prometheus/Grafana (V5)
└── Qualité → Great Expectations (V5)
```

**dbt est la pièce centrale de la transformation.**

### 4.3 Les problèmes que dbt résout au quotidien

| Problème | Sans dbt | Avec dbt |
|----------|----------|----------|
| "Qui a modifié cette requête ?" | Chercher dans git log | `git diff models/` |
| "Qu'est-ce qui dépend de cette table ?" | Lire tout le code | `dbt docs serve` → lineage |
| "Est-ce que les données sont correctes ?" | Écrire des tests manuels | `dbt test` automatique |
| "Comment documenter le pipeline ?" | Faire un README à la main | `dbt docs generate` automatique |
| "Rejouer le pipeline ?" | Relancer le script Python | `dbt run` (idempotent) |

---

## 5. Les concepts clés à maîtriser

### 5.1 Jinja Templates

dbt utilise Jinja (moteur de template) pour générer du SQL dynamique :

```sql
-- ref() : référence un autre modèle
select * from {{ ref('stg_transactions') }}

-- source() : référence une source brute
select * from {{ source('raw', 'transactions') }}

-- var() : variables configurables
select * from {{ var('start_date') }}
```

### 5.2 Tests intégrés

```yaml
# schema.yml
models:
  - name: stg_transactions
    columns:
      - name: id
        tests:
          - unique        # Chaque ID est unique
          - not_null      # Pas de nuls
      - name: type
        tests:
          - accepted_values:
              values: ['PAYMENT', 'TRANSFER']
```

### 5.3 Lineage (Lignée)

```
dbt docs generate → page web interactive
│
├── Montre quel modèle dépend de quel autre
├── Montre les colonnes utilisées
├── Montre les tests associés
└── Permet de naviguer visuellement
```

### 5.4 Incrémental models

```sql
-- Modèle incrémental (n'ajoute que les nouvelles données)
{{ config(materialized='incremental') }}

select *
from {{ ref('stg_transactions') }}

{% if is_incremental() %}
  where created_at > (select max(created_at) from {{ this }})
{% endif %}
```

---

## 6. Cas réels d'utilisation

### 6.1 E-commerce

```
Sources : Shopify, Stripe, Google Analytics
    │
    ▼
dbt models :
├── stg_orders : nettoyage des commandes
├── stg_payments : nettoyage des paiements
├── int_revenue : calcul du revenu
└── mart_sales_dashboard : tableau de bord ventes
```

### 6.2 Fintech

```
Sources : Transactions bancaires, KYC, Compliance
    │
    ▼
dbt models :
├── stg_transactions : nettoyage
├── int_fraud_detection : détection de fraude
├── int_kyc_verification : vérification identité
└── mart_compliance : rapport réglementaire
```

### 6.3 SaaS

```
Sources : Stripe, Intercom, Segment
    │
    ▼
dbt models :
├── stg_subscriptions : abonnements
├── stg_events : événements utilisateurs
├── int_churn_prediction : prédiction de churn
└── mart_mrr : Monthly Recurring Revenue
```

---

## 7. Les erreurs courantes

### 7.1 Utiliser dbt pour l'ingestion

```
❌ FAUX : dbt pour lire des CSV
✅ VRAI : dbt pour transformer des données déjà en base
```

### 7.2 Tout mettre dans un seul modèle

```
❌ FAUX : un seul fichier de 500 lignes
✅ VRAI : plusieurs modèles pequeuns et ciblés
```

### 7.3 Ne pas tester

```
❌ FAUX : écrire des modèles sans tests
✅ VRAI : chaque colonne importante a un test
```

### 7.4 Ignorer le lineage

```
❌ FAUX : ne pas consulter dbt docs
✅ VRAI : consulter le lineage avant de modifier un modèle
```

---

## 8. dbt vs alternatives

| Outil | Type | Différence avec dbt |
|-------|------|---------------------|
| **Python pandas** | Script | dbt = SQL pur, versionné, testé |
| **Spark** | Moteur distribué | dbt = léger, SQL, pas de cluster |
| **dbt** | Transform SQL | Le standard de l'industrie |
| **SQLMesh** | Alternative dbt | Plus récent, moins de communauté |
| **Dataform** | Alternative dbt | Google, moins populaire |

---

## 9. Les commandes essentielles

```bash
# Vérifier la connexion
dbt debug

# Exécuter tous les modèles
dbt run

# Exécuter un seul modèle
dbt run --select stg_transactions

# Tester tous les modèles
dbt test

# Tester un seul modèle
dbt test --select mart_transactions

# Générer la documentation
dbt docs generate

# Servir la documentation
dbt docs serve

# Nettoyer
dbt clean

# Voir le SQL généré
dbt compile
```

---

## 10. Résumé — Pourquoi dbt est essentiel

```
Un Data Engineer SANS dbt :
├── Écrit du Python pour transformer
├── Pas de tests intégrés
├── Documentation manuelle
├── Pas de lineage
└── Difficile à maintenir

Un Data Engineer AVEC dbt :
├── Écrit du SQL pour transformer
├── Tests intégrés automatiquement
├── Documentation générée automatiquement
├── Lineage visuel
└── Facile à maintenir et collaborer
```

**dbt n'est pas un outil optionnel — c'est le standard de l'industrie pour la transformation de données.**

---

*Document généré pour le projet Transaction Data Platform*
*V2 — dbt (Transformation as Code)*
