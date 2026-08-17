# Unigram Tokenizer - Lattice (Word Graph)

## Why do we need a Lattice?

A word can have many valid segmentations.

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

For long words, the number of possible segmentations grows exponentially.

Instead of explicitly generating every segmentation, Unigram constructs a **Lattice (Word Graph)**.

---

# Lattice

A lattice is a directed graph representing all valid tokenizations of a **single word**.

> **One Word → One Lattice**

Each new word gets its own lattice.

---

# Nodes

Nodes represent **character positions**.

Example

```text
lowest

l  o  w  e  s  t
0  1  2  3  4  5  6
```

There are

$$
n+1
$$

nodes for a word of length

$$
n
$$

---

# Edges

Every candidate token creates one edge.

If a token starts at position

$$
i
$$

and ends at position

$$
j
$$

then create an edge

$$
i \rightarrow j
$$

Examples

```text
lowest
```

creates

```text
0 → 6
```

```text
low
```

creates

```text
0 → 3
```

```text
est
```

creates

```text
3 → 6
```

```text
lo
```

creates

```text
0 → 2
```

```text
west
```

creates

```text
2 → 6
```

---

# Example Lattice

```text
(0)
 | \
 |  \
 |   \
 |    \
 |     \
(3)    (2)
 |       \
 |        \
(6) <------|
```

Possible paths

```text
0 → 6
```

↓

```text
lowest
```

---

```text
0 → 3 → 6
```

↓

```text
low + est
```

---

```text
0 → 2 → 6
```

↓

```text
lo + west
```

---

# Key Insight

Every complete path

$$
0 \rightarrow n
$$

represents one valid segmentation.

Therefore,

> **Segmentation Problem = Graph Path Problem**

---

# Why is this useful?

Instead of enumerating every segmentation,

the paper performs Dynamic Programming directly on the graph.

This allows efficient computation even when millions of segmentations are possible.

---

# Forward Algorithm (Next Step)

The goal of the Forward Algorithm is to compute the probability of the entire word.

Instead of computing every path separately,

it propagates probabilities through the lattice from left to right.

---

# Important Notes

- One word creates one lattice.
- Lattices are temporary.
- After processing the word, the lattice can be discarded.
- Character positions (indices) are local to that word.

---

# Pipeline

$$
\boxed{
\begin{aligned}
\text{Word}
&\rightarrow
\text{Character Positions}
\\
&\rightarrow
\text{Candidate Tokens}
\\
&\rightarrow
\text{Edges}
\\
&\rightarrow
\text{Lattice}
\\
&\rightarrow
\text{Forward Algorithm}
\end{aligned}
}
$$