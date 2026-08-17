# Unigram Tokenizer using EM (Conceptual)

> **Note:** This is the conceptual version of EM used to understand the idea.  
> The actual SentencePiece implementation later uses Lattice + Forward-Backward to compute expected counts efficiently.

---

# Goal

Given a candidate vocabulary,

learn the probability of every token.

The tokenizer should automatically discover which subwords are most useful.

---

# Input

Training Corpus

$$
\mathcal{D}
=
\{x_1,x_2,\ldots,x_N\}
$$

Candidate Vocabulary

$$
V
=
\{s_1,s_2,\ldots,s_M\}
$$

---

# Step 1. Initialize Token Probabilities

Estimate an initial probability for every token.

$$
P(s_i)
=
\frac{\mathrm{freq}(s_i)}
{\sum_j\mathrm{freq}(s_j)}
$$

This is only an initial estimate.

---

# Step 2. Generate All Valid Segmentations

For every word

$$
x=s_1\Vert s_2\Vert\cdots\Vert s_n
$$

generate every valid segmentation.

Example

```text
lowest
```

Possible segmentations

```text
[lowest]
[low, est]
[lo, west]
[low, e, st]
```

---

# Step 3. Compute Segmentation Probability

For every segmentation

$$
P(S)
=
\prod_{i=1}^{n}
P(s_i)
$$

Example

$$
P([low,est])
=
P(low)\times P(est)
$$

**Why multiplication?**

Because all tokens in the segmentation must appear together.

> AND ⇒ Multiply

---

# Step 4. Estimate Token Usage (Expectation)

Instead of assuming only one segmentation is correct,

every segmentation contributes according to its probability.

Example

| Segmentation | Probability |
|--------------|------------:|
| lowest | 0.50 |
| low + est | 0.35 |
| lo + west | 0.15 |

Expected counts

```text
lowest += 0.50

low += 0.35
est += 0.35

lo += 0.15
west += 0.15
```

Thus,

tokens appearing in highly probable segmentations receive more credit.

---

# Step 5. Update Token Probabilities (Maximization)

After processing the entire corpus,

update every token probability.

$$
P(s_i)
=
\frac{\mathrm{Count}(s_i)}
{\sum_j\mathrm{Count}(s_j)}
$$

Higher expected count

↓

Higher probability.

---

# Step 6. Repeat

Repeat the entire process.

$$
P
\rightarrow
P(S)
\rightarrow
\text{Expected Counts}
\rightarrow
P
\rightarrow
\cdots
$$

Until

$$
P_{t+1}
\approx
P_t
$$

This is called **convergence**.

---

# Why does EM work?

Learning happens over the **entire corpus**, not one word.

Example

```text
low
low
lower
lowest
slow
below
```

The token

```text
low
```

appears in many words.

Therefore

$$
\mathrm{Count}(low)\uparrow
$$

which increases

$$
P(low)\uparrow
$$

As

$$
P(low)
$$

increases,

segmentations containing **low** become more likely in future iterations.

Thus,

the tokenizer gradually discovers reusable subwords.

---

# Final Step

After EM converges,

tokens having very low probability are removed.

This process is called

> **Pruning**

The remaining tokens become the final vocabulary.

---

# Complete Pipeline

$$
\boxed{
\begin{aligned}
\text{Corpus}
&\rightarrow
\text{Candidate Vocabulary}
\\
&\rightarrow
\text{Initial Probabilities}
\\
&\rightarrow
\text{Generate Segmentations}
\\
&\rightarrow
P(S)
\\
&\rightarrow
\text{Expected Counts}
\\
&\rightarrow
\text{Update }P
\\
&\rightarrow
\text{Repeat Until Convergence}
\\
&\rightarrow
\text{Prune Low-Probability Tokens}
\\
&\rightarrow
\textbf{Final Vocabulary}
\end{aligned}
}
$$

---

# Important Intuitions

✅ Candidate Vocabulary ≠ Final Vocabulary

✅ Segmentation = Sequence of candidate tokens

✅ AND ⇒ Multiply

$$
P([low,est])
=
P(low)\times P(est)
$$

✅ OR ⇒ Add

$$
P(x)
=
\sum_S
P(S)
$$

(where $S$ represents every valid segmentation of the word.)

---

# Reality Check

The explanation above describes the intuition behind EM.

The actual SentencePiece Unigram implementation **does not explicitly enumerate every segmentation**.

Instead, it uses

- Lattice (Word Graph)
- Forward Algorithm
- Backward Algorithm

to efficiently compute the same expected counts.