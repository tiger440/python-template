# groundcite — Compagnon ML

> Comprendre chaque maillon de la pipeline au niveau où on peut le dériver, le
> débugger et prédire son comportement — pas seulement l'appeler.
>
> Prérequis assumés : algèbre linéaire d'ingénieur (produit scalaire, normes,
> matrices), probabilités de base (espérance, variance, loi binomiale). Tout le
> reste est construit ici. Les constantes empiriques sont marquées comme telles.

## 0. Comment utiliser ce document

Chaque chapitre correspond à un moment du build. Lis le chapitre **avant** de
lancer le jalon correspondant, puis utilise `/deepdive <composant>` dans Claude
Code pour confronter la théorie au code réel du repo.

| Jalon | Chapitres à lire |
|---|---|
| Tranche de calibration | 1, 2, 3 |
| E2e complet (hybride + citations) | 4, 5, 6, 7 |
| Boucles d'éval | 8, 9 (le 9 est le plus important du document) |
| Productisation | 10, 11 |

---

## 1. Le système entier : un entonnoir de probabilités

Avant les maths de chaque brique, le cadre qui justifie toute l'architecture.
Une réponse correcte exige une conjonction d'événements :

$$P(\text{réponse correcte}) \approx P(\text{doc dans le corpus}) \cdot P(\text{retrouvé} \mid \text{présent}) \cdot P(\text{utilisé} \mid \text{retrouvé}) \cdot P(\text{fidèle} \mid \text{utilisé})$$

C'est une approximation (les événements ne sont pas indépendants), mais elle a
une conséquence pratique majeure : **les erreurs se multiplient**. Quatre étages
à 90 % donnent un système à 66 %. D'où deux règles :

1. On instrumente chaque étage séparément (c'est la raison d'être du harnais
   d'éval : mesurer $P(\text{retrouvé})$ sans le bruit de la génération).
2. On investit toujours sur l'étage le plus faible — un reranker parfait ne
   sauve pas un retrieval qui n'a pas ramené le bon document ($P(\text{utilisé})$
   est conditionné à $P(\text{retrouvé})$).

Quand une réponse est fausse, ta première question n'est jamais « pourquoi le
LLM a halluciné » mais « à quel étage de l'entonnoir l'information s'est
perdue ». Le harnais te répondra en une requête SQL.

---

## 2. Du texte aux vecteurs

### 2.1 Tokenisation

Les modèles ne voient pas des mots mais des *subwords* issus d'un vocabulaire
appris (BPE ou WordPiece, typiquement 30k–250k entrées). L'algorithme BPE part
des caractères et fusionne itérativement la paire la plus fréquente du corpus
d'entraînement. Conséquences concrètes pour toi :

- Un mot rare ou technique explose en plusieurs tokens (`pgvector` → `pg`,
  `vector`) — le lexical (ch. 4) le retrouvera exactement, le dense parfois non.
- La limite de séquence du modèle (souvent 512 tokens pour les encodeurs, 8192
  pour bge-m3) se compte en tokens, pas en mots : ~0,7 mot/token en français.
  C'est une contrainte dure sur la taille des chunks (ch. 7).

### 2.2 L'encodeur Transformer

Un encodeur = une pile de $n$ couches identiques. Chaque couche applique
l'attention multi-têtes puis un MLP, avec connexions résiduelles et
normalisation. Le cœur, l'attention :

$$\mathrm{Attn}(Q, K, V) = \mathrm{softmax}\!\left(\frac{QK^\top}{\sqrt{d_k}}\right) V$$

où $Q = XW_Q$, $K = XW_K$, $V = XW_V$ sont des projections linéaires de la
séquence d'entrée $X \in \mathbb{R}^{L \times d}$. Lecture : pour chaque token,
$QK^\top$ calcule un score de compatibilité avec tous les autres tokens ; le
softmax en fait une distribution ; la sortie est une moyenne pondérée des
valeurs $V$. Chaque token « lit » donc tout le contexte.

Le facteur $\sqrt{d_k}$ : si les composantes de $q$ et $k$ sont i.i.d. de
moyenne nulle et de variance 1, alors $\mathrm{Var}(q \cdot k) = d_k$. Sans normalisation, les
scores grandissent avec la dimension, le softmax sature (gradients quasi nuls).
On divise par l'écart-type $\sqrt{d_k}$ pour ramener la variance à 1.

Coût d'une couche pour $L$ tokens en dimension $d$ (ordres de grandeur, en
comptant multiplication+addition = 2 FLOPs) :

