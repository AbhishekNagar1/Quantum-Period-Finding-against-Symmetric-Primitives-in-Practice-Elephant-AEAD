# Quantum Period Finding against Symmetric Primitives in Practice: The Complete A to Z Guide
### Target Primitive: Elephant Authenticated Encryption Scheme (Dumbo Variant)
**Academic Reference:** Xavier Bonnetain and Samuel Jaques, *"Quantum Period Finding against Symmetric Primitives in Practice"*, IACR Cryptology ePrint Archive Report 2020/1418 (TCHES 2022).

---

## 1. Introduction for Complete Beginners (Zero Quantum Knowledge Required)

If you have never studied quantum mechanics or quantum computing before, do not worry. This section introduces every foundational concept in simple, intuitive terms.

### 1.1 Classical Bits vs. Quantum Qubits
* In traditional computers (like laptops, phones, and servers), the fundamental unit of information is a **classical bit**. A bit is a physical switch: it can be in state `0` (low voltage) or state `1` (high voltage). It can only be one or the other at any moment.
* In a quantum computer, the fundamental unit is a **qubit** (quantum bit). A qubit is a microscopic quantum system (such as an electron's spin or a trapped ion). Unlike a classical bit, a qubit can exist in a linear combination of both states simultaneously. This phenomenon is called **superposition**:
  $$|\psi\rangle = \alpha |0\rangle + \beta |1\rangle$$
  where $\alpha$ and $\beta$ are complex numbers called probability amplitudes, satisfying $|\alpha|^2 + |\beta|^2 = 1$.
  - $|\alpha|^2$ is the probability that measuring the qubit yields `0`.
  - $|\beta|^2$ is the probability that measuring the qubit yields `1`.

### 1.2 Quantum Measurement & State Collapse
A qubit can stay in a superposition of `0` and `1` while it is isolated. However, the moment a measurement is performed to read the qubit, the superposition **collapses** instantaneously into a definite classical value: either `0` or `1`.

### 1.3 Quantum Parallelism
If you have $n$ classical bits, they can store exactly one of $2^n$ possible combinations at a time (for example, 3 bits can be `000`, `001`, ..., or `111`).
If you have $n$ qubits in superposition, they represent all $2^n$ combinations **at the exact same time**:
$$|\psi\rangle = \frac{1}{\sqrt{2^n}} \sum_{x \in \{0, 1\}^n} |x\rangle$$
Evaluating a mathematical function $f$ on this superposition evaluates $f(x)$ for all $2^n$ inputs simultaneously in a single computational step.

### 1.4 Core Quantum Gates Used in this Project
Quantum gates are operations that rotate or transform qubit states:
1. **Hadamard Gate ($H$):** Creates superposition.
   - $H |0\rangle = \frac{|0\rangle + |1\rangle}{\sqrt{2}}$
   - $H |1\rangle = \frac{|0\rangle - |1\rangle}{\sqrt{2}}$
   Applying $H$ to $n$ qubits ($H^{\otimes n}$) initializes an equal superposition of all $2^n$ states.
2. **Pauli-X Gate ($X$):** The quantum equivalent of the classical NOT gate: flips $|0\rangle \leftrightarrow |1\rangle$.
3. **Controlled-NOT Gate ($CNOT$ / $CX$):** Operates on two qubits (Control and Target). If the control qubit is $|1\rangle$, it flips the target qubit. This gate performs XOR addition: $|x\rangle |y\rangle \to |x\rangle |y \oplus x\rangle$.
4. **Multi-Controlled NOT ($MCX$):** Flips the target qubit only if all $n$ control qubits are $|1\rangle$. Used to compile classical truth tables into quantum circuits.

---

## 2. Symmetric Cryptography & Authenticated Encryption (AEAD)

### 2.1 The Two Pillars: Confidentiality & Authenticity
In modern cybersecurity, sending a message securely requires two guarantees:
1. **Confidentiality (Encryption):** An eavesdropper reading the transmission cannot understand the plaintext message.
2. **Integrity & Authenticity (Authentication Tag):** An attacker cannot tamper with the message, replace the data, or spoof the sender. If even 1 bit is changed, the receiver detects it immediately and rejects the message.

A system that provides both simultaneously is called an **Authenticated Encryption with Associated Data (AEAD)** scheme. The "Associated Data" (AD) refers to headers (like packet IDs or IP addresses) that are transmitted in plaintext but must be authenticated to prevent tampering.

### 2.2 The Even-Mansour Block Cipher Construction
Proposed in 1991 by Shimon Even and Yishay Mansour, this is the simplest and most elegant symmetric cipher construction. Given an unkeyed, publicly known cryptographic permutation $P$ and a secret key $k$:
$$E_k(x) = P(x \oplus k) \oplus k$$
1. XOR input $x$ with secret key $k$ (pre-whitening).
2. Pass through the public permutation $P$.
3. XOR output with secret key $k$ (post-whitening).

Even-Mansour is classically proven secure up to $2^{n/2}$ queries (the Birthday paradox).

---

## 3. The Elephant AEAD Algorithm (Dumbo Variant)

Elephant is a family of lightweight AEAD schemes selected as a **Finalist in the NIST Lightweight Cryptography standardization project**. Designed for resource-constrained IoT devices, RFID tags, and sensors, Elephant uses an **inverse-free, permutation-based Encrypt-then-MAC** architecture.

### 3.1 Dumbo Parameters
* **Underlying Permutation:** $\text{Spongent-}\pi[160]$ (160 bits / 20 bytes, 80 rounds).
* **Master Key ($K$):** 128 bits (16 bytes).
* **Public Nonce ($N$):** 96 bits (12 bytes).
* **Authentication Tag ($T$):** 64 bits (8 bytes).
* **Security Target:** 112 bits classical security.

### 3.2 Spongent-pi[160] Permutation
Each of the 80 rounds applies three operations:
1. **Round Counter Addition (`lCounter`):** A 7-bit Linear Feedback Shift Register (LFSR) with polynomial $x^7 + x^6 + 1$ initialized to `0x75`. Its value is XORed into byte 0, and its bit-reversal (`retnuoCl`) is XORed into byte 19.
2. **Substitution Layer (`sBoxLayer`):** 40 parallel 4-bit S-boxes:
   $$S = [0xE, 0x4, 0xB, 0x1, 0x7, 0x9, 0xF, 0x3, 0x0, 0xC, 0x5, 0x2, 0xA, 0xD, 0x8, 0x6]$$
3. **Bit Permutation Layer (`pLayer`):** Shuffles bits across the 160-bit state:
   $$P(j) = (40 \cdot j) \pmod{159} \quad \text{for } 0 \le j \le 158, \quad P(159) = 159$$

### 3.3 LFSR Mask Progression ($\varphi$) & Closed-Form Inversion ($\varphi^{-1}$)
The root mask $M_0$ is derived from key $K$:
$$M_0 = P(K \parallel 0^{32}) \oplus (K \parallel 0^{32})$$
Subsequent block masks advance via the 20-byte LFSR $\varphi$:
$$\text{feedback} = \text{rotl}_3(\text{input}[0]) \oplus (\text{input}[3] \ll 7) \oplus (\text{input}[13] \gg 7)$$
$$\text{output} = \text{input}[1..19] \parallel \text{feedback}$$

Because $\varphi$ is an $\mathbb{F}_2$-linear bijection, it can be inverted in closed form:
$$\text{input}[0] = \text{rotr}_3(\text{output}[19] \oplus (\text{output}[2] \ll 7) \oplus (\text{output}[12] \gg 7))$$

### 3.4 Encryption & Authentication
* **Counter Encryption:** Padded nonce $N' = N \parallel 0^{64}$. For block $i$, keystream is:
  $$Z_i = P(N' \oplus \text{mask}_i) \oplus \text{mask}_i \oplus N'$$
  $$C_i = M_i \oplus Z_i$$
* **Tag Generation:** Accumulates nonce, associated data, and ciphertext blocks through masked permutation calls:
  $$T = \text{trunc}_{64} \left( P(N' \oplus M_0) \oplus M_0 \oplus \sum P(A_j \oplus \text{mask}_{A,j}) \oplus \text{mask}_{A,j} \oplus \sum P(C_i \oplus \text{mask}_{C,i}) \oplus \text{mask}_{C,i} \right)$$

---

## 4. Simon's Algorithm: Quantum Period Finding

Introduced by Daniel Simon in 1994, this algorithm was the inspiration for Peter Shor's algorithm for breaking RSA.

### 4.1 Simon's Problem
Given a black-box function $f: \{0, 1\}^n \to \{0, 1\}^n$ guaranteed to satisfy:
$$f(x) = f(y) \iff x \oplus y \in \{0^n, s\}$$
where $s \in \{0, 1\}^n$ is a secret non-zero XOR-period.

* **Classically:** Finding $s$ requires testing approximately $\sqrt{2^n} = 2^{n/2}$ random inputs (Birthday paradox). For $n = 128$, $2^{64}$ evaluations are needed (computationally impossible in real time).
* **Quantumly:** Simon's algorithm finds $s$ using only $O(n)$ quantum evaluations—an **exponential speedup**!

### 4.2 How the Quantum Circuit Solves It
1. Prepare two registers of $n$ qubits initialized to $|0\rangle^{\otimes n} |0\rangle^{\otimes n}$.
2. Apply Hadamard gates to the query register:
   $$\frac{1}{\sqrt{2^n}} \sum_{x \in \{0, 1\}^n} |x\rangle |0\rangle^{\otimes n}$$
3. Query the oracle $U_f$:
   $$\frac{1}{\sqrt{2^n}} \sum_{x \in \{0, 1\}^n} |x\rangle |f(x)\rangle$$
4. Apply Hadamard gates again to the query register:
   $$\frac{1}{2^n} \sum_{x} \sum_{y} (-1)^{x \cdot y} |y\rangle |f(x)\rangle$$
5. Measure the query register.
   Due to quantum interference, any state $|y\rangle$ where $y \cdot s \equiv 1 \pmod 2$ cancels out destructively (probability $= 0$).
   Only states satisfying:
   $$y \cdot s = \sum_{j=0}^{n-1} y_j s_j \equiv 0 \pmod 2$$
   survive constructive interference!

### 4.3 Classical Post-Processing (Gaussian Elimination over GF(2))
Each measurement yields an equation:
$$y_0 s_0 \oplus y_1 s_1 \oplus \dots \oplus y_{n-1} s_{n-1} = 0$$
By repeating the circuit $O(n)$ times, we collect a system of linear equations:
$$M \cdot s = 0 \pmod 2$$
Using Gaussian elimination over $\text{GF}(2)$, when $\text{rank}(M) \ge n - 1$, the nullspace reveals the unique secret period $s$.

---

## 5. The Attack: Targeting Elephant with Simon's Algorithm

### 5.1 Isolating the Periodic Function
From Elephant's encryption equation:
$$C_i \oplus M_i \oplus N' = P(N' \oplus \text{mask}_i) \oplus \text{mask}_i$$
Let $x = N'$ and $k = \text{mask}_i$. This is an Even-Mansour cipher:
$$E_k(x) = P(x \oplus k) \oplus k$$

We construct the Kuwakado-Morii periodic function:
$$f(x) = E_k(x) \oplus P(x) = P(x \oplus k) \oplus k \oplus P(x)$$

Evaluate $f(x \oplus k)$:
$$f(x \oplus k) = P((x \oplus k) \oplus k) \oplus k \oplus P(x \oplus k) = P(x) \oplus k \oplus P(x \oplus k) = f(x)$$
Thus, $f(x)$ is **strictly periodic** with hidden period $s = k = \text{mask}_i$!

### 5.2 From Recovered Period to Master Key
1. **Active Mask Recovery:** Simon's algorithm outputs $s = \text{mask}_i$.
2. **Root Mask Recovery:** Invert the LFSR $i$ times using the exact formula:
   $$M_0 = \varphi^{-i}(\text{mask}_i)$$
   *Impact:* Knowing $M_0$ allows computing all past and future masks $\text{mask}_j = \varphi^j(M_0)$. This **completely breaks Elephant's confidentiality and authenticity**—the attacker can decrypt any ciphertext and forge arbitrary authentication tags without knowing the master key!
3. **Master Key Recovery:** To recover master key $K \in \{0, 1\}^{128}$, the attacker inverts the one-way function $M_0 = P(K \parallel 0^{32}) \oplus (K \parallel 0^{32})$ via Grover's search.

---

## 6. The Central Research Finding: Why Elephant is Resistant

In their landmark paper (*ePrint 2020/1418*), Xavier Bonnetain and Samuel Jaques evaluated offline quantum period-finding attacks against symmetric primitives:

```
+--------------------------------------------------------------------------------------------------+
|                            CRYPTANALYTIC COMPLEXITY COMPARISON                                   |
+-------------------+------------+-----------+----------------------+------------------------------+
| Primitive         | State (n)  | Key (k)   | Grover Key Search    | Offline Simon Attack         |
+-------------------+------------+-----------+----------------------+------------------------------+
| PRINCE            | 64 bits    | 128 bits  | 2^64 operations      | ~ 2^64.8 operations (Faster) |
| Chaskey           | 128 bits   | 128 bits  | 2^64 operations      | ~ 2^65.2 operations (Faster) |
| Elephant-Dumbo    | 160 bits   | 128 bits  | 2^64 operations      | > 2^78.5 operations (SLOWER) |
+-------------------+------------+-----------+----------------------+------------------------------+
```

### Why Elephant Resists Simon's Algorithm
1. **State-to-Key Asymmetry:**
   - In PRINCE ($n=64, k=128$) and Chaskey ($n=128, k=128$), the state size is less than or equal to the key size. Offline Simon achieves $O(2^{n/3})$ query complexity, beating classical collision bounds and Grover search.
   - In Elephant-Dumbo ($n=160, k=128$), the state size ($160$ bits) is **substantially larger** than the master key ($128$ bits).
   - Grover brute-force key search operates on the 128-bit key: takes $\approx 2^{64}$ steps.
   - Offline Simon must resolve the entire 160-bit permutation space: classical query complexity is $2^{160/3} \approx 2^{53.3}$, and offline quantum operations exceed $2^{78}$.
2. **Permutation Synthesis Overhead:**
   Synthesizing reversible quantum circuits for 80 rounds of Spongent-$\pi[160]$ requires $> 1{,}600$ logical qubits and massive T-gate depth.
3. **Core Conclusion:** Elephant's state-to-key proportion is an effective architectural defense: **period-finding shortcuts are more expensive than brute-force key search.**

---

## 7. Project Architecture & Codebase Map

```
Quantum_Period_Finding/
├── elephant/
│   ├── spongent.py            # Spongent-pi[160] (80 rounds, S-box, pLayer, lCounter)
│   ├── lfsr.py                # LFSR forward step phi and exact inverse phi^-1
│   ├── dumbo.py               # Elephant-Dumbo AEAD (Encrypt, Decrypt, Tag verify)
│   └── test_vectors.py        # NIST Known Answer Tests (KAT)
├── quantum/
│   ├── gf2_solver.py          # GF(2) Gaussian elimination & nullspace basis solver
│   ├── oracle.py              # Canonical & custom reversible quantum oracles
│   └── simon.py               # Simon's algorithm quantum circuit & Aer executor
├── attack/
│   ├── reduced_elephant.py    # Reduced-scale Even-Mansour models (4-bit & 8-bit)
│   ├── attack_oracle.py       # Quantum oracle for f(x) = E_k(x) ^ P(x)
│   └── recovery_pipeline.py   # Full attack pipeline: Circuit -> Aer -> GF(2) -> Inversion
├── experiments/
│   ├── cost_analysis.py       # Bonnetain-Jaques theoretical formulas & table generator
│   └── run_experiment.py      # Master benchmark runner (Tiers 1, 2, and 3)
├── results/
│   ├── circuits/simon_circuit.txt      # Text quantum circuit diagram
│   ├── histograms/measurement_distribution.png  # Quantum measurement histogram
│   ├── plots/cost_comparison.png       # Complexity comparison bar chart
│   ├── attack_benchmark_summary.csv    # Empirical attack metrics
│   └── complexity_comparison.csv       # Theoretical complexity data
└── tests/
    ├── test_elephant.py       # 7 passing unit tests
    ├── test_gf2.py            # 4 passing unit tests
    ├── test_simon.py          # 11 passing unit tests
    └── test_attack.py         # 8 passing unit tests (Total: 30 tests)
```

---

## 8. Inputs, Outputs, and Data Flow

### 8.1 Module Inputs
1. **Elephant-Dumbo (`elephant/dumbo.py`):**
   - `key`: 16 bytes (128 bits) hexadecimal string or bytes.
   - `nonce`: 12 bytes (96 bits) hexadecimal string or bytes.
   - `plaintext`: Arbitrary byte string (e.g. `b"Hello Quantum"`).
   - `associated_data`: Arbitrary byte string (optional header).
2. **Reduced Quantum Attack (`attack/recovery_pipeline.py`):**
   - `model`: `ReducedElephant4Bit(secret_mask=...)` or `ReducedElephant8Bit(secret_mask=...)`.
   - `step_index`: LFSR step $i$ (e.g. $i=1$ or $i=2$).
   - `shots`: Number of quantum circuit evaluations in Qiskit Aer (e.g. `2048` or `4096`).

### 8.2 Module Outputs
1. **Ciphertext & Tag:** `ciphertext_and_tag` where the last 8 bytes are the 64-bit MAC tag.
2. **Quantum Measurement Distribution:** Frequencies of bitstrings $y$ measured in Aer.
3. **Recovered Period ($s$):** The active block mask extracted via $\text{GF}(2)$ Gaussian elimination.
4. **Inverted Root Mask ($M_0$):** The original initial mask recovered via $\varphi^{-i}(s)$.
5. **Saved Artifacts:**
   - `results/circuits/simon_circuit.txt`: Text diagram of the quantum circuit.
   - `results/histograms/measurement_distribution.png`: Bar plot showing constructive interference.
   - `results/plots/cost_comparison.png`: Comparison plot of Classical vs. Grover vs. Simon.
   - `results/attack_benchmark_summary.csv`: Empirical execution metrics.
   - `results/complexity_comparison.csv`: Numerical complexity data.

---

## 9. Step-by-Step Practical Guide: Running in VS Code

### Step 1: Open the Project in VS Code
1. Launch **Visual Studio Code**.
2. Go to **File $\to$ Open Folder...**
3. Select the folder:  
   `/Users/abhishek/Downloads/M.Tech/QC Project`
4. Click **Open**.

### Step 2: Open the Integrated Terminal
* In VS Code, press **Ctrl + `** (or **Cmd + `** on macOS), or go to **Terminal $\to$ New Terminal**.

### Step 3: Activate the Virtual Environment
In the terminal, run:
```bash
source venv/bin/activate
```
*(On Windows Command Prompt: `venv\Scripts\activate.bat`)*

### Step 4: Run the Complete Demonstration
Execute the master runner:
```bash
PYTHONPATH=. ./venv/bin/python experiments/run_experiment.py
```
**What you will see:**
1. **Tier 1:** Plaintext encryption, tag generation, decryption verification, and NIST Known Answer Test validation.
2. **Tier 2:** 4-bit and 8-bit quantum period-finding attacks running on Qiskit Aer, outputting circuit depth, measurement samples, recovered masks, and LFSR inverted root masks.
3. **Tier 3:** The Bonnetain & Jaques complexity table and generated plot paths.

### Step 5: Run the Automated Pytest Suite
Run all 30 tests:
```bash
PYTHONPATH=. ./venv/bin/pytest tests/ -v
```
All 30 tests will execute in $\approx 0.6$ seconds with `PASSED [100%]`.

### Step 6: How to Test Custom Inputs
Open Python in interactive mode or create a test script:
```python
from elephant.dumbo import ElephantDumbo

# Set custom key and nonce
key = bytes.fromhex("00112233445566778899AABBCCDDEEFF")
nonce = bytes.fromhex("0102030405060708090A0B0C")

cipher = ElephantDumbo(key)
ct_tag = cipher.encrypt(nonce, b"My custom secret payload")
print("Ciphertext + Tag:", ct_tag.hex())

recovered_pt = cipher.decrypt(nonce, ct_tag)
print("Decrypted:", recovered_pt.decode())
```

---

## 10. Summary Checklist for Viva & Presentation

1. **Primitive:** Elephant-Dumbo (Spongent-$\pi[160]$, 128-bit key, 96-bit nonce, 64-bit tag).
2. **Algorithm:** Simon's algorithm (solves $f(x \oplus s) = f(x)$ with exponential speedup).
3. **Reduction:** Even-Mansour keystream $Z(N') = P(N' \oplus \text{mask}) \oplus \text{mask}$ converted to $f(x) = E(x) \oplus P(x)$.
4. **Target:** Simon's algorithm extracts the active mask $s = \text{mask}_i$; the LFSR inverse $\varphi^{-i}$ extracts root mask $M_0$.
5. **Key Paper Discovery:** Bonnetain & Jaques (2020) proved that Elephant's 160-bit state makes Simon's attack **more expensive** than Grover's 128-bit key search ($2^{78}$ operations vs. $2^{64}$ operations).
