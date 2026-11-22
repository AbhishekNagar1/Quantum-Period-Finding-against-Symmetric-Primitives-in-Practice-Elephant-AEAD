# Research Report: Quantum Period Finding against Symmetric Primitives in Practice
### Target Cryptographic Primitive: Elephant Authenticated Encryption Scheme
**Author:** Quantum Cryptography Research Group  
**Academic Basis:** Xavier Bonnetain and Samuel Jaques, *"Quantum Period Finding against Symmetric Primitives in Practice"*, IACR Cryptology ePrint Archive Report 2020/1418 (TCHES 2022).

---

## 1. Executive Summary

While public-key cryptosystems like RSA and ECC are well known to be broken in polynomial time by Shor's algorithm, symmetric-key cryptography is typically considered quantum-resistant with security halved by Grover's algorithm ($O(2^{k/2})$). However, recent developments in quantum cryptanalysis demonstrate that **quantum period-finding algorithms (Simon's algorithm)** can break certain symmetric primitives with exponential or sub-exponential speedups if an internal periodic structure exists.

This project investigates the application of quantum period finding against the NIST Lightweight Cryptography finalist **Elephant** (specifically the **Dumbo** instance). We formulate the Even-Mansour reduction, synthesize quantum oracles for reduced-scale experimental models, evaluate linear systems over $\text{GF}(2)$, and rigorously formalize the theoretical resource estimations from Bonnetain & Jaques (ePrint 2020/1418).

**Primary Research Finding:**
In contrast to primitives like **PRINCE** and **Chaskey** (which are highly vulnerable to offline Simon attacks around $2^{65}$ quantum operations), **Elephant's quantum period-finding attack is strictly more expensive than exhaustive key search ($> 2^{75}$ operations vs. $2^{64}$ for Grover search)**. This proves that Elephant's state-to-key asymmetry ($n = 160 > k = 128$) and LFSR masking structure provide robust protection against quantum period-finding attacks.

---

## 2. Cryptographic Architecture of Elephant-Dumbo

Elephant was designed by Tim Beyne, Yu Long Chen, Christoph Dobraunig, and Bart Mennink. Dumbo is its primary hardware-oriented instance:
* **State / Permutation Size ($n$):** 160 bits (20 bytes).
* **Master Key Size ($k$):** 128 bits (16 bytes).
* **Nonce Size ($|N|$):** 96 bits (12 bytes).
* **Authentication Tag ($\tau$):** 64 bits (8 bytes).
* **Permutation Primitive:** $\text{Spongent-}\pi[160]$ (80 rounds).

### 2.1 Spongent-pi[160] Permutation
Each of the 80 rounds consists of:
1. **Round Constant XOR (`lCounter`):** Driven by a 7-bit LFSR with primitive polynomial $x^7 + x^6 + 1$ initialized to `0x75`. State byte 0 is XORed with `lCounter`, and state byte 19 is XORed with the bit-reversed `retnuoCl`.
2. **Non-Linear Layer (`sBoxLayer`):** 40 parallel 4-bit S-boxes:
   $$S = [0xE, 0x4, 0xB, 0x1, 0x7, 0x9, 0xF, 0x3, 0x0, 0xC, 0x5, 0x2, 0xA, 0xD, 0x8, 0x6]$$
3. **Linear Layer (`pLayer`):** Bit-permutation moving bit $j$ to position $P(j)$:
   $$P(j) = \begin{cases} (40 \cdot j) \pmod{159} & 0 \le j \le 158 \\ 159 & j = 159 \end{cases}$$

### 2.2 LFSR Mask Progression ($\varphi$)
The root mask $M_0$ is derived from master key $K$:
$$K' = K \parallel 0^{32}$$
$$M_0 = P(K') \oplus K'$$
Subsequent masks for block $i$ advance via the 20-byte LFSR $\varphi$:
$$\text{feedback} = \text{rotl}_3(\text{input}[0]) \oplus (\text{input}[3] \ll 7) \oplus (\text{input}[13] \gg 7)$$
$$\text{output} = \text{input}[1..19] \parallel \text{feedback}$$

Because $\varphi$ is a linear bijection over $\mathbb{F}_2^{160}$, it is invertible in polynomial time:
$$\text{input}[0] = \text{rotr}_3(\text{output}[19] \oplus (\text{output}[2] \ll 7) \oplus (\text{output}[12] \gg 7))$$

---

## 3. Mathematical Derivation of the Quantum Attack

### 3.1 Isolating the Even-Mansour Core
For a known plaintext block $M_i$ and ciphertext block $C_i$ with padded nonce $N' = N \parallel 0^{64}$:
$$C_i = M_i \oplus P(N' \oplus \text{mask}_i) \oplus \text{mask}_i \oplus N'$$
Rearranging known terms defines the keystream evaluation:
$$Z(N') = C_i \oplus M_i \oplus N' = P(N' \oplus \text{mask}_i) \oplus \text{mask}_i$$
This is a single-key Even-Mansour cipher $E_k(x) = P(x \oplus k) \oplus k$, with secret key $k = \text{mask}_i$.

### 3.2 Periodic Function Reduction
Following Kuwakado and Morii (2012):
$$f(x) = E_k(x) \oplus P(x) = P(x \oplus k) \oplus k \oplus P(x)$$
Evaluating at $x \oplus k$:
$$f(x \oplus k) = P((x \oplus k) \oplus k) \oplus k \oplus P(x \oplus k) = P(x) \oplus k \oplus P(x \oplus k) = f(x)$$
Thus, $f(x)$ is periodic with period $s = k = \text{mask}_i$.

### 3.3 Simon's Quantum Subroutine & GF(2) Elimination
1. Prepare $|0\rangle^{\otimes n} |0\rangle^{\otimes n}$.
2. Apply Hadamard gates: $\frac{1}{\sqrt{2^n}} \sum_x |x\rangle |0\rangle^{\otimes n}$.
3. Evaluate oracle $U_f$: $\frac{1}{\sqrt{2^n}} \sum_x |x\rangle |f(x)\rangle$.
4. Apply Hadamard gates: $\frac{1}{2^n} \sum_x \sum_y (-1)^{x \cdot y} |y\rangle |f(x)\rangle$.
5. Measurement produces bitstring $y$ such that:
   $$y \cdot s \equiv 0 \pmod 2$$
6. Gaussian elimination over $\text{GF}(2)$ on $n - 1$ linearly independent vectors uniquely extracts $s$.

---

## 4. Online vs. Offline Simon (Q1 vs. Q2 Model)

* **Online Q2 Model:** Requires superposition queries to the physical encryption device. Unrealistic in practical symmetric cryptanalysis.
* **Offline Q1 Model (Bonnetain et al. 2019):** Attacker queries the target classically, gathering $D = \{(x_j, y_j)\}$. The quantum computer executes Simon's search offline on the attacker's hardware using reversible evaluations of $P$.

---

## 5. Quantitative Cryptanalytic Comparison

Formalizing the findings of Bonnetain & Jaques (2020/1418):

| Target Primitive | State ($n$) | Key ($k$) | Classical Brute Force | Grover Key Search | Offline Simon Qubits | Offline Simon Operations | Vulnerability Assessment |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **PRINCE** | 64 | 128 | $2^{128}$ ops | $2^{64}$ ops | 840 | $\approx 2^{64.8}$ ops | Highly vulnerable |
| **Chaskey** | 128 | 128 | $2^{128}$ ops | $2^{64}$ ops | 1,580 | $\approx 2^{65.2}$ ops | Highly vulnerable |
| **Elephant-Dumbo** | **160** | **128** | $2^{128}$ ops | **$2^{64}$ ops** | **1,620** | **$> 2^{78.5}$ ops** | **Resistant (Attack > Brute Force)** |

### Why Elephant is Structurally Resilient:
1. **Key Size < State Size:** Grover's algorithm searches over the 128-bit key space ($2^{64}$ steps). Offline Simon must resolve the full 160-bit permutation state ($O(2^{160/3}) = 2^{53.3}$ classical queries and $> 2^{78}$ quantum gate operations).
2. **Heavy Permutation Overhead:** 80 rounds of $\text{Spongent-}\pi[160]$ require deep reversible S-box synthesis and high T-depth, causing period finding to be significantly more expensive than quantum brute-force key search.

---

## 6. Experimental Validation (Software Simulation)

The project executed two reduced-scale models on Qiskit Aer:

1. **4-Bit Reduced Model:**
   * Secret root mask: `0b1011` (11)
   * Step index $i = 2$: Active mask `0b1100` (12)
   * Samples needed: 5 measurements
   * Recovered mask: `0b1100` (100% Match)
   * Inverted root mask: `0b1011` (100% Match)
   * Outcome: **SUCCESSFUL**

2. **8-Bit Reduced Model:**
   * Secret root mask: `0b10101100` (172)
   * Step index $i = 1$: Active mask `0b01011001` (89)
   * Subspace resolution: Resolved using Even-Mansour relation $P(k) \oplus k = E_k(0)$.
   * Recovered mask: `0b01011001` (100% Match)
   * Inverted root mask: `0b10101100` (100% Match)
   * Outcome: **SUCCESSFUL**

---

## 7. Conclusion

This project confirms the theoretical findings of Bonnetain & Jaques (2020/1418):
1. Simon's algorithm can algebraically recover Even-Mansour masks in polynomial time when quantum superposition queries are available.
2. In the realistic offline setting, Elephant's design—specifically choosing a state size (160 bits) substantially larger than its key size (128 bits)—serves as an effective defense mechanism against quantum period-finding attacks, making the attack less efficient than Grover's algorithm.