- Projections + MLP : $\mathcal{O}(L \cdot d^2)$ — domine pour les séquences courtes.
- Scores d'attention $QK^\top$ et agrégation : $\mathcal{O}(L^2 \cdot d)$ — domine
  pour les longues séquences. En comptant les constantes, le croisement n'arrive
  que vers $L \approx 6d$ : aux longueurs de reranking (256–512 tokens, $d \geq 384$),
  le terme en $L \cdot d^2$ reste dominant. Ce qui rend le cross-encoder cher
  (ch. 6) n'est donc pas le terme quadratique — c'est le passage complet
  **par paire**, non précalculable.

Positions : l'attention est invariante par permutation, il faut injecter l'ordre.
Selon le modèle : embeddings de position appris (XLM-RoBERTa, donc bge-m3) ou
rotations RoPE appliquées à $Q$ et $K$ (ModernBERT). Retiens surtout que la
capacité à traiter 8k tokens dépend de ce choix.

### 2.3 Du token à la phrase : pooling

L'encodeur sort une matrice $H \in \mathbb{R}^{L \times d}$ (un vecteur par
token). L'embedding de passage est un résumé : soit le vecteur du token spécial
`[CLS]`, soit le *mean pooling* $\frac{1}{L}\sum_i h_i$ (pondéré par le masque
d'attention). C'est une **compression avec perte** : tout le passage doit tenir
dans $d$ nombres (384 à 1024). Garde cette image — elle explique à elle seule la
moitié des échecs de retrieval (ch. 2.6 et 7).

### 2.4 Ce qui donne son sens à l'espace : l'objectif contrastif

Un encodeur pré-entraîné (masked LM) ne produit PAS un bon espace de recherche.
Ce qui le produit, c'est le fine-tuning contrastif : rapprocher les paires
(requête, passage pertinent), éloigner tout le reste. La loss standard,
**InfoNCE** :

$$\mathcal{L} = -\log \frac{\exp(s(q, d^+)/\tau)}{\exp(s(q, d^+)/\tau) + \sum_{d^- \in \mathcal{N}} \exp(s(q, d^-)/\tau)}$$

avec $s$ = similarité cosinus, $\tau$ la température (empiriquement 0,01–0,05
pour les modèles de retrieval), $\mathcal{N}$ les négatifs. Trois mécanismes à
comprendre :

- **La température** contrôle la dureté : petite $\tau$ ⇒ le softmax se
  concentre sur les négatifs les plus proches du positif — le gradient est
  dominé par les *hard negatives*. C'est ce qui sculpte les frontières fines.
- **In-batch negatives** : dans un batch de $B$ paires, chaque passage sert de
  négatif aux $B-1$ autres requêtes — $B^2$ interactions pour le prix de $2B$
  encodages. D'où les batchs énormes de l'entraînement de ces modèles.
- **Hard negative mining** : les négatifs aléatoires deviennent vite triviaux
  (gradient ≈ 0) ; on mine des négatifs difficiles (ex. top BM25 non pertinents).
  La qualité d'un modèle d'embedding est largement la qualité de son mining.

Vue géométrique (Wang & Isola, 2020) : InfoNCE optimise deux propriétés en
tension — *alignment* (les paires positives sont proches) et *uniformity* (les
embeddings se répartissent uniformément sur la sphère, préservant un maximum
d'information). Un espace effondré (tout proche de tout) est le mode d'échec
que l'uniformité combat.

Pourquoi ça te concerne : ton corpus d'entreprise n'est pas distribué comme les
données d'entraînement du modèle. Quand le retrieval dense échoue sur ton
jargon interne, la cause profonde est là — et la réponse est l'hybride (ch. 4-5),
pas un meilleur prompt.

### 2.5 Géométrie : cosinus, produit scalaire, L2

Pour des vecteurs normalisés ($\|u\| = \|v\| = 1$) :

$$\|u - v\|^2 = \|u\|^2 + \|v\|^2 - 2\langle u, v\rangle = 2 - 2\cos(u, v)$$

Donc distance L2, similarité cosinus et produit scalaire induisent **le même
classement**. C'est pour ça qu'on normalise systématiquement en sortie
d'encodeur : ça rend le choix d'opérateur indifférent au ranking et ça borne les
scores dans $[-1, 1]$. Sans normalisation, le produit scalaire mélange direction
et norme — la norme encode souvent la fréquence/longueur plus que le sens
(anisotropie des espaces contextuels, Ethayarajh 2019).

Attention piège : les scores cosinus **ne sont pas des probabilités** ni
comparables entre modèles. Un seuil « 0,8 = pertinent » n'a aucun sens absolu ;
seule la distribution de TES scores sur TON corpus en a (d'où le harnais).

### 2.6 Ce que le vecteur ne contient pas

La compression de 2.3 + l'objectif de 2.4 impliquent des angles morts
systématiques, à connaître par cœur parce que tu les verras dans tes cas
d'échec :

- **Négation** : « le contrat inclut X » et « le contrat n'inclut pas X »
  partagent presque tous leurs tokens — cosinus très élevé, sens opposé.
- **Nombres, dates, identifiants** : « CA 2024 » vs « CA 2025 », « article 12 »
  vs « article 21 » — la géométrie contrastive n'a pas été entraînée à les
  séparer, ils pèsent peu dans le vecteur.
- **Entités rares** : deux noms propres inconnus du modèle tombent au même
  endroit approximatif de l'espace.

Le lexical exact (ch. 4) couvre précisément ces trois cas. L'hybride n'est pas
une option d'ingénieur prudent, c'est la conséquence logique de cette géométrie.

---

## 3. Chercher dans l'espace : kNN exact et HNSW

### 3.1 Le problème

Trouver les $k$ plus proches voisins d'une requête parmi $N$ vecteurs de
dimension $d$ coûte $\mathcal{O}(N \cdot d)$ en exact (un produit scalaire par
document). À $N = 10^5$, c'est encore jouable (~40 ms mono-thread à 768d) ; à
$10^7$, non. Et il n'existe pas de structure exacte efficace en haute dimension
(malédiction de la dimensionnalité : les distances se concentrent, les arbres
type k-d dégénèrent). D'où l'approximation.

### 3.2 HNSW

HNSW (Malkov & Yashunin, 2016) = un graphe de proximité navigable + une
hiérarchie de type skip-list.

**Construction** : chaque nœud tire son niveau maximal
$l = \lfloor -\ln(U) \cdot m_L \rfloor$ avec $U \sim \mathrm{Uniform}(0,1)$ et
$m_L = 1/\ln(M)$ — une géométrique : la couche $l$ contient environ $N/M^l$
nœuds. À chaque couche, le nœud se connecte à ses $M$ voisins les plus proches
(2M à la couche 0), avec une heuristique de diversification des arêtes qui évite
les clusters de liens redondants.

**Recherche** : on part du point d'entrée de la couche la plus haute (clairsemée
= grands sauts), descente gloutonne vers la requête, puis on passe à la couche
inférieure, jusqu'à la couche 0 où une recherche en faisceau de largeur
`ef_search` explore le voisinage. Complexité empirique
$\mathcal{O}(\log N)$ par requête.

**Les trois boutons et leurs effets** :

- $M$ (liens/nœud) : ↑ = meilleur rappel, plus de RAM (~$M \times 8$ octets de
  liens par nœud en plus du vecteur), construction plus lente. Typique : 16–48.
- `ef_construction` : largeur du faisceau à l'insertion. ↑ = graphe de meilleure
  qualité, indexation plus lente. Typique : 64–200.
- `ef_search` : largeur du faisceau à la requête. **C'est TON bouton
  rappel/latence à chaud** : la courbe rappel(ef_search) monte vite puis
  sature ; elle se mesure, jamais ne se devine.

**Le rappel ANN se mesure** : $\text{recall}_{\text{ANN}}@k = \frac{|\text{ANN}@k \cap \text{exact}@k|}{k}$,
calculé contre un scan exact sur un échantillon de requêtes. Il vient
multiplier ton entonnoir du ch. 1 — un index mal réglé te coûte des points de
recall que tu iras chercher à tort dans le chunking.

### 3.3 Spécificités pgvector

- Opérateurs : `<=>` distance cosinus, `<#>` produit scalaire négatif, `<->` L2.
  Vecteurs normalisés ⇒ classements identiques (cf. 2.5) ; on standardise sur `<=>`.
- `halfvec` (fp16) : moitié de RAM, perte de rappel généralement négligeable —
  à vérifier sur ton bench, pas à croire sur parole.
- **Suppressions/mises à jour** : HNSW ne rétrécit pas ; les tuples morts sont
  nettoyés par VACUUM mais la structure du graphe se dégrade lentement sous
  churn élevé — prévois un `REINDEX` périodique (ton versionnement de documents
  fait beaucoup de deletes).
- **Filtrage (ACL !)** : un `WHERE` sur une recherche HNSW est appliqué
  *pendant/après* le parcours du graphe — si le filtre élimine 90 % des
  candidats, l'index peut rendre moins de $k$ résultats ou dégrader le rappel.
  pgvector ≥ 0.8 introduit les *iterative index scans* (il continue le parcours
  jusqu'à satisfaire k) — mais c'est **opt-in** : `SET hnsw.iterative_scan =
  relaxed_order` (défaut `off`), borné par `hnsw.max_scan_tuples`. Active-le
  explicitement, puis mesure le rappel **avec** filtres
  ACL représentatifs — c'est un des pièges classiques du RAG d'entreprise
  (ch. 11).

---

## 4. La voie lexicale : BM25 — et la vérité sur Postgres FTS

### 4.1 De TF-IDF à BM25

Intuition : un terme de requête compte s'il est fréquent dans le document (TF)
et rare dans le corpus (IDF). BM25 (Robertson et al., issu du modèle
probabiliste de pertinence) raffine les deux :

$$\text{score}(q, D) = \sum_{t \in q} \mathrm{IDF}(t) \cdot \frac{f_{t,D} \cdot (k_1 + 1)}{f_{t,D} + k_1 \cdot \left(1 - b + b \cdot \frac{|D|}{\text{avgdl}}\right)}$$

$$\mathrm{IDF}(t) = \ln\!\left(1 + \frac{N - n_t + 0.5}{n_t + 0.5}\right)$$

- **Saturation de TF** ($k_1$, empiriquement 1,2–2,0) : le terme
  $\frac{f(k_1+1)}{f + k_1 \cdot (\ldots)}$ est une hyperbole croissante bornée —
  la 10ᵉ occurrence d'un mot apporte moins que la 2ᵉ. TF-IDF brut est linéaire
  en $f$, ce qui sur-récompense le keyword stuffing.
- **Normalisation de longueur** ($b$, empiriquement ≈ 0,75) : un long document
  a mécaniquement plus d'occurrences ; on pénalise proportionnellement à
  $|D|/\text{avgdl}$. $b = 0$ : aucune normalisation ; $b = 1$ : totale.
- **IDF** : $\ln$ du ratio documents-sans-le-terme / documents-avec. Un terme
  présent partout (« le », « projet ») pèse ~0 ; un identifiant présent dans 2
  documents pèse énormément. C'est exactement le complément des angles morts
  du dense (2.6).

### 4.2 `ts_rank` n'est PAS BM25

Le full-text natif de Postgres (`tsvector`/`ts_rank`) score sur la fréquence des
lexèmes avec pondérations de zones et option de normalisation par longueur,
mais **sans IDF** : il ne sait pas qu'un terme est rare dans le corpus. Sur des
requêtes à mélange de mots communs et rares, il sur-pondère les communs.

Conséquence pour groundcite v1 : Postgres FTS + RRF devrait donner l'essentiel
du gain hybride (le dense compense en partie) — hypothèse à confirmer au bench —
et ça reste « zéro infra ». Mais si le bench lexical déçoit, la première suspecte est l'absence
d'IDF — l'option documentée est une extension BM25 réelle (ex. pg_search/
ParadeDB, moteur tantivy) au prix d'une dépendance. Décision à prendre avec
des chiffres, pas par principe — et c'est un excellent sujet d'ADR.

### 4.3 Quand le lexical gagne

Identifiants (`INV-2024-0113`), jargon interne, noms propres, nombres, sigles,
requêtes courtes très spécifiques. Quand tu liras tes cas d'échec en boucle
d'éval, classe-les : « échec de vocabulaire » (dense aveugle, lexical voit) vs
« échec de paraphrase » (lexical aveugle, dense voit). Le ratio des deux te dit
où investir.

---

## 5. Fusion hybride

### 5.1 Le problème : des scores incommensurables

Cosinus ∈ $[-1, 1]$ avec une distribution serrée (souvent 0,3–0,9) ; BM25 ∈
$[0, +\infty)$, dépendant de la requête. Additionner naïvement n'a pas de sens.
Deux familles de solutions :

**Fusion par rangs — RRF** (Reciprocal Rank Fusion, Cormack et al. 2009) :

$$\mathrm{RRF}(d) = \sum_{r \in \text{systèmes}} \frac{1}{k + \mathrm{rank}_r(d)}$$

avec $k = 60$ (constante empirique du papier, étonnamment robuste). Propriétés :
insensible aux échelles (on jette les scores, on garde les rangs), le $k$
amortit l'écart entre rang 1 et rang 10 (sans lui, rang 1 vaudrait 2× rang 2),
et un document bien classé par les deux systèmes bat un document excellent dans
un seul — c'est un vote avec majoration de consensus.

**Fusion par scores normalisés** : min-max ou z-score par liste, puis
combinaison convexe $\alpha \cdot s_{\text{dense}} + (1-\alpha) \cdot s_{\text{lex}}$.
Potentiellement meilleure (elle exploite l'information d'écart que RRF jette),
mais $\alpha$ et la normalisation deviennent des hyperparamètres à régler par
corpus — fragile en v1.

Choix groundcite : RRF d'abord (zéro hyperparamètre, robuste), score fusion en
expérience de boucle d'éval si le plafond RRF est atteint. Le reranker (ch. 6)
récupère de toute façon l'essentiel de ce que la fusion laisse sur la table.

---

## 6. Reranking : pourquoi un cross-encoder voit ce que le dense ne peut pas voir

### 6.1 L'argument structurel

Le bi-encodeur calcule $s(q, d) = \langle f(q), g(d) \rangle$ : chaque texte est
compressé **indépendamment**, l'interaction se réduit à un produit scalaire —
une forme bilinéaire de rang $\leq d$ sur des représentations figées. Aucune
chance de modéliser « le mot *pas* de la requête porte sur le terme 3 du
document ».

Le cross-encoder encode la **concaténation** `[CLS] q [SEP] d` : l'attention
(2.2) calcule des interactions token-à-token entre requête et document dès la
première couche, et sort un score $s(q, d)$ directement. C'est structurellement
plus expressif — et ça se paie : un passage transformer complet
($\mathcal{O}(L d^2 + L^2 d)$) **par paire**, non précalculable côté documents
contrairement aux embeddings du bi-encodeur — impossible sur tout le corpus, d'où le
pattern : retrieval large (top 50–100 par candidat generator) → rerank fin →
top 5–10 au LLM.

Entre les deux, l'interaction tardive (ColBERT) : embeddings par token des deux
côtés, score $\sum_i \max_j \langle q_i, d_j \rangle$ (MaxSim) — précalculable
côté documents. Hors scope v1, mais bge-m3 sait le produire ; à garder pour une
boucle d'éval future.

### 6.2 Entraînement et nature des scores

Pointwise (BCE sur pertinent/non), pairwise (RankNet :
$\mathcal{L} = \log(1 + e^{-\sigma(s^+ - s^-)})$ — n'apprend que l'ordre), ou
listwise ; souvent distillé d'un modèle plus gros. Conséquence pratique : les
scores d'un cross-encoder sont **des logits de classement, pas des
probabilités calibrées**. Deux usages, deux exigences :

- Trier le top-k : les rangs suffisent, aucun problème.
- Couper (« ne garder que si score > θ ») : là il faut calibrer — choisir θ sur
  la distribution de TES scores annotés (courbe précision/rappel), pas sur une
  valeur vue dans un blog.

### 6.3 Budget latence

Reranker 50 paires de 256 tokens ≈ 50 passages d'encodeur : c'est LE poste
lourd de ta latence hors LLM. Leviers : batch unique sur GPU/CPU, int8 (ch. 10),
réduire à top-30, tronquer les passages. Chaque levier se mesure au bench (le
p95 < 800 ms de la roadmap se gagne ou se perd ici).

---

## 7. Le chunking : un problème de compression avec perte

### 7.1 La tension fondamentale

Rappelle-toi 2.3 : un chunk = un vecteur de $d$ nombres, quelle que soit sa
taille. D'où la tension :

- **Chunk long** → plus de contenu par vecteur → signal dilué (le paragraphe
  pertinent noyé dans la page) → retrieval imprécis. La similarité
  requête-document se comporte approximativement comme une moyenne sur les
  sous-thèmes du chunk.
- **Chunk court** → vecteur précis → mais contexte insuffisant pour la
  génération (la phrase retrouvée sans sa définition, son tableau, sa section).

Ce sont deux objectifs différents : **retrouver** demande petit, **répondre**
demande grand. Les stratégies avancées découplent les deux :

- **Parent-child** : on indexe des petits chunks, on remonte le parent (section
  entière) au LLM. Le retrieval garde sa précision, la génération son contexte.
- **Late chunking** : on encode le document long d'un coup (les embeddings de
  tokens voient tout le contexte), puis on poole par chunk — chaque vecteur de
  chunk « sait » ce qui l'entoure. Élégant, dépend d'un encodeur long-contexte.
- **Layout-aware** (choix v1) : découper aux frontières de structure (sections,
  paragraphes, tableaux) plutôt qu'à taille fixe — l'hypothèse est que la
  structure documentaire approxime la cohérence sémantique. L'overlap
  (10–20 %) est un pansement contre les coupes malheureuses aux frontières.

### 7.2 Les invariants d'offsets (citations)

Décision d'ingénierie qui a une justification théorique : la citation au span
près exige que chaque chunk conserve `(doc_id, char_start, char_end)` **exacts
à travers toute la pipeline** (parsing → nettoyage → chunking → index). Toute
transformation de texte (normalisation d'espaces, dé-hyphénation) doit être
soit répercutée sur les offsets, soit appliquée avant leur calcul. C'est un
invariant à tester unitairement — un offset décalé de 3 caractères détruit la
confiance de l'utilisateur plus sûrement qu'une absence de citation, parce
qu'il ressemble à un mensonge.

---

## 8. Génération ancrée et refus : de la probabilité à la décision

### 8.1 Pourquoi le LLM peut ignorer tes documents

Le LLM échantillonne $y \sim p_\theta(y \mid q, D)$. Mais $p_\theta$ a été
façonnée par le pré-entraînement : quand le contexte $D$ contredit le prior du
modèle (connaissance paramétrique), le conflit se résout parfois en faveur du
prior — surtout si $D$ est ambigu, tronqué ou peu saillant. L'ancrage n'est pas
un interrupteur, c'est un rapport de forces. Le prompt de synthèse peut le
déplacer (« réponds uniquement depuis les extraits »), jamais le garantir —
d'où la vérification a posteriori.

### 8.2 Vérifier la fidélité : NLI au niveau des claims

Pipeline de vérification :

1. **Décomposer** la réponse en claims atomiques (une affirmation vérifiable
   par claim) — fait par un petit LLM ; c'est le maillon le plus fragile,
   surveille-le.
2. Pour chaque claim $c_i$, chercher le meilleur span support $s_j$ et scorer
   $P(\text{entailment} \mid \text{premise}=s_j, \text{hypothesis}=c_i)$ avec un
   modèle NLI (entailment / neutral / contradiction).
3. **Agréger** : $\text{faithfulness} = \frac{1}{n}\sum_i \mathbb{1}[\max_j P_{ij} > \theta]$
   (part des claims soutenus). Le $\min_i$ est l'alternative paranoïaque : une
   seule claim non soutenue coule la réponse. Choix produit, pas choix
   technique.

Un NLI n'est pas magique : il hérite de ses biais d'entraînement (paires
courtes, anglais dominant) — vérifie sa qualité sur 30 exemples à toi avant de
lui confier le gate.

### 8.3 Le refus comme prédiction sélective

« Je ne réponds pas si ce n'est pas fondé » est un problème formalisé
(prédiction sélective, Geifman & El-Yaniv) : tu choisis un seuil $\theta$ qui
définit une **couverture** $\phi = P(\text{répondre})$ et un **risque**
$r = P(\text{erreur} \mid \text{répondre})$. Monter $\theta$ baisse le risque et
la couverture. Le bon $\theta$ minimise le coût attendu :

$$\mathbb{E}[\text{coût}] = \phi \cdot r \cdot c_{\text{erreur}} + (1 - \phi) \cdot c_{\text{refus}}$$

Les deux coûts sont des jugements métier (une réponse juridique fausse coûte
1000× un refus ; en brainstorming c'est l'inverse). Livrable concret du harnais :
la **courbe risque-couverture** de ton système — elle transforme un débat
d'opinion (« il refuse trop ») en choix d'opérating point chiffré. C'est
exactement le type d'artefact qui distingue un ML engineer.

### 8.4 Calibration

Pour que $\theta$ soit interprétable, les scores doivent être à peu près
calibrés : parmi les prédictions à confiance 0,8, ~80 % devraient être
correctes. Diagnostic : diagramme de fiabilité (binner les confiances, tracer
précision observée vs confiance moyenne) et ECE
$= \sum_b \frac{n_b}{n} |\mathrm{acc}(b) - \mathrm{conf}(b)|$. Correction
simple si besoin : régression logistique sur le score (Platt scaling), apprise
sur ton dev set.

---

## 9. L'évaluation — le chapitre qui empêche de tourner en rond

### 9.1 Les métriques de retrieval, dérivées

Pertinence binaire par (requête, document), jugée par ton golden set.

- $\text{recall@}k = \frac{|\text{pertinents} \cap \text{top-}k|}{|\text{pertinents}|}$ —
  « le bon doc est-il dans ce que je passe au reranker/LLM ». LA métrique
  amont de l'entonnoir.
- $\mathrm{MRR} = \frac{1}{|Q|}\sum_q \frac{1}{\mathrm{rank}_q^{\text{1er pertinent}}}$ —
  récompense violemment le rang 1 (1 vs 0,5 vs 0,33...). Pertinent quand un
  seul document suffit.
- $\mathrm{nDCG@}k = \frac{\mathrm{DCG@}k}{\mathrm{IDCG@}k}$ avec
  $\mathrm{DCG@}k = \sum_{i=1}^{k} \frac{2^{\mathrm{rel}_i} - 1}{\log_2(i+1)}$ —
  gère la pertinence graduée (2 = répond, 1 = contexte utile, 0 = rien) avec un
  escompte logarithmique du rang : être 4ᵉ au lieu de 1ᵉʳ coûte, mais moins que
  d'être absent. La normalisation par le classement idéal (IDCG) rend les
  requêtes comparables entre elles.

Convention : recall@k pour piloter le candidate generator (k = ce que voit le
reranker), nDCG@10 pour piloter le classement final.

### 9.2 Les métriques d'ancrage, définies formellement

- **Faithfulness** = part des claims de la réponse soutenus par au moins un
  span cité (8.2).
- **Citation precision** = part des citations qui soutiennent réellement la
  claim qu'elles décorent.
- **Citation coverage** = part des claims portant au moins une citation.
Les trois se calculent avec le même juge NLI — et le juge lui-même doit être
audité sur un échantillon (sinon tu optimises l'accord avec un juge faux).

### 9.3 La statistique qui manque à 90 % des évals RAG

Ton golden set aura n ≈ 60–100 requêtes. À cette taille, **le bruit
d'échantillonnage est du même ordre que les effets que tu cherches** :

Écart-type d'un recall@k (succès binaire par requête, taux $p$) :
$\mathrm{SE} = \sqrt{p(1-p)/n}$. À $p = 0{,}7$, $n = 80$ : SE ≈ 5,1 points.
Une différence brute de 3 points entre deux configs est **invisible** dans ce
bruit en comparaison non appariée.

Ce qui te sauve : **l'appariement**. Les deux configs sont évaluées sur les
mêmes requêtes ; seules comptent les requêtes discordantes (A réussit, B
échoue, ou l'inverse). Test de McNemar : avec $b$ discordantes en faveur de A
et $c$ en faveur de B, sous l'hypothèse nulle $b \sim \mathrm{Binom}(b+c, 0{,}5)$
— à 12 discordantes il faut au moins un partage 10–2 pour conclure (p ≈ 0,04).
Version continue et plus générale : **bootstrap apparié** — rééchantillonne les
requêtes avec remise, recalcule $\Delta$métrique à chaque tirage, lis
l'intervalle [2,5 % ; 97,5 %] ; s'il contient 0, tu n'as rien montré.

Règles d'hygiène à coder dans le harnais (pas dans ta discipline personnelle,
elle cédera) :

1. Chaque comparaison affiche $\Delta$ **avec** son CI bootstrap apparié et le
   compte de discordantes. Une amélioration sans CI n'existe pas.
2. **Dev set vs test set** : tu itéreras 15–25 fois sur le dev set ; à force de
   choisir la variante qui monte, tu overfittes le dev set (garden of forking
   paths — chaque boucle est une comparaison multiple implicite). Le test set
   (30–40 % des requêtes, gelé) ne se regarde qu'aux jalons, 3–4 fois au total.
3. **Auto-accord** : re-annote 10 requêtes à 48 h d'écart ; Cohen's
   $\kappa = \frac{p_o - p_e}{1 - p_e}$ (accord observé corrigé de l'accord dû
   au hasard). $\kappa < 0{,}7$ ⇒ tes labels sont trop bruités pour mesurer des
   effets < 5 points — corrige la consigne d'annotation avant de continuer.

### 9.4 Lire une boucle d'éval sans se mentir

Checklist de lecture d'un rapport de boucle : (1) $\Delta$ dev avec CI —
significatif ? (2) les requêtes discordantes, lues une à une — l'amélioration
a-t-elle un *mécanisme* compréhensible ou est-ce du reshuffling ? (3) une
métrique adjacente s'est-elle dégradée (recall ↑ mais nDCG ↓ = tu ramènes du
bruit mieux classé) ? (4) latence p95 — le gain vaut-il son coût ? Un
changement se garde s'il a un mécanisme + un CI qui exclut 0, pas s'il « a l'air
mieux ».

---

## 10. Efficacité : quantization et budgets de latence par premiers principes

### 10.1 Quantization int8

Représenter les poids (et activations) en entiers 8 bits via une application
affine :

$$x \approx s \cdot (x_q - z), \qquad x_q = \mathrm{clamp}\!\left(\mathrm{round}(x/s) + z,\ 0,\ 255\right)$$

$s$ (échelle) et $z$ (zéro-point) sont calibrés sur la plage observée —
par tenseur, ou mieux **par canal** (une échelle par colonne de la matrice de
poids, ce qui absorbe les canaux à grande dynamique). Pourquoi ça accélère :
4× moins d'octets à déplacer (l'inférence CPU est souvent limitée par la bande
passante mémoire) + instructions SIMD int8 (VNNI/AMX) qui font plus de
multiplications-accumulations par cycle. Coût en qualité sur les encodeurs de
retrieval : typiquement < 1 point de nDCG@10 — mais c'est un chiffre à
**vérifier sur ton bench**, pas un théorème.

### 10.2 Estimer une latence avant de la mesurer

Approximation standard pour un transformer dense : FLOPs ≈ $2 P L$ ($P$ =
paramètres **hors embeddings** — la matrice d'embedding ne fait aucun matmul
par token et pèse ~1/3 d'un petit encodeur, donc l'estimation avec $P$ total
est majorante ; $L$ tokens ; ×2 pour multiplication+addition), plus le terme
d'attention $\propto L^2$, négligeable aux longueurs courtes. Exemple — encoder
une requête de 32 tokens avec un modèle 33M paramètres :
$2 \times 33{\cdot}10^6 \times 32 \approx 2{,}1$ GFLOPs. Un CPU moderne en int8
soutient grossièrement 30–100 GFLOPS effectifs ⇒ ~20–70 ms. Le même calcul sur
le reranker (50 paires × 256 tokens) t'explique immédiatement pourquoi c'est
lui le poste dominant, et de combien le batching/int8/troncature doivent le
réduire pour tenir ton p95. Fais ce calcul de coin de table avant chaque choix
de modèle — c'est lui qui t'évite de découvrir en semaine 3 qu'un modèle est
intenable.

---

## 11. ACL et retrieval filtré

Le filtrage de permissions n'est pas un détail d'API, il change le problème ANN
(3.3) : filtrer **après** la recherche vectorielle tronque les résultats
(moins de $k$ survivants) et biaise le rappel pour les utilisateurs à
permissions étroites — précisément ceux pour qui l'erreur est la plus grave.
Règles :

- Le filtre ACL s'applique **dans** la requête d'index (pre-filter / iterative
  scan), jamais en post-traitement applicatif.
- Le harnais d'éval doit inclure des personas à permissions étroites : mesure
  recall@k **conditionné au périmètre de droits**, pas seulement global.
- Les tests d'étanchéité (aucun span d'un doc interdit ne peut apparaître dans
  une réponse, même via le cache d'une autre requête) sont des tests
  d'invariant, exécutés en CI, adversariaux par construction.

---

## 12. Références (une par idée, les fondatrices)

- Attention/Transformer : Vaswani et al., *Attention Is All You Need*, 2017. arXiv:1706.03762
- Embeddings de phrases : Reimers & Gurevych, *Sentence-BERT*, 2019. arXiv:1908.10084
- InfoNCE : van den Oord et al., *Representation Learning with CPC*, 2018. arXiv:1807.03748
- Alignment/uniformity : Wang & Isola, 2020. arXiv:2005.10242
- Anisotropie : Ethayarajh, 2019. arXiv:1909.00512
- HNSW : Malkov & Yashunin, 2016. arXiv:1603.09320
- BM25 : Robertson & Zaragoza, *The Probabilistic Relevance Framework*, 2009.
- RRF : Cormack, Clarke & Buettcher, SIGIR 2009.
- ColBERT : Khattab & Zaharia, 2020. arXiv:2004.12832
- Late chunking : Günther et al. (Jina), 2024. arXiv:2409.04701
- Prédiction sélective : Geifman & El-Yaniv, 2017. arXiv:1705.08500
- Calibration : Guo et al., *On Calibration of Modern Neural Networks*, 2017. arXiv:1706.04599
- Éval RAG (métriques d'ancrage) : Es et al., *RAGAS*, 2023. arXiv:2309.15217

---

*Ce document vit dans `docs/` de groundcite : chaque fois qu'une boucle d'éval
t'apprend quelque chose qui contredit ou précise un chapitre, amende-le. À
terme, c'est un chapitre « The ML behind groundcite » de la doc publique — ton
apprentissage devient un actif du portfolio.*
