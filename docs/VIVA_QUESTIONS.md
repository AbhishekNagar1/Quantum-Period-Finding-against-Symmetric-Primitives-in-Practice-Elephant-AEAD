# Comprehensive Viva Voce Questions & Answers
### *Project: Quantum Period Finding against Symmetric Primitives in Practice (Target: Elephant AEAD)*
**Reference Literature:** Xavier Bonnetain & Samuel Jaques, *"Quantum Period Finding against Symmetric Primitives in Practice"*, IACR Cryptology ePrint Archive Report 2020/1418 (TCHES 2022).

---

### Q1: What is the core research objective of this project?
**Answer:**  
The objective is to implement, simulate, and analyze the application of quantum period finding (specifically Simon's algorithm and its offline variant) against the NIST Lightweight Cryptography finalist **Elephant** (specifically the Dumbo instance). The project evaluates whether quantum period finding provides an attack faster than exhaustive key search, validating the findings of Xavier Bonnetain and Samuel Jaques (2020/1418).

---

### Q2: How does Elephant-Dumbo operate, and what are its key parameters?
**Answer:**  
Elephant-Dumbo is an inverse-free, parallelizable Authenticated Encryption with Associated Data (AEAD) scheme operating in an Encrypt-then-MAC mode:
* **Underlying Permutation:** $\text{Spongent-}\pi[160]$ (160 bits / 20 bytes state width, 80 rounds).
* **Master Key ($K$):** 128 bits (16 bytes).
* **Public Nonce ($N$):** 96 bits (12 bytes).
* **Authentication Tag ($T$):** 64 bits (8 bytes).
* **Mask Generation:** Linear Feedback Shift Register (LFSR) $\varphi$ operating on 20-byte states.

Encryption uses a counter mode:
$$C_i = M_i \oplus P(N' \oplus \text{mask}_i) \oplus \text{mask}_i \oplus N'$$
where $N' = N \parallel 0^{64}$ is the 160-bit padded nonce.

---

### Q3: Where is the Even-Mansour construction inside Elephant?
**Answer:**  
Rearranging the encryption equation for known plaintext block $M_i$ and ciphertext block $C_i$:
$$Z(N') = C_i \oplus M_i \oplus N' = P(N' \oplus \text{mask}_i) \oplus \text{mask}_i$$
This is precisely a single-key Even-Mansour block cipher:
$$E_k(x) = P(x \oplus k) \oplus k$$
where $x = N'$ is the known padded nonce, and $k = \text{mask}_i$ is the secret block mask.

---

### Q4: How is Simon's periodic function constructed for Elephant?
**Answer:**  
Following the Kuwakado-Morii (2012) framework:
Define the function $f(x)$ combining the cipher evaluation $E_k(x)$ and the unkeyed public permutation $P(x)$:
$$f(x) = E_k(x) \oplus P(x) = P(x \oplus k) \oplus k \oplus P(x)$$
Evaluating $f(x \oplus k)$:
$$f(x \oplus k) = P((x \oplus k) \oplus k) \oplus k \oplus P(x \oplus k) = P(x) \oplus k \oplus P(x \oplus k)$$
Because XOR is commutative:
$$f(x \oplus k) = P(x \oplus k) \oplus k \oplus P(x) = f(x)$$
Thus, $f(x)$ has a hidden XOR-period $s = k = \text{mask}_i$.

---

### Q5: What is the difference between Online Simon (Q2 Model) and Offline Simon (Q1 Model)?
**Answer:**  
* **Online Simon (Q2 Model):** Requires physical quantum superposition queries to the target device's encryption box:
  $$|x\rangle |y\rangle \to |x\rangle |y \oplus E_k(x)\rangle$$
  This is considered physically unrealistic for symmetric cryptography because deployed cryptographic hardware only accepts classical inputs.
* **Offline Simon (Q1 Model - Bonnetain et al. 2019):** The adversary only makes standard **classical queries** to the online cipher, gathering a dataset $D = \{(x_j, y_j)\}$. The quantum computer is then used entirely **offline** to run Grover-meets-Simon search subroutines using local reversible evaluations of the public permutation $P$.

---

### Q6: What did Bonnetain and Jaques discover about Elephant, and why is it resistant?
**Answer:**  
Bonnetain & Jaques discovered that **the offline Simon attack against Elephant is more expensive than Grover exhaustive key search**:
* **State-to-Key Asymmetry:** Dumbo has state size $n = 160$ bits, while the master key is only $k = 128$ bits.
* **Grover Exhaustive Key Search:** Brute-forcing the 128-bit key takes $\approx \frac{\pi}{4} 2^{128/2} \approx 2^{64}$ quantum operations.
* **Offline Simon Period Finding:** Must find a period in the 160-bit permutation space. The classical query complexity is $O(2^{n/3}) = 2^{160/3} \approx 2^{53.3}$. Combining this with the quantum circuit complexity for 80 rounds of $\text{Spongent-}\pi[160]$ results in $> 1{,}600$ logical qubits and $> 2^{75}$ quantum gate operations.
* **Conclusion:** Unlike PRINCE and Chaskey (which require $\approx 2^{65}$ operations), Elephant's state-to-key ratio protects it from period-finding shortcuts.

---

### Q7: Does Simon's algorithm recover the master key $K$ directly?
**Answer:**  
No. Simon's algorithm directly recovers the **active block mask** $s = \text{mask}_i \in \{0, 1\}^{160}$.
From $\text{mask}_i$:
1. The root mask $M_0 \in \{0, 1\}^{160}$ is recovered in polynomial time by applying the inverse LFSR step $i$ times:
   $$M_0 = \varphi^{-i}(\text{mask}_i)$$
   Knowing $M_0$ completely breaks confidentiality and authenticity across all blocks.
2. Recovering the 128-bit master key $K$ requires inverting the one-way relation:
   $$M_0 = P(K \parallel 0^{32}) \oplus (K \parallel 0^{32})$$
   which is solved via a Grover pre-image check on $K$.

---

### Q8: How does the classical post-processing in Simon's algorithm work?
**Answer:**  
Measuring the quantum query register after the second Walsh-Hadamard transform yields bitstrings $y \in \{0, 1\}^n$ orthogonal to $s$:
$$y \cdot s = \sum_{j=0}^{n-1} y_j s_j \equiv 0 \pmod 2$$
We collect independent measurement vectors into a matrix $M$. Using Gaussian elimination over $\text{GF}(2)$, we row-reduce $M$ to echelon form. When $\text{rank}(M) \ge n - 1$, the nullspace (kernel) has dimension 1, containing the non-zero hidden period vector $s$.

---

### Q9: What happens if there are chance collisions in $f(x)$?
**Answer:**  
In practice, symmetric permutations can have differential characteristics that produce accidental collisions ($f(x) = f(x')$ where $x' \neq x \oplus s$). When this occurs:
* The measurement vectors span a subspace of dimension $n - 2$ (rank $n - 2$), yielding a nullspace with 3 non-zero candidate vectors $\{s, s_2, s \oplus s_2\}$.
* In Even-Mansour, the true secret key $k$ uniquely satisfies the classical relation:
  $$P(k) \oplus k = E_k(0)$$
  Evaluating this single classical check identifies the true cryptographic key among the nullspace candidates.

---

### Q10: Why did this project use a reduced-scale model for simulation?
**Answer:**  
A full 160-bit quantum circuit requires $2^{160}$ complex statevector amplitudes (requiring $10^{39}$ Terabytes of RAM), which cannot be simulated on any classical computer. We created mathematically exact 4-bit and 8-bit scaled models preserving Elephant's exact Even-Mansour algebraic structure, LFSR feedback, and S-box permutation. This enables 100% executable quantum verification in Qiskit Aer while formalizing full 160-bit costs analytically using the Bonnetain & Jaques formulas.
